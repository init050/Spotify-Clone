from django.contrib import admin

from .models import (
    Album,
    AlbumArtist,
    Artist,
    ArtistFollower,
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
    list_display = ('name', 'slug', 'country', 'is_verified', 'followers_count')
    list_filter = ('is_verified', 'country')
    search_fields = ('name', 'bio')
    prepopulated_fields = {'slug': ('name',)}


class TrackInline(admin.TabularInline):
    model = Track
    extra = 1
    # To prevent editing all fields of a track inside an album
    fields = ('track_number', 'title', 'duration_ms', 'is_explicit')
    readonly_fields = ('title', 'duration_ms')


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'primary_artist', 'album_type', 'release_date')
    list_filter = ('album_type', 'release_date')
    search_fields = ('title', 'primary_artist__name')
    prepopulated_fields = {'slug': ('title',)}
    # inlines = [TrackInline] # Disabling for now to avoid complexity in admin


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ('title', 'track_number', 'album', 'primary_artist', 'duration_ms', 'popularity')
    list_filter = ('is_explicit', 'genres')
    search_fields = ('title', 'album__title', 'primary_artist__name')
    prepopulated_fields = {'slug': ('title',)}
    autocomplete_fields = ['album', 'primary_artist', 'artists', 'genres']


@admin.register(ArtistFollower)
class ArtistFollowerAdmin(admin.ModelAdmin):
    list_display = ('user', 'artist', 'created_at')
    search_fields = ('user__username', 'artist__name')
    autocomplete_fields = ['user', 'artist']


# Registering through models for visibility
@admin.register(AlbumArtist)
class AlbumArtistAdmin(admin.ModelAdmin):
    list_display = ('album', 'artist', 'role')
    autocomplete_fields = ['album', 'artist']


@admin.register(TrackArtist)
class TrackArtistAdmin(admin.ModelAdmin):
    list_display = ('track', 'artist', 'role')
    autocomplete_fields = ['track', 'artist']
