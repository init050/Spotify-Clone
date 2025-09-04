from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from artists.models import Artist, Album, Track
from playlists.models import Playlist
from .models import Recommendation, TrendingContent, SearchHistory
from django.utils import timezone

User = get_user_model()

from .tasks import compute_trending_window, compute_recommendations_batch

class SearchTaskTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='password')
        self.artist = Artist.objects.create(name='Test Artist')
        self.album = Album.objects.create(title='Test Album', primary_artist=self.artist, release_date=timezone.now())
        self.track = Track.objects.create(title='Test Track', album=self.album, primary_artist=self.artist, duration_ms=180000, track_number=1)
        self.playlist = Playlist.objects.create(title='Test Playlist', owner=self.user)

    def test_compute_trending_window(self):
        compute_trending_window()
        self.assertGreater(TrendingContent.objects.count(), 0)

    def test_compute_recommendations_batch(self):
        from social.models import SocialInteraction
        # Create another track by the same artist
        Track.objects.create(title='Another Track', slug='another-track', album=self.album, primary_artist=self.artist, duration_ms=180000, track_number=2)
        SocialInteraction.objects.create(user=self.user, object_id=self.track.id, object_type='track', interaction_type='like')
        compute_recommendations_batch()
        self.assertGreater(Recommendation.objects.filter(user=self.user).count(), 0)

class SearchAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='password')
        self.staff_user = User.objects.create_user(email='staff@example.com', password='password', is_staff=True)

        self.artist = Artist.objects.create(name='Test Artist')
        self.album = Album.objects.create(title='Test Album', primary_artist=self.artist, release_date=timezone.now())
        self.track = Track.objects.create(title='Test Track', album=self.album, primary_artist=self.artist, duration_ms=180000, track_number=1)
        self.playlist = Playlist.objects.create(title='Test Playlist', owner=self.user)

        self.trending = TrendingContent.objects.create(content_type='track', content_id=self.track.id, score=1.0, window_start=timezone.now(), window_end=timezone.now())
        self.recommendation = Recommendation.objects.create(user=self.user, item_type='track', item_id=self.track.id, score=0.9, model_version='test_v1')
        self.history = SearchHistory.objects.create(user=self.user, query='test', results_count=1)

    def test_suggest_view(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('suggest')
        response = self.client.get(url, {'q': 'Test'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    def test_search_view(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('search')
        response = self.client.get(url, {'q': 'Test'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('facets', response.data)
        self.assertGreater(len(response.data['results']), 0)
        self.assertIn('headline', response.data['results'][0])

    def test_trending_view(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('trending')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_recommendation_view(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('recommendations-me')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_search_history_view(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('search-history')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_search_analytics_view_staff(self):
        self.client.force_authenticate(user=self.staff_user)
        url = reverse('search-analytics')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_analytics_view_non_staff(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('search-analytics')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_search_feedback_view(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('search-feedback')
        data = {'query': 'test', 'clicked_item': {'type': 'track', 'id': str(self.track.id)}, 'position': 1}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
