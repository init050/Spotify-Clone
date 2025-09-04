from django.conf import settings
from django.db import models
import uuid

class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_notifications'
    )
    type = models.CharField(max_length=32)  # e.g., 'follow','like','comment','system'
    actor_id = models.UUIDField(null=True)  # who triggered it
    object_type = models.CharField(max_length=32, null=True)
    object_id = models.UUIDField(null=True)
    payload = models.JSONField(default=dict)  # small renderable payload
    is_read = models.BooleanField(default=False)
    delivered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['created_at']),
        ]

class NotificationSettings(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_settings'
    )
    email_enabled = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=True)
    inapp_enabled = models.BooleanField(default=True)
    daily_digest = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class PushNotificationDevice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='push_devices'
    )
    provider = models.CharField(max_length=16)  # 'fcm'|'apns'
    token = models.CharField(max_length=512, db_index=True)
    platform = models.CharField(max_length=16, null=True)  # 'ios','android','web'
    is_active = models.BooleanField(default=True)
    last_seen = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
