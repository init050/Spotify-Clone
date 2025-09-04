import uuid
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from ..models import Notification

User = get_user_model()

class NotificationAPITest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='password')
        self.client.force_authenticate(user=self.user)

    def test_list_notifications(self):
        Notification.objects.create(user=self.user, type='test')
        Notification.objects.create(user=self.user, type='test', is_read=True)

        url = reverse('notification-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_list_unread_notifications(self):
        Notification.objects.create(user=self.user, type='test')
        Notification.objects.create(user=self.user, type='test', is_read=True)

        url = reverse('notification-list') + '?unread=true'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_mark_read(self):
        n1 = Notification.objects.create(user=self.user, type='test')
        n2 = Notification.objects.create(user=self.user, type='test')

        url = reverse('notification-mark-read')
        response = self.client.post(url, {'ids': [str(n1.id), str(n2.id)]})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['marked'], 2)

        n1.refresh_from_db()
        n2.refresh_from_db()
        self.assertTrue(n1.is_read)
        self.assertTrue(n2.is_read)

class PushNotificationDeviceAPITest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='password')
        self.client.force_authenticate(user=self.user)

    def test_register_device(self):
        url = reverse('notification-device-register')
        data = {
            'provider': 'fcm',
            'token': str(uuid.uuid4()),
            'platform': 'android'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.user.push_devices.count(), 1)
