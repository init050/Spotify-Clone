from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .factories import GenreFactory, UserFactory


class GenreAPITest(APITestCase):
    def setUp(self):
        self.staff_user = UserFactory(is_staff=True)
        self.regular_user = UserFactory()
        self.genre = GenreFactory(name='Electronic')

    def test_list_genres_unauthenticated(self):
        url = reverse('genre-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_genre_by_staff(self):
        self.client.force_authenticate(user=self.staff_user)
        url = reverse('genre-list')
        data = {'name': 'Techno', 'slug': 'techno'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Techno')

    def test_create_genre_by_regular_user_fails(self):
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('genre-list')
        data = {'name': 'House', 'slug': 'house'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_genre_by_staff(self):
        self.client.force_authenticate(user=self.staff_user)
        url = reverse('genre-detail', kwargs={'slug': self.genre.slug})
        data = {'name': 'Electronic Dance Music'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Electronic Dance Music')

    def test_delete_genre_by_staff(self):
        self.client.force_authenticate(user=self.staff_user)
        url = reverse('genre-detail', kwargs={'slug': self.genre.slug})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_genre_by_regular_user_fails(self):
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('genre-detail', kwargs={'slug': self.genre.slug})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
