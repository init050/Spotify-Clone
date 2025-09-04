from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from ..models import Notification, PushNotificationDevice, NotificationSettings
from ..tasks import deliver_notification, PermanentError

User = get_user_model()

class DeliverNotificationTaskTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='password')
        NotificationSettings.objects.create(user=self.user)
        self.notification = Notification.objects.create(user=self.user, type='test')
        self.device = PushNotificationDevice.objects.create(
            user=self.user,
            provider='fcm',
            token='test-token'
        )

    @patch('notifications.tasks.provider_client')
    def test_deliver_notification_success(self, mock_provider_client):
        mock_provider_client.send.return_value = True

        deliver_notification(self.notification.id)

        self.notification.refresh_from_db()
        self.assertTrue(self.notification.delivered)
        mock_provider_client.send.assert_called_once()

    @patch('notifications.tasks.provider_client')
    def test_deliver_notification_permanent_failure(self, mock_provider_client):
        mock_provider_client.send.side_effect = PermanentError("Invalid token")

        deliver_notification(self.notification.id)

        self.device.refresh_from_db()
        self.assertFalse(self.device.is_active)

        self.notification.refresh_from_db()
        self.assertFalse(self.notification.delivered) # Because the only device failed

    @patch('notifications.tasks.deliver_notification.retry')
    @patch('notifications.tasks.provider_client')
    def test_deliver_notification_transient_failure(self, mock_provider_client, mock_retry):
        mock_provider_client.send.side_effect = Exception("Service unavailable")
        mock_retry.side_effect = Exception("Retry called") # To stop the test from actually retrying

        with self.assertRaises(Exception, msg="Retry called"):
            deliver_notification(self.notification.id)

        self.notification.refresh_from_db()
        self.assertFalse(self.notification.delivered)
        self.assertTrue(mock_retry.called)

    def test_deliver_notification_user_disabled_pushes(self):
        self.user.notification_settings.push_enabled = False
        self.user.notification_settings.save()

        deliver_notification(self.notification.id)

        self.notification.refresh_from_db()
        self.assertFalse(self.notification.delivered)
