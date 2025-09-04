from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .factories import ArtistFactory, UserFactory


class ArtistAPITest(APITestCase):
    def setUp(self):
        self.staff_user = UserFactory(is_staff=True)
        self.manager_user = UserFactory()
        self.regular_user = UserFactory()

        self.managed_artist = ArtistFactory()
        self.managed_artist.managers.add(self.manager_user)

        self.other_artist = ArtistFactory()

    def test_list_artists(self):
        url = reverse('artist-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_manager_can_update_their_artist(self):
        self.client.force_authenticate(user=self.manager_user)
        url = reverse('artist-detail', kwargs={'slug': self.managed_artist.slug})
        data = {'bio': 'An updated bio.'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.managed_artist.refresh_from_db()
        self.assertEqual(self.managed_artist.bio, 'An updated bio.')

    def test_manager_cannot_update_other_artist(self):
        self.client.force_authenticate(user=self.manager_user)
        url = reverse('artist-detail', kwargs={'slug': self.other_artist.slug})
        data = {'bio': 'Trying to update bio.'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_cannot_update_artist(self):
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('artist-detail', kwargs={'slug': self.managed_artist.slug})
        data = {'bio': 'Trying to update bio.'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_update_any_artist(self):
        self.client.force_authenticate(user=self.staff_user)
        url = reverse('artist-detail', kwargs={'slug': self.other_artist.slug})
        data = {'bio': 'A bio updated by staff.'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.other_artist.refresh_from_db()
        self.assertEqual(self.other_artist.bio, 'A bio updated by staff.')
