from django.conf import settings
from django.db import models
import uuid

class PlayHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name='play_history'
    )
    track_id = models.UUIDField(db_index=True)
    started_at = models.DateTimeField(db_index=True)
    ended_at = models.DateTimeField(null=True)
    position_ms = models.IntegerField(default=0)
    duration_ms = models.IntegerField(null=True)
    device_info = models.JSONField(default=dict, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class UserAnalytics(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='analytics'
    )
    date = models.DateField(db_index=True)
    play_seconds = models.BigIntegerField(default=0)
    plays = models.IntegerField(default=0)
    unique_tracks = models.IntegerField(default=0)

    class Meta:
        unique_together = ('user', 'date')

class ContentAnalytics(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    track_id = models.UUIDField(db_index=True)
    date = models.DateField(db_index=True)
    plays = models.BigIntegerField(default=0)
    completes = models.BigIntegerField(default=0)
    skips = models.BigIntegerField(default=0)
    avg_listen_ms = models.IntegerField(default=0)

    class Meta:
        unique_together = ('track_id', 'date')

class SystemMetrics(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128, db_index=True)  # metric name
    labels = models.JSONField(default=dict)  # e.g., {'worker':'celery1'}
    value = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
