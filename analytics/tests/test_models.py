import uuid
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from ..models import PlayHistory, UserAnalytics, ContentAnalytics, SystemMetrics

User = get_user_model()

class AnalyticsModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='password')
        self.track_id = uuid.uuid4()

    def test_create_play_history(self):
        PlayHistory.objects.create(
            user=self.user,
            track_id=self.track_id,
            started_at=timezone.now()
        )
        self.assertEqual(PlayHistory.objects.count(), 1)

    def test_create_user_analytics(self):
        UserAnalytics.objects.create(
            user=self.user,
            date=timezone.now().date(),
            plays=10,
            play_seconds=1234
        )
        self.assertEqual(UserAnalytics.objects.count(), 1)

    def test_create_content_analytics(self):
        ContentAnalytics.objects.create(
            track_id=self.track_id,
            date=timezone.now().date(),
            plays=100
        )
        self.assertEqual(ContentAnalytics.objects.count(), 1)

    def test_create_system_metrics(self):
        SystemMetrics.objects.create(
            name='cpu_usage',
            value=0.75,
            labels={'host': 'worker1'}
        )
        self.assertEqual(SystemMetrics.objects.count(), 1)
