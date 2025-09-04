from django.contrib import admin

from .models import (
    Album,
    AlbumArtist,
    Artist,
    Genre,
    Track,
    TrackArtist,
)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'country', 'is_verified', 'followers_count', 'monthly_listeners')
    list_filter = ('is_verified', 'country')
    search_fields = ('name', 'bio')
    prepopulated_fields = {'slug': ('name',)}


class TrackInline(admin.TabularInline):
    model = Track
    extra = 1
    fields = ('track_number', 'title', 'duration_ms', 'is_explicit', 'status')
    readonly_fields = ('title', 'duration_ms', 'status')
    autocomplete_fields = ['artists', 'genres']


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'primary_artist', 'album_type', 'release_date', 'total_tracks')
    list_filter = ('album_type', 'release_date', 'is_explicit')
    search_fields = ('title', 'primary_artist__name')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [TrackInline]
    autocomplete_fields = ['primary_artist', 'artists']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('primary_artist')


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ('title', 'track_number', 'album', 'primary_artist', 'duration_ms', 'popularity', 'status')
    list_filter = ('is_explicit', 'genres', 'status')
    search_fields = ('title', 'album__title', 'primary_artist__name')
    prepopulated_fields = {'slug': ('title',)}
    autocomplete_fields = ['album', 'primary_artist', 'artists', 'genres']


# Registering through models for visibility
@admin.register(AlbumArtist)
class AlbumArtistAdmin(admin.ModelAdmin):
    list_display = ('album', 'artist', 'role')
    autocomplete_fields = ['album', 'artist']


@admin.register(TrackArtist)
class TrackArtistAdmin(admin.ModelAdmin):
    list_display = ('track', 'artist', 'role')
    autocomplete_fields = ['track', 'artist']
