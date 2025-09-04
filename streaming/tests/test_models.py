from django.test import TestCase
from django.db.utils import IntegrityError

from .factories import (
    AudioFileFactory,
    AudioQualityFactory,
    PlaybackSettingsFactory,
    StreamingSessionFactory,
    UserFactory,
    TrackFactory,
)

class ModelTests(TestCase):

    def test_create_audio_file(self):
        audio_file = AudioFileFactory()
        self.assertIsNotNone(audio_file.pk)
        self.assertEqual(str(audio_file), f'Audio for {audio_file.track.title}')
        self.assertEqual(audio_file.status, 'completed') # Default from factory

    def test_audio_file_track_uniqueness(self):
        'An AudioFile must have a unique link to a Track.'
        track = TrackFactory()
        AudioFileFactory(track=track)
        with self.assertRaises(IntegrityError):
            AudioFileFactory(track=track) # Creating another AudioFile for the same track should fail

    def test_create_audio_quality(self):
        quality = AudioQualityFactory()
        self.assertIsNotNone(quality.pk)
        self.assertEqual(
            str(quality),
            f'{quality.audio_file.track.title} ({quality.resolution_label})'
        )

    def test_audio_quality_uniqueness(self):
        'An AudioQuality should be unique for a given file, bitrate, and format.'
        audio_file = AudioFileFactory()
        AudioQualityFactory(
            audio_file=audio_file,
            bitrate_kbps=128,
            format='hls'
        )
        with self.assertRaises(IntegrityError):
            AudioQualityFactory(
                audio_file=audio_file,
                bitrate_kbps=128,
                format='hls'
            )

    def test_create_streaming_session(self):
        session = StreamingSessionFactory()
        self.assertIsNotNone(session.pk)
        self.assertEqual(session.last_position_ms, 0)
        self.assertIn(str(session.user), str(session))

    def test_anonymous_session_str(self):
        session = StreamingSessionFactory(user=None)
        self.assertEqual(
            str(session),
            f'Anonymous session on {session.track.title}'
        )

    def test_create_playback_settings(self):
        settings = PlaybackSettingsFactory()
        self.assertIsNotNone(settings.pk)
        self.assertTrue(settings.autoplay_next)
        self.assertEqual(
            str(settings),
            f'Playback settings for {settings.user.username}'
        )

    def test_playback_settings_user_uniqueness(self):
        'A user can only have one PlaybackSettings object.'
        user = UserFactory()
        PlaybackSettingsFactory(user=user)
        with self.assertRaises(IntegrityError):
            PlaybackSettingsFactory(user=user)
