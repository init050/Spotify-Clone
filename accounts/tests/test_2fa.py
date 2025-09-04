import pyotp
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class TwoFactorAuthAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='test2fa@example.com', password='password123', is_active=True
        )
        self.client.force_authenticate(user=self.user)

        self.setup_url = reverse('2fa-setup')
        self.verify_url = reverse('2fa-verify')
        self.disable_url = reverse('2fa-disable')
        self.login_url = reverse('token_obtain_pair')
        self.login_verify_url = reverse('2fa-login-verify')

    def _enable_2fa(self):
        # Helper to perform setup and verify steps
        setup_response = self.client.post(self.setup_url)
        self.assertEqual(setup_response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        secret = self.user.totp_secret
        totp = pyotp.TOTP(secret)
        valid_code = totp.now()

        verify_response = self.client.post(self.verify_url, {'totp_code': valid_code})
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.two_factor_enabled)
        return verify_response.data['backup_codes']

    def test_2fa_setup(self):
        response = self.client.post(self.setup_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('provisioning_uri', response.data)
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.totp_secret)

    def test_2fa_verify_and_enable(self):
        self._enable_2fa()
        # Asserts are in the helper

    def test_2fa_login_flow(self):
        self._enable_2fa()

        # Unauthenticate for login attempt
        self.client.force_authenticate(user=None)

        # Step 1: Initial login
        login_payload = {'email': self.user.email, 'password': 'password123'}
        login_response = self.client.post(self.login_url, login_payload)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertTrue(login_response.data['2fa_required'])
        user_id_signed = login_response.data['user_id_signed']

        # Step 2: Verify with TOTP code
        totp = pyotp.TOTP(self.user.totp_secret)
        valid_code = totp.now()
        verify_payload = {'user_id_signed': user_id_signed, 'totp_code': valid_code}

        verify_response = self.client.post(self.login_verify_url, verify_payload)
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', verify_response.data)
        self.assertIn('refresh', verify_response.data)

    def test_2fa_login_with_backup_code(self):
        backup_codes = self._enable_2fa()
        backup_code_to_use = backup_codes[0]

        self.client.force_authenticate(user=None)

        # Step 1: Initial login
        login_payload = {'email': self.user.email, 'password': 'password123'}
        login_response = self.client.post(self.login_url, login_payload)
        user_id_signed = login_response.data['user_id_signed']

        # Step 2: Verify with backup code
        verify_payload = {'user_id_signed': user_id_signed, 'totp_code': backup_code_to_use}
        verify_response = self.client.post(self.login_verify_url, verify_payload)
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)

        # Check that backup code was removed
        self.user.refresh_from_db()
        from django.contrib.auth.hashers import check_password
        self.assertFalse(any(check_password(backup_code_to_use, hashed_code) for hashed_code in self.user.totp_backup_codes))

    def test_2fa_disable(self):
        self._enable_2fa()

        totp = pyotp.TOTP(self.user.totp_secret)
        valid_code = totp.now()

        disable_payload = {'password': 'password123', 'totp_code': valid_code}
        response = self.client.post(self.disable_url, disable_payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertFalse(self.user.two_factor_enabled)
