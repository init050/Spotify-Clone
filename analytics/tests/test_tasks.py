import uuid
from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from unittest.mock import patch
from ..models import PlayHistory, UserAnalytics, ContentAnalytics
from ..tasks import ingest_play_event, aggregate_daily_user_analytics, aggregate_daily_content_analytics

User = get_user_model()

class AnalyticsTaskTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='password')
        self.track_id = uuid.uuid4()
        self.event_data = {
            'user_id': str(self.user.id),
            'track_id': str(self.track_id),
            'timestamp': timezone.now(),
            'position_ms': 10000,
            'duration_ms': 200000,
            'device_info': {}
        }

    @patch('analytics.tasks.cache')
    def test_ingest_play_event(self, mock_cache):
        ingest_play_event(self.event_data)
        self.assertEqual(PlayHistory.objects.count(), 1)
        mock_cache.client.get_client.return_value.hincrby.assert_called_once()

    def test_aggregate_daily_user_analytics(self):
        # Create some play history for yesterday
        yesterday = timezone.now() - timedelta(days=1)
        PlayHistory.objects.create(user=self.user, track_id=self.track_id, started_at=yesterday, duration_ms=60000)
        PlayHistory.objects.create(user=self.user, track_id=uuid.uuid4(), started_at=yesterday, duration_ms=30000)

        aggregate_daily_user_analytics(day=yesterday.date())

        self.assertEqual(UserAnalytics.objects.count(), 1)
        ua = UserAnalytics.objects.first()
        self.assertEqual(ua.plays, 2)
        self.assertEqual(ua.play_seconds, 90)
        self.assertEqual(ua.unique_tracks, 2)

    def test_aggregate_daily_content_analytics(self):
        # Create some play history for yesterday
        yesterday = timezone.now() - timedelta(days=1)
        PlayHistory.objects.create(track_id=self.track_id, started_at=yesterday, position_ms=195000, duration_ms=200000) # complete
        PlayHistory.objects.create(track_id=self.track_id, started_at=yesterday, position_ms=5000, duration_ms=200000)   # skip

        aggregate_daily_content_analytics(day=yesterday.date())

        self.assertEqual(ContentAnalytics.objects.count(), 1)
        ca = ContentAnalytics.objects.first()
        self.assertEqual(ca.plays, 2)
        self.assertEqual(ca.completes, 1)
        self.assertEqual(ca.skips, 1)
