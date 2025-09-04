from django.contrib import admin
from .models import (
    Playlist,
    PlaylistTrack,
    PlaylistCollaborator,
    UserLibrary,
    LibraryItem,
)

class PlaylistTrackInline(admin.TabularInline):
    model = PlaylistTrack
    extra = 1
    autocomplete_fields = ['track']
    ordering = ['position']

class PlaylistCollaboratorInline(admin.TabularInline):
    model = PlaylistCollaborator
    extra = 1
    autocomplete_fields = ['user']

@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'is_public', 'is_unlisted', 'followers_count', 'plays_count', 'version')
    list_filter = ('is_public', 'is_unlisted', 'owner')
    search_fields = ('title', 'slug', 'owner__email')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [PlaylistTrackInline, PlaylistCollaboratorInline]

@admin.register(UserLibrary)
class UserLibraryAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__email',)
    autocomplete_fields = ['user']

@admin.register(LibraryItem)
class LibraryItemAdmin(admin.ModelAdmin):
    list_display = ('library', 'playlist', 'is_pinned')
    search_fields = ('library__user__email', 'playlist__title')
    autocomplete_fields = ['library', 'playlist']
