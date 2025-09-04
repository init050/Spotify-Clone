from celery import shared_task
from .models import Notification, PushNotificationDevice
from django.utils import timezone
# from .metrics import notifications_delivered_total, notifications_failed_total, notification_delivery_latency_seconds
import time

# This would be defined in a real provider client library
class PermanentError(Exception):
    pass

class ProviderClient:
    def send(self, provider, token, title, body, data):
        # This is a mock client. A real implementation would connect to FCM/APNs.
        print(f"Sending push notification to {token} via {provider}: '{title}' - '{body}'")
        # Simulate a permanent failure for a specific token for testing purposes
        if "permanent-failure" in token:
            raise PermanentError("Invalid device token")
        # Simulate a transient failure for another token
        if "transient-failure" in token:
            raise Exception("Provider service unavailable")
        return True

provider_client = ProviderClient()


@shared_task(bind=True, max_retries=5, default_retry_delay=60)
def deliver_notification(self, notification_id):
    # load notification
    try:
        n = Notification.objects.select_related('user__notification_settings').get(pk=notification_id)
    except Notification.DoesNotExist:
        return

    # respect user settings
    settings = getattr(n.user, 'notification_settings', None)
    if settings and not settings.push_enabled:
        n.delivered = False # Not delivered due to user settings
        n.save(update_fields=['delivered'])
        return

    # fetch devices and call provider (FCM/APNs) via provider client (abstracted)
    devices = PushNotificationDevice.objects.filter(user=n.user, is_active=True)
    if not devices.exists():
        return # No active devices to send to

    success_count = 0
    for d in devices:
        start_time = time.time()
        try:
            provider_client.send(
                provider=d.provider,
                token=d.token,
                title=n.payload.get('title'),
                body=n.payload.get('body'),
                data=n.payload.get('data', {})
            )
            # notifications_delivered_total.labels(provider=d.provider).inc()
            success_count += 1
        except PermanentError:
            # The token is invalid and should not be used again.
            d.is_active = False
            d.save(update_fields=['is_active'])
            # notifications_failed_total.labels(provider=d.provider, reason='permanent').inc()
        except Exception as exc:
            # Any other exception is treated as transient and will be retried.
            # notifications_failed_total.labels(provider=d.provider, reason='transient').inc()
            raise self.retry(exc=exc)
        finally:
            latency = time.time() - start_time
            # notification_delivery_latency_seconds.labels(provider=d.provider).observe(latency)

    if success_count > 0:
        n.delivered = True
        n.save(update_fields=['delivered'])
