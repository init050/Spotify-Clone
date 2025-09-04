import uuid
from unittest.mock import patch

from django.urls import reverse
from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.test import APITestCase

from .factories import ArtistFactory, TrackFactory, UserFactory


class UploadAPITest(APITestCase):
    def setUp(self):
        self.artist_manager = UserFactory()
        manager_group, _ = Group.objects.get_or_create(name='artist_manager')
        self.artist_manager.groups.add(manager_group)

        self.artist = ArtistFactory()
        self.artist.managers.add(self.artist_manager)
        self.track = TrackFactory(primary_artist=self.artist)

    @patch('boto3.client')
    def test_upload_init_success(self, mock_boto_client):
        """
        Tests that the upload init view returns a presigned URL structure.
        """
        # Configure the mock
        mock_s3 = mock_boto_client.return_value
        mock_s3.generate_presigned_post.return_value = {
            'url': 'http://s3.example.com/test-bucket',
            'fields': {'key': 'value'}
        }

        self.client.force_authenticate(user=self.artist_manager)
        url = reverse('upload-audio-init')
        data = {
            'filename': 'test.mp3',
            'file_size': 12345,
            'mime_type': 'audio/mpeg'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('url', response.data)
        self.assertIn('fields', response.data)
        self.assertIn('upload_id', response.data)
        self.assertIn('object_name', response.data)
        mock_s3.generate_presigned_post.assert_called_once()

    @patch('artists.views.process_audio_upload.delay')
    def test_upload_complete_success(self, mock_task_delay):
        """
        Tests that the upload complete view triggers the processing task.
        """
        self.client.force_authenticate(user=self.artist_manager)
        url = reverse('upload-audio-complete')
        data = {
            'upload_id': str(uuid.uuid4()),
            'object_name': 'uploads/original/some-uuid/test.mp3',
            'track_id': str(self.track.id)
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        self.track.refresh_from_db()
        self.assertEqual(self.track.audio_original.name, data['object_name'])
        self.assertEqual(self.track.status, 'processing')

        mock_task_delay.assert_called_once_with(str(self.track.id))
