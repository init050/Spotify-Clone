from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .factories import AlbumFactory, ArtistFactory, UserFactory


class AlbumAPITest(APITestCase):
    def setUp(self):
        self.staff_user = UserFactory(is_staff=True)
        self.manager_user = UserFactory()
        self.regular_user = UserFactory()

        self.managed_artist = ArtistFactory()
        self.managed_artist.managers.add(self.manager_user)

        self.album = AlbumFactory(primary_artist=self.managed_artist)

    def test_list_albums(self):
        url = reverse('album-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_manager_can_update_their_artists_album(self):
        self.client.force_authenticate(user=self.manager_user)
        url = reverse('album-detail', kwargs={'slug': self.album.slug})
        data = {'label': 'New Label'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.album.refresh_from_db()
        self.assertEqual(self.album.label, 'New Label')

    def test_manager_cannot_update_other_artists_album(self):
        other_artist = ArtistFactory()
        other_album = AlbumFactory(primary_artist=other_artist)
        self.client.force_authenticate(user=self.manager_user)
        url = reverse('album-detail', kwargs={'slug': other_album.slug})
        data = {'label': 'New Label'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_cannot_create_album(self):
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('album-list')
        data = {
            'title': 'New Album by Regular User',
            'slug': 'new-album-by-regular-user',
            'primary_artist': self.managed_artist.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
