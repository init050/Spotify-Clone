import math
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import TrendingContent, Recommendation
from artists.models import Track, Artist, Album
from playlists.models import Playlist
from django.conf import settings
from django.contrib.auth import get_user_model

@shared_task
def compute_trending_window():
    """
    Computes trending content using a time-decay scoring algorithm.
    """
    window_end = timezone.now()
    window_start = window_end - timedelta(days=7)
    lambda_decay = 0.1

    TrendingContent.objects.all().delete()

    # Define weights for different content types
    weights = {'track': 1.0, 'album': 0.8, 'artist': 0.9, 'playlist': 0.7}

    def calculate_score(item, weight):
        delta_hours = (window_end - item.created_at).total_seconds() / 3600
        return weight * math.exp(-lambda_decay * delta_hours)

    # Process tracks
    for track in Track.objects.filter(created_at__gte=window_start):
        score = calculate_score(track, weights['track'])
        TrendingContent.objects.create(content_type='track', content_id=track.id, score=score, window_start=window_start, window_end=window_end)

    # Process albums
    for album in Album.objects.filter(created_at__gte=window_start):
        score = calculate_score(album, weights['album'])
        TrendingContent.objects.create(content_type='album', content_id=album.id, score=score, window_start=window_start, window_end=window_end)

    # Process artists
    for artist in Artist.objects.filter(created_at__gte=window_start):
        score = calculate_score(artist, weights['artist'])
        TrendingContent.objects.create(content_type='artist', content_id=artist.id, score=score, window_start=window_start, window_end=window_end)

    # Process playlists
    for playlist in Playlist.objects.filter(created_at__gte=window_start):
        score = calculate_score(playlist, weights['playlist'])
        TrendingContent.objects.create(content_type='playlist', content_id=playlist.id, score=score, window_start=window_start, window_end=window_end)

from social.models import SocialInteraction

@shared_task
def compute_recommendations_batch():
    """
    Computes recommendations for all users based on liked tracks.
    """
    User = get_user_model()
    users = User.objects.all()

    for user in users:
        Recommendation.objects.filter(user=user).delete()

        # Get liked track IDs from the new SocialInteraction model
        liked_track_ids = SocialInteraction.objects.filter(
            user=user,
            interaction_type='like',
            object_type='track'
        ).values_list('object_id', flat=True)

        if not liked_track_ids:
            continue

        # Get artists of liked tracks
        liked_tracks_qs = Track.objects.filter(id__in=liked_track_ids).select_related('primary_artist')
        artist_ids = {t.primary_artist.id for t in liked_tracks_qs}

        # Find other tracks from these artists
        recommended_tracks = Track.objects.filter(primary_artist_id__in=artist_ids).exclude(
            id__in=liked_track_ids
        ).order_by('?')[:20]

        for track in recommended_tracks:
            Recommendation.objects.create(
                user=user,
                item_type='track',
                item_id=track.id,
                score=0.5, # Placeholder score
                model_version='content_based_v1'
            )
