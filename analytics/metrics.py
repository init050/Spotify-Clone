from prometheus_client import Counter, Histogram, Gauge

# A real implementation would use django-prometheus to register these metrics.
# We define them here to show what would be collected.

play_events_ingested_total = Counter(
    'play_events_ingested_total',
    'Total number of play events ingested.',
    ['event_type'] # e.g., 'start', 'progress', 'complete'
)

play_events_processing_latency_seconds = Histogram(
    'play_events_processing_latency_seconds',
    'Latency of play event processing from ingestion to storage.'
)

play_history_rows_total = Gauge(
    'play_history_rows_total',
    'Total number of rows in the PlayHistory table.'
)

analytics_aggregation_runtime_seconds = Histogram(
    'analytics_aggregation_runtime_seconds',
    'Runtime of the analytics aggregation tasks.',
    ['aggregator_type'] # e.g., 'user_analytics', 'content_analytics'
)
