from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

# Using a router for the StreamingSessionViewSet provides standard CRUD URLs.
router = DefaultRouter()
router.register(r'sessions', views.StreamingSessionViewSet, basename='session')

# The API URLs are now determined automatically by the router for sessions:
# - `sessions/` -> list (GET), create (POST)
# - `sessions/{pk}/` -> retrieve (GET), update (PUT/PATCH)
# - `sessions/{pk}/end/` -> end (POST) (custom action)

urlpatterns = [
    # Manually defined URLs for specific actions
    path('tracks/<slug:slug>/stream/', views.TrackStreamView.as_view(), name='track-stream'),
    path('tracks/<slug:slug>/upload/', views.TrackUploadView.as_view(), name='track-upload'),
    path('tracks/<slug:slug>/transcode/', views.TrackTranscodeView.as_view(), name='track-transcode'),
    path('tracks/<slug:slug>/qualities/', views.AudioQualitiesView.as_view(), name='track-qualities'),
    path('audiofiles/<uuid:id>/publish/', views.AudioFilePublishView.as_view(), name='audiofile-publish'),

    # URL for user-specific playback settings.
    # This maps to /api/v1/streaming/me/playback/
    path('me/playback/', views.PlaybackSettingsView.as_view(), name='playback-settings'),

    # Include the router-generated URLs. This will be prefixed with /api/v1/streaming/
    path('', include(router.urls)),
]

# The endpoint `GET /sessions/me/` is handled by the `StreamingSessionViewSet` list action
# at `/api/v1/streaming/sessions/`, since the queryset is automatically filtered
# to the currently authenticated user.
