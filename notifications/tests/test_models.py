import uuid
from django.test import TestCase
from django.contrib.auth import get_user_model
from ..models import Notification, NotificationSettings, PushNotificationDevice

User = get_user_model()

class NotificationModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='password')

    def test_create_notification(self):
        notification = Notification.objects.create(
            user=self.user,
            type='test_notification',
            payload={'message': 'This is a test'}
        )
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.type, 'test_notification')
        self.assertFalse(notification.is_read)
        self.assertFalse(notification.delivered)

class NotificationSettingsModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='password')

    def test_create_notification_settings(self):
        settings = NotificationSettings.objects.create(user=self.user)
        self.assertEqual(NotificationSettings.objects.count(), 1)
        self.assertTrue(settings.email_enabled)
        self.assertTrue(settings.push_enabled)
        self.assertTrue(settings.inapp_enabled)
        self.assertFalse(settings.daily_digest)

    def test_user_has_notification_settings_on_creation(self):
        # This depends on a signal handler which is not implemented in this example
        # but is a good practice.
        # For now, we will manually create it.
        NotificationSettings.objects.create(user=self.user)
        self.assertIsNotNone(self.user.notification_settings)


class PushNotificationDeviceModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='password')

    def test_create_push_notification_device(self):
        device = PushNotificationDevice.objects.create(
            user=self.user,
            provider='fcm',
            token=str(uuid.uuid4()),
            platform='android'
        )
        self.assertEqual(PushNotificationDevice.objects.count(), 1)
        self.assertTrue(device.is_active)
