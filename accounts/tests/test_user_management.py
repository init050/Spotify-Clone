from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class UserManagementAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='testprofile@example.com',
            password='password123',
            is_active=True
        )
        self.profile_url = reverse('profile')
        self.preferences_url = reverse('preferences')

        # Authenticate the client
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['display_name'], self.user.profile.display_name)

    def test_update_profile(self):
        payload = {
            'display_name': 'New Name',
            'bio': 'This is a new bio.'
        }
        response = self.client.put(self.profile_url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.display_name, 'New Name')
        self.assertEqual(self.user.profile.bio, 'This is a new bio.')

    def test_retrieve_preferences(self):
        response = self.client.get(self.preferences_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['language'], self.user.preferences.language)

    def test_update_preferences(self):
        payload = {
            'language': 'fr',
            'playback_quality': 'HIGH'
        }
        response = self.client.put(self.preferences_url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.preferences.refresh_from_db()
        self.assertEqual(self.user.preferences.language, 'fr')
        self.assertEqual(self.user.preferences.playback_quality, 'HIGH')

    def test_unauthenticated_access_profile(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.put(self.profile_url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_access_preferences(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.preferences_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.put(self.preferences_url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
