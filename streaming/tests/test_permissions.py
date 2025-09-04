from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from artists.tests.factories import UserFactory, ArtistFactory, TrackFactory

class PermissionAPITests(APITestCase):
    def setUp(self):
        self.regular_user = UserFactory()
        self.staff_user = UserFactory(is_staff=True)

        self.artist1 = ArtistFactory()
        self.artist2 = ArtistFactory()

        self.manager_user = UserFactory()
        self.artist1.managers.add(self.manager_user)

        self.track1 = TrackFactory(primary_artist=self.artist1)
        self.track2 = TrackFactory(primary_artist=self.artist2)

        self.upload_url_track1 = reverse('track-upload', kwargs={'slug': self.track1.slug})
        self.transcode_url_track1 = reverse('track-transcode', kwargs={'slug': self.track1.slug})

        self.upload_url_track2 = reverse('track-upload', kwargs={'slug': self.track2.slug})

    def test_staff_user_has_write_permission(self):
        'Staff users should have permission to upload and transcode.'
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(self.upload_url_track1, {})
        self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.post(self.transcode_url_track1, {})
        self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_has_no_write_permission(self):
        'Regular, non-manager users should be denied access.'
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.post(self.upload_url_track1, {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_artist_manager_has_permission_for_their_artist(self):
        'A manager for artist1 should have access to track1 endpoints.'
        self.client.force_authenticate(user=self.manager_user)
        response = self.client.post(self.upload_url_track1, {})
        self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_artist_manager_has_no_permission_for_other_artists(self):
        'A manager for artist1 should NOT have access to track2 endpoints.'
        self.client.force_authenticate(user=self.manager_user)
        response = self.client.post(self.upload_url_track2, {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_has_no_write_permission(self):
        'Unauthenticated users should be denied access.'
        response = self.client.post(self.upload_url_track1, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_404_if_track_not_found(self):
        'A 404 should be returned if the track slug does not exist.'
        self.client.force_authenticate(user=self.staff_user)
        invalid_url = reverse('track-upload', kwargs={'slug': 'non-existent-slug'})
        response = self.client.post(invalid_url, {})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
