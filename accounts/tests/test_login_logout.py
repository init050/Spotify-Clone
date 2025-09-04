from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from ..models import UserSession
from django.core.cache import cache

User = get_user_model()

class LoginLogoutAPITests(APITestCase):

    def setUp(self):
        cache.clear()
        self.login_url = reverse('token_obtain_pair')
        self.logout_url = reverse('logout')
        self.refresh_url = reverse('token_refresh')

        self.user = User.objects.create_user(
            email='testlogin@example.com',
            password='password123',
            is_active=True
        )
        self.valid_payload = {
            'email': 'testlogin@example.com',
            'password': 'password123'
        }

    def test_successful_login(self):
        response = self.client.post(self.login_url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

        # Check session was created
        self.assertTrue(UserSession.objects.filter(user=self.user).exists())

    def test_login_inactive_user(self):
        self.user.is_active = False
        self.user.save()
        response = self.client.post(self.login_url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_wrong_password(self):
        payload = self.valid_payload.copy()
        payload['password'] = 'wrong'
        response = self.client.post(self.login_url, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_account_lockout(self):
        payload = self.valid_payload.copy()
        payload['password'] = 'wrong'

        # Fail 5 times
        for i in range(5):
            response = self.client.post(self.login_url, payload)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, f'Failed on attempt {i+1}')

        # 6th attempt should be locked
        response = self.client.post(self.login_url, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('locked', response.data['detail'])

    def test_successful_logout(self):
        # 1. Login
        login_response = self.client.post(self.login_url, self.valid_payload)
        refresh_token = login_response.data['refresh']

        # 2. Logout
        logout_payload = {'refresh': refresh_token}
        # We need to authenticate to logout
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {login_response.data["access"]}')
        logout_response = self.client.post(self.logout_url, logout_payload)
        self.assertEqual(logout_response.status_code, status.HTTP_205_RESET_CONTENT)

        # 3. Try to use the blacklisted refresh token
        refresh_response = self.client.post(self.refresh_url, logout_payload)
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh(self):
        login_response = self.client.post(self.login_url, self.valid_payload)
        old_refresh = login_response.data['refresh']
        old_access = login_response.data['access']

        refresh_payload = {'refresh': old_refresh}
        refresh_response = self.client.post(self.refresh_url, refresh_payload)

        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        new_access = refresh_response.data['access']
        new_refresh = refresh_response.data['refresh']

        self.assertNotEqual(old_access, new_access)
        self.assertNotEqual(old_refresh, new_refresh) # Because of token rotation
