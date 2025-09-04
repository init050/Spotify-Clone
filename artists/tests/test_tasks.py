import unittest
from unittest.mock import patch
from django.test import TestCase
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile

from .factories import TrackFactory
from .test_utils import create_silent_wav
from artists.tasks import process_audio_upload
from artists.models import Track


class TaskProcessingTest(TestCase):
    def setUp(self):
        self.silent_wav_data = create_silent_wav(duration_ms=1000).read()
        self.track = TrackFactory(
            audio_original=SimpleUploadedFile(
                name='silent.wav',
                content=self.silent_wav_data,
                content_type='audio/wav'
            )
        )

    @unittest.skip('Skipping test that requires ffprobe to be installed in the environment.')
    @patch('artists.tasks.default_storage.save')
    @patch('artists.tasks.default_storage.open')
    def test_process_audio_success(self, mock_storage_open, mock_storage_save):
        """
        Tests the successful processing of a real (silent) audio file.
        """
        # Mock the file coming from storage to return our silent wav
        mock_storage_open.return_value.__enter__.return_value = ContentFile(self.silent_wav_data)
        # Mock the save to return a path, not a MagicMock
        mock_storage_save.return_value = 'mock/path/to/file'

        # Run the task
        process_audio_upload(self.track.id)

        self.track.refresh_from_db()

        self.assertEqual(self.track.status, Track.ProcessingStatus.COMPLETED)
        self.assertAlmostEqual(self.track.duration_ms, 1000, delta=20) # Allow small delta
        self.assertIsNotNone(self.track.audio_hls_master.name)
        # Check that HLS files and waveform were saved
        self.assertGreater(mock_storage_save.call_count, 0)
        self.assertEqual(self.track.waveform_json['image_path'], 'mock/path/to/file')


    @patch('artists.tasks.ffmpeg.probe', side_effect=Exception('FFMPEG probe error'))
    def test_process_audio_failure_on_probe(self, mock_ffmpeg_probe):
        """
        Tests that the track status is set to FAILED if probing fails.
        """
        with patch('artists.tasks.default_storage.open') as mock_storage_open:
            mock_storage_open.return_value.__enter__.return_value = ContentFile(self.silent_wav_data)
            try:
                process_audio_upload(self.track.id)
            except Exception:
                pass

        self.track.refresh_from_db()
        self.assertEqual(self.track.status, Track.ProcessingStatus.FAILED)

    @patch('artists.tasks.ffmpeg.merge_outputs')
    def test_process_audio_failure_on_transcode(self, mock_ffmpeg_merge):
        """
        Tests that the track status is set to FAILED if transcoding fails.
        """
        # Configure the mock to raise an error when .run() is called
        mock_ffmpeg_merge.return_value.run.side_effect = Exception('FFMPEG transcode error')

        with patch('artists.tasks.default_storage.open') as mock_storage_open:
            mock_storage_open.return_value.__enter__.return_value = ContentFile(self.silent_wav_data)
            try:
                process_audio_upload(self.track.id)
            except Exception:
                pass

        self.track.refresh_from_db()
        self.assertEqual(self.track.status, Track.ProcessingStatus.FAILED)
