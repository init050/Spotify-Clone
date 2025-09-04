from prometheus_client import Counter, Histogram

# A real implementation would use django-prometheus to register these metrics.
# We define them here to show what would be collected.

notifications_delivered_total = Counter(
    'notifications_delivered_total',
    'Total number of notifications successfully delivered.',
    ['provider']
)

notifications_failed_total = Counter(
    'notifications_failed_total',
    'Total number of notifications that failed to be delivered.',
    ['provider', 'reason'] # reason can be 'permanent' or 'transient'
)

notification_delivery_latency_seconds = Histogram(
    'notification_delivery_latency_seconds',
    'Latency of notification delivery.',
    ['provider']
)
