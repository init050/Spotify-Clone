from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .factories import TrackFactory, ArtistFactory, UserFactory


class TrackAPITest(APITestCase):
    def setUp(self):
        self.staff_user = UserFactory(is_staff=True)
        self.manager_user = UserFactory()
        self.regular_user = UserFactory()

        self.managed_artist = ArtistFactory()
        self.managed_artist.managers.add(self.manager_user)

        self.track = TrackFactory(primary_artist=self.managed_artist)

    def test_list_tracks(self):
        url = reverse('track-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_manager_can_update_their_artists_track(self):
        self.client.force_authenticate(user=self.manager_user)
        url = reverse('track-detail', kwargs={'slug': self.track.slug})
        data = {'is_explicit': True}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.track.refresh_from_db()
        self.assertTrue(self.track.is_explicit)

    def test_manager_cannot_update_other_artists_track(self):
        other_artist = ArtistFactory()
        other_track = TrackFactory(primary_artist=other_artist)
        self.client.force_authenticate(user=self.manager_user)
        url = reverse('track-detail', kwargs={'slug': other_track.slug})
        data = {'is_explicit': True}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
