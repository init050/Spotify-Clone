import uuid
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from unittest.mock import patch
from ..models import UserAnalytics, ContentAnalytics

User = get_user_model()

class AnalyticsAPITest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='password')
        self.track_id = uuid.uuid4()

    @patch('analytics.views.ingest_play_event.delay')
    def test_ingest_play_event(self, mock_task):
        url = reverse('analytics-ingest-play')
        data = {
            'user_id': str(self.user.id),
            'track_id': str(self.track_id),
            'event': 'start',
            'position_ms': 0,
            'duration_ms': 300000,
            'timestamp': timezone.now().isoformat()
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        mock_task.assert_called_once()

    def test_get_user_analytics(self):
        self.client.force_authenticate(user=self.user)
        UserAnalytics.objects.create(user=self.user, date=timezone.now().date(), plays=10)

        url = reverse('analytics-user', kwargs={'user_id': self.user.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['plays'], 10)

    def test_get_content_analytics(self):
        ContentAnalytics.objects.create(track_id=self.track_id, date=timezone.now().date(), plays=100)

        url = reverse('analytics-content', kwargs={'track_id': self.track_id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['plays'], 100)
