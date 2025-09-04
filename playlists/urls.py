from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'playlists', views.PlaylistViewSet, basename='playlist')

# Separate router for user-specific, non-nested resources
me_router = DefaultRouter()
me_router.register(r'library', views.LibraryViewSet, basename='library')
# The LikedSongs viewset handles its own routing logic for create/list/destroy
# so we will add it manually.

urlpatterns = [
    path('', include(router.urls)),

    # Reorder
    path('playlists/<slug:slug>/reorder/', views.ReorderView.as_view(), name='playlist-reorder'),

    # Collaborators
    path('playlists/<slug:playlist_slug>/collaborators/', views.CollaboratorViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='playlist-collaborators-list'),
    path('playlists/<slug:playlist_slug>/collaborators/<uuid:pk>/', views.CollaboratorViewSet.as_view({
        'get': 'retrieve',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='playlist-collaborators-detail'),

    # Library
    path('me/library/', views.LibraryViewSet.as_view({'get': 'list'}), name='user-library'),
]
