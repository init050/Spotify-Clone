from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch

User = get_user_model()

class RegistrationAPITests(APITestCase):

    def setUp(self):
        self.register_url = reverse('register')
        self.valid_payload = {
            'email': 'test@example.com',
            'password': 'password123',
            'password2': 'password123'
        }

    @patch('accounts.tasks.send_verification_email.delay')
    def test_successful_registration(self, mock_send_email):
        response = self.client.post(self.register_url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check if user was created
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.get()
        self.assertEqual(user.email, self.valid_payload['email'])
        self.assertFalse(user.is_active) # Should be inactive until verified

        # Check if email task was called
        mock_send_email.assert_called_once_with(user.pk)

    def test_registration_password_mismatch(self):
        payload = self.valid_payload.copy()
        payload['password2'] = 'wrongpassword'
        response = self.client.post(self.register_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_registration_existing_email(self):
        # Create a user first
        User.objects.create_user(email=self.valid_payload['email'], password='somepassword')

        response = self.client.post(self.register_url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    @patch('accounts.tasks.send_verification_email.delay')
    def test_email_verification(self, mock_send_email):
        # 1. Register user
        self.client.post(self.register_url, self.valid_payload)
        user = User.objects.get(email=self.valid_payload['email'])
        self.assertFalse(user.is_active)

        # 2. Simulate email verification link
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        verify_url = reverse('verify-email') + f'?uidb64={uid}&token={token}'
        response = self.client.get(verify_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 3. Check if user is now active
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_email_verified)

    def test_invalid_email_verification_token(self):
        # 1. Register user
        self.client.post(self.register_url, self.valid_payload)
        user = User.objects.get(email=self.valid_payload['email'])

        # 2. Use an invalid token
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = 'invalid-token'

        verify_url = reverse('verify-email') + f'?uidb64={uid}&token={token}'
        response = self.client.get(verify_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        user.refresh_from_db()
        self.assertFalse(user.is_active)
