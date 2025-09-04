from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomUserManagerTests(TestCase):

    def test_create_user(self):
        user = User.objects.create_user(
            email='test@example.com',
            password='password123'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.check_password('password123'))

        # Check that profile and preferences are created
        self.assertIsNotNone(user.profile)
        self.assertIsNotNone(user.preferences)

    def test_create_user_no_email(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', password='password123')

    def test_create_superuser(self):
        superuser = User.objects.create_superuser(
            email='super@example.com',
            password='password123'
        )
        self.assertEqual(superuser.email, 'super@example.com')
        self.assertTrue(superuser.is_active)
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.check_password('password123'))

    def test_create_superuser_not_staff(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email='super@example.com',
                password='password123',
                is_staff=False
            )

    def test_create_superuser_not_superuser(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email='super@example.com',
                password='password123',
                is_superuser=False
            )

    def test_normalize_email(self):
        email = 'TEST@EXAMPLE.COM'
        user = User.objects.create_user(email=email, password='password123')
        self.assertEqual(user.email, 'test@example.com')
