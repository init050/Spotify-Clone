from celery import shared_task
from .models import PlayHistory
from django.core.cache import cache
# from .metrics import play_events_ingested_total, analytics_aggregation_runtime_seconds
import time

from datetime import date, timedelta
from django.db.models import Sum, Count, Avg, F
from .models import UserAnalytics, ContentAnalytics

@shared_task
def ingest_play_event(event):
    """
    Ingests a play event. This is a simplified implementation.
    A more robust solution would handle different event types (start, progress, complete, pause)
    to build a more accurate play session history.
    """
    # play_events_ingested_total.labels(event_type=event.get('event', 'unknown')).inc()

    # SECURITY: Before saving, scrub PII from device_info if necessary.
    # For example, remove or hash the IP address.
    device_info = event.get('device_info', {})
    if 'ip' in device_info:
        # Example: replace with a generic value or hash
        device_info['ip'] = '0.0.0.0'

    PlayHistory.objects.create(
        user_id=event.get('user_id'),
        track_id=event.get('track_id'),
        started_at=event.get('timestamp'),
        position_ms=event.get('position_ms'),
        duration_ms=event.get('duration_ms'),
        device_info=event.get('device_info', {})
    )

    # Update real-time counters in Redis
    redis_client = cache.client.get_client()
    redis_client.hincrby(f'content:{event["track_id"]}:counters', 'plays', 1)

    # Here you could also add the user to a set for unique daily listeners
    # redis_client.sadd(f'content:{event["track_id"]}:daily_listeners', event.get('user_id'))


@shared_task
def aggregate_daily_user_analytics(day=None):
    """
    Aggregates user play data for a given day.
    If no day is provided, it defaults to yesterday.
    """
    start_time = time.time()
    if day is None:
        day = date.today() - timedelta(days=1)

    # Aggregate data from PlayHistory
    user_data = PlayHistory.objects.filter(started_at__date=day)\
        .values('user_id')\
        .annotate(
            total_play_seconds=Sum(F('duration_ms')) / 1000,
            total_plays=Count('id'),
            total_unique_tracks=Count('track_id', distinct=True)
        )

    # Create or update UserAnalytics records
    for data in user_data:
        UserAnalytics.objects.update_or_create(
            user_id=data['user_id'],
            date=day,
            defaults={
                'play_seconds': data['total_play_seconds'],
                'plays': data['total_plays'],
                'unique_tracks': data['total_unique_tracks']
            }
        )

    duration = time.time() - start_time
    # analytics_aggregation_runtime_seconds.labels(aggregator_type='user_analytics').observe(duration)

@shared_task
def aggregate_daily_content_analytics(day=None):
    """
    Aggregates content play data for a given day.
    If no day is provided, it defaults to yesterday.
    """
    start_time = time.time()
    if day is None:
        day = date.today() - timedelta(days=1)

    # Aggregate data from PlayHistory
    content_data = PlayHistory.objects.filter(started_at__date=day)\
        .values('track_id')\
        .annotate(
            total_plays=Count('id'),
            total_completes=Count('id', filter=F('position_ms') >= F('duration_ms') * 0.95),
            total_skips=Count('id', filter=F('position_ms') < F('duration_ms') * 0.1),
            average_listen_ms=Avg('position_ms')
        )

    # Create or update ContentAnalytics records
    for data in content_data:
        ContentAnalytics.objects.update_or_create(
            track_id=data['track_id'],
            date=day,
            defaults={
                'plays': data['total_plays'],
                'completes': data['total_completes'],
                'skips': data['total_skips'],
                'avg_listen_ms': data['average_listen_ms']
            }
        )

    duration = time.time() - start_time
    # analytics_aggregation_runtime_seconds.labels(aggregator_type='content_analytics').observe(duration)
