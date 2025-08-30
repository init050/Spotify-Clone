from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.core.files.base import ContentFile

from .factories import TrackFactory
from artists.tasks import process_audio_upload
from artists.models import Track


class TaskProcessingTest(TestCase):
    def setUp(self):
        self.track = TrackFactory(audio_original__data=b'dummy audio data')

    @patch('artists.tasks.default_storage.save')
    @patch('artists.tasks.default_storage.open')
    @patch('ffmpeg.probe')
    @patch('ffmpeg.run')
    def test_process_audio_success(self, mock_ffmpeg_run, mock_ffmpeg_probe, mock_storage_open, mock_storage_save):
        """
        Tests the successful processing of an audio file.
        """
        # Mock the file coming from storage
        mock_storage_open.return_value.__enter__.return_value = ContentFile(b'dummy data')

        # Mock ffmpeg.probe to return some metadata
        mock_ffmpeg_probe.return_value = {
            'streams': [{
                'codec_type': 'audio',
                'duration': '180.5',
                'bit_rate': '128000',
                'sample_rate': '44100'
            }]
        }

        # Run the task
        process_audio_upload(self.track.id)

        self.track.refresh_from_db()

        self.assertEqual(self.track.status, Track.ProcessingStatus.COMPLETED)
        self.assertEqual(self.track.duration_ms, 180500)
        self.assertEqual(self.track.bitrate_kbps, 128)
        self.assertIsNotNone(self.track.audio_hls_master.name)

        # Check that ffmpeg was called to transcode and generate waveform
        self.assertTrue(mock_ffmpeg_run.called)
        # Check that HLS files and waveform were saved
        # The exact number of calls depends on HLS segments
        self.assertGreater(mock_storage_save.call_count, 0)

    @patch('artists.tasks.ffmpeg.probe', side_effect=Exception('FFMPEG Error'))
    def test_process_audio_failure(self, mock_ffmpeg_probe):
        """
        Tests that the track status is set to FAILED if processing fails.
        """
        # The task is designed to catch exceptions and retry, so we call it directly
        # and expect it to eventually fail and set the status.
        # For this test, we'll just call it once and check the status.
        # A real-world test might need to handle Celery's retry logic.
        with self.assertRaises(Exception):
             process_audio_upload.delay(self.track.id) # .delay to simulate real call

        # In a test environment with CELERY_TASK_ALWAYS_EAGER=True, this will run synchronously
        # but the exception will be raised. We need to catch it and then check the state.
        try:
            process_audio_upload(self.track.id)
        except Exception:
            pass

        self.track.refresh_from_db()
        self.assertEqual(self.track.status, Track.ProcessingStatus.FAILED)
