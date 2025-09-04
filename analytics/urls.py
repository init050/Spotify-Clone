from django.urls import path
from .views import (
    IngestPlayEventView,
    UserAnalyticsView,
    ContentAnalyticsView,
)

urlpatterns = [
    path('play/', IngestPlayEventView.as_view(), name='analytics-ingest-play'),
    path('users/<uuid:user_id>/', UserAnalyticsView.as_view(), name='analytics-user'),
    path('tracks/<uuid:track_id>/', ContentAnalyticsView.as_view(), name='analytics-content'),
]
