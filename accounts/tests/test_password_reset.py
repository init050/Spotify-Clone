from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch

User = get_user_model()

class PasswordResetAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='testreset@example.com',
            password='oldpassword',
            is_active=True
        )
        self.request_url = reverse('password-reset-request')
        self.confirm_url = reverse('password-reset-confirm')

    @patch('accounts.tasks.send_password_reset_email.delay')
    def test_password_reset_request_success(self, mock_send_email):
        response = self.client.post(self.request_url, {'email': self.user.email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_send_email.assert_called_once_with(self.user.pk)

    def test_password_reset_request_nonexistent_email(self):
        response = self.client.post(self.request_url, {'email': 'nonexistent@example.com'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_confirm_success(self):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes

        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)

        payload = {
            'uidb64': uid,
            'token': token,
            'new_password': 'newpassword123',
            'new_password2': 'newpassword123'
        }

        response = self.client.post(self.confirm_url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify password has changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword123'))

        # Verify old password no longer works
        self.assertFalse(self.user.check_password('oldpassword'))

    def test_password_reset_confirm_invalid_token(self):
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes

        uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        payload = {
            'uidb64': uid,
            'token': 'invalid-token',
            'new_password': 'newpassword123',
            'new_password2': 'newpassword123'
        }

        response = self.client.post(self.confirm_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('token', response.data)
