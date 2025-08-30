from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'genres', views.GenreViewSet, basename='genre')
router.register(r'artists', views.ArtistViewSet, basename='artist')
router.register(r'albums', views.AlbumViewSet, basename='album')
router.register(r'tracks', views.TrackViewSet, basename='track')

urlpatterns = [
    path('search/', views.SearchView.as_view(), name='catalog-search'),
    path('uploads/audio/init/', views.UploadInitView.as_view(), name='upload-audio-init'),
    path('uploads/audio/complete/', views.UploadCompleteView.as_view(), name='upload-audio-complete'),
    path('streams/<slug:track_slug>/manifest/', views.StreamManifestView.as_view(), name='stream-manifest'),
    path('', include(router.urls)),
]
