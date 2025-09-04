from rest_framework import generics
from rest_framework.response import Response
from django.contrib.postgres.search import TrigramSimilarity, SearchQuery, SearchRank, SearchVector, SearchHeadline
from django.db.models.functions import Greatest
from django.db.models import F
from artists.models import Artist, Album, Track
from playlists.models import Playlist
from .serializers import SuggestionSerializer, SearchResultSerializer, TrendingContentSerializer, RecommendationSerializer, SearchHistorySerializer, SearchAnalyticsSerializer, SearchFeedbackSerializer
from django.core.cache import cache
from .models import TrendingContent, Recommendation, SearchHistory, SearchAnalytics
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from django.db import connection

class SearchView(generics.ListAPIView):
    """
    Performs a full-text search across multiple models.
    """
    serializer_class = SearchResultSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        # This is a simplified faceting implementation.
        # In a real application, this would be more dynamic.
        facets = {
            'type': {
                'artist': Artist.objects.filter(name__icontains=request.query_params.get('q', '')).count(),
                'album': Album.objects.filter(title__icontains=request.query_params.get('q', '')).count(),
                'track': Track.objects.filter(title__icontains=request.query_params.get('q', '')).count(),
                'playlist': Playlist.objects.filter(title__icontains=request.query_params.get('q', '')).count(),
            }
        }

        return Response({'results': serializer.data, 'facets': facets})

    def get_queryset(self):
        query = self.request.query_params.get('q', '')
        if not query:
            return []

        search_type = self.request.query_params.get('type')
        results = []

        if 'postgres' in connection.vendor:
            search_query = SearchQuery(query, search_type='websearch')
            headline_kwargs = {'start_sel': '<span>', 'stop_sel': '</span>'}
            if not search_type or search_type == 'artist':
                artists = Artist.objects.annotate(
                    rank=SearchRank(F('search_vector'), search_query),
                    headline=SearchHeadline('name', search_query, **headline_kwargs)
                ).filter(search_vector=search_query).order_by('-rank').prefetch_related('managers')
                results.extend([{'type': 'artist', 'instance': a, 'score': a.rank, 'headline': a.headline} for a in artists])
            if not search_type or search_type == 'album':
                albums = Album.objects.select_related('primary_artist').annotate(
                    rank=SearchRank(F('search_vector'), search_query),
                    headline=SearchHeadline('title', search_query, **headline_kwargs)
                ).filter(search_vector=search_query).order_by('-rank')
                results.extend([{'type': 'album', 'instance': a, 'score': a.rank, 'headline': a.headline} for a in albums])
            if not search_type or search_type == 'track':
                tracks = Track.objects.select_related('album', 'primary_artist').prefetch_related('artists', 'genres').annotate(
                    rank=SearchRank(F('search_vector'), search_query),
                    headline=SearchHeadline('title', search_query, **headline_kwargs)
                ).filter(search_vector=search_query).order_by('-rank')
                results.extend([{'type': 'track', 'instance': t, 'score': t.rank, 'headline': t.headline} for t in tracks])
            if not search_type or search_type == 'playlist':
                playlists = Playlist.objects.select_related('owner').annotate(
                    rank=SearchRank(F('search_vector'), search_query),
                    headline=SearchHeadline('title', search_query, **headline_kwargs)
                ).filter(search_vector=search_query).order_by('-rank')
                results.extend([{'type': 'playlist', 'instance': p, 'score': p.rank, 'headline': p.headline} for p in playlists])
        else: # Fallback for SQLite
            if not search_type or search_type == 'artist':
                artists = Artist.objects.filter(name__icontains=query)
                results.extend([{'type': 'artist', 'instance': a, 'score': 0, 'headline': a.name} for a in artists])
            if not search_type or search_type == 'album':
                albums = Album.objects.filter(title__icontains=query)
                results.extend([{'type': 'album', 'instance': a, 'score': 0, 'headline': a.title} for a in albums])
            if not search_type or search_type == 'track':
                tracks = Track.objects.filter(title__icontains=query)
                results.extend([{'type': 'track', 'instance': t, 'score': 0, 'headline': t.title} for t in tracks])
            if not search_type or search_type == 'playlist':
                playlists = Playlist.objects.filter(title__icontains=query)
                results.extend([{'type': 'playlist', 'instance': p, 'score': 0, 'headline': p.title} for p in playlists])

        results.sort(key=lambda x: x['score'], reverse=True)
        return results

class TrendingView(generics.ListAPIView):
    """
    Returns a list of trending content.
    """
    serializer_class = TrendingContentSerializer

    def list(self, request, *args, **kwargs):
        cache_key = f'trending:{request.query_params.get("type", "all")}'
        cached_results = cache.get(cache_key)
        if cached_results:
            return Response(cached_results)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=60 * 15) # Cache for 15 minutes
        return response

    def get_queryset(self):
        content_type = self.request.query_params.get('type')
        if content_type:
            return TrendingContent.objects.filter(content_type=content_type).order_by('-score')
        return TrendingContent.objects.all().order_by('-score')

class RecommendationView(generics.ListAPIView):
    """
    Returns a list of recommendations for the authenticated user.
    """
    serializer_class = RecommendationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Recommendation.objects.filter(user=self.request.user).order_by('-score')

class SearchHistoryView(generics.ListAPIView):
    """
    Returns a list of the authenticated user's search history.
    """
    serializer_class = SearchHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SearchHistory.objects.select_related('user').filter(user=self.request.user).order_by('-created_at')

class SearchAnalyticsView(generics.ListAPIView):
    """
    Returns a list of search analytics.
    """
    serializer_class = SearchAnalyticsSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return SearchAnalytics.objects.all().order_by('-last_seen_at')

class SearchFeedbackView(generics.CreateAPIView):
    """
    Accepts feedback on search results to improve relevance.
    """
    serializer_class = SearchFeedbackSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # In a real application, this would trigger a background task
        # to update analytics and potentially a machine learning model.
        # For now, we'll just save the feedback.
        serializer.save(user=self.request.user)

class SuggestView(generics.GenericAPIView):
    """
    Provides typeahead search suggestions across artists, tracks, and albums.
    """
    serializer_class = SuggestionSerializer

    def get(self, request, *args, **kwargs):
        query = request.query_params.get('q', '')
        if not query or len(query) < 2:
            return Response([])

        limit = int(request.query_params.get('limit', 10))

        cache_key = f'suggest:{query}:{limit}'
        cached_results = cache.get(cache_key)
        if cached_results:
            return Response(cached_results)

        results = []

        if 'postgres' in connection.vendor:
            # Search artists
            artists = Artist.objects.annotate(
                similarity=Greatest(
                    TrigramSimilarity('name', query),
                    TrigramSimilarity('bio', query)
                )
            ).filter(similarity__gt=0.1).order_by('-similarity')[:limit]
            results.extend([{'type': 'artist', 'text': a.name, 'score': a.similarity} for a in artists])
            # ... similar for album, track
        else: # Fallback for SQLite
            artists = Artist.objects.filter(name__icontains=query)[:limit]
            results.extend([{'type': 'artist', 'text': a.name, 'score': 0} for a in artists])
            albums = Album.objects.filter(title__icontains=query)[:limit]
            results.extend([{'type': 'album', 'text': a.title, 'score': 0} for a in albums])
            tracks = Track.objects.filter(title__icontains=query)[:limit]
            results.extend([{'type': 'track', 'text': t.title, 'score': 0} for t in tracks])

        # Sort all results by score and take the top N
        results.sort(key=lambda x: x['score'], reverse=True)
        final_results = results[:limit]

        cache.set(cache_key, final_results, timeout=60 * 5) # Cache for 5 minutes

        return Response(final_results)
