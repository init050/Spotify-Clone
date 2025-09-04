from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from artists.tests.factories import UserFactory
from artists.models import Track
from .factories import (
    AudioFileFactory,
    PlaybackSettingsFactory,
    StreamingSessionFactory,
    TrackFactory
)

class PlaybackSettingsAPITests(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
        self.url = reverse('playback-settings')

    def test_get_playback_settings(self):
        'GET request retrieves user\'s playback settings, creating them if non-existent.'
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('autoplay_next' in response.data)

    def test_update_playback_settings(self):
        'PATCH request updates user\'s playback settings.'
        PlaybackSettingsFactory(user=self.user, shuffle=False)

        response = self.client.patch(self.url, {'shuffle': True}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['shuffle'])

    def test_unauthenticated_access_denied(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class StreamingSessionAPITests(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
        self.track = TrackFactory()
        self.audio_file = AudioFileFactory(track=self.track, status=Track.ProcessingStatus.COMPLETED)

    def test_start_session(self):
        'POST to /sessions/ starts a new streaming session.'
        url = reverse('session-list') # 'session-list' is the default name from the router
        data = {'track': self.track.pk}

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['track'], self.track.title) # Using StringRelatedField
        self.assertIsNotNone(response.data['id'])

    def test_start_session_for_unprocessed_track_fails(self):
        'A session cannot be started for a track that is not yet processed.'
        unprocessed_track = TrackFactory()
        AudioFileFactory(track=unprocessed_track, status=Track.ProcessingStatus.PENDING)
        url = reverse('session-list')
        data = {'track': unprocessed_track.pk}

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_session_position(self):
        'PATCH to /sessions/{id}/ updates the last_position_ms.'
        session = StreamingSessionFactory(user=self.user)
        url = reverse('session-detail', kwargs={'pk': session.pk})
        data = {'last_position_ms': 30000}

        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['last_position_ms'], 30000)

    def test_user_cannot_update_another_users_session(self):
        'A user cannot update a session belonging to another user.'
        other_user = UserFactory()
        session = StreamingSessionFactory(user=other_user)
        url = reverse('session-detail', kwargs={'pk': session.pk})
        data = {'last_position_ms': 30000}

        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) # 404 because queryset is filtered first

    def test_end_session_and_increment_popularity(self):
        'POST to /sessions/{id}/end/ ends the session and may increment popularity.'
        session = StreamingSessionFactory(user=self.user, track=self.track, audio_file=self.audio_file)
        url = reverse('session-end', kwargs={'pk': session.pk})

        initial_popularity = self.track.popularity

        # Simulate listening for more than 30 seconds
        session.last_position_ms = 45000
        session.save()

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data['ended_at'])

        self.track.refresh_from_db()
        self.assertEqual(self.track.popularity, initial_popularity + 1)


class TrackStreamingAPITests(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
        self.track = TrackFactory()
        self.audio_file = AudioFileFactory(track=self.track)

    def test_get_stream_url(self):
        'GET /tracks/{slug}/stream/ returns a URL.'
        url = reverse('track-stream', kwargs={'slug': self.track.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('url' in response.data)
        self.assertIn('.m3u8', response.data['url']) # Check for HLS playlist

    def test_get_stream_url_for_unprocessed_file_fails(self):
        'GET /stream/ returns 404 if the audio file is not marked as COMPLETED.'
        self.audio_file.status = Track.ProcessingStatus.PENDING
        self.audio_file.save()
        url = reverse('track-stream', kwargs={'slug': self.track.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
