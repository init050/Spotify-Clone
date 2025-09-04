from django.contrib import admin
from .models import AudioFile, AudioQuality, StreamingSession, PlaybackSettings

class AudioQualityInline(admin.TabularInline):
    model = AudioQuality
    extra = 1

@admin.register(AudioFile)
class AudioFileAdmin(admin.ModelAdmin):
    list_display = ('track_title', 'status', 'bitrate_kbps', 'sample_rate', 'channels')
    list_filter = ('status', 'bitrate_kbps', 'sample_rate')
    search_fields = ('track__title', 'track__primary_artist__name')
    autocomplete_fields = ['track']
    inlines = [AudioQualityInline]

    def track_title(self, obj):
        return obj.track.title
    track_title.short_description = 'Track'
    track_title.admin_order_field = 'track__title'

@admin.register(AudioQuality)
class AudioQualityAdmin(admin.ModelAdmin):
    list_display = ('audio_file', 'resolution_label', 'bitrate_kbps', 'format')
    list_filter = ('format', 'bitrate_kbps')
    search_fields = ('audio_file__track__title',)
    autocomplete_fields = ['audio_file']

@admin.register(StreamingSession)
class StreamingSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'track', 'started_at', 'last_position_ms', 'ended_at')
    list_filter = ('started_at', 'ended_at')
    search_fields = ('user__email', 'track__title')
    autocomplete_fields = ['user', 'track', 'audio_file']
    date_hierarchy = 'started_at'

@admin.register(PlaybackSettings)
class PlaybackSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'autoplay_next', 'crossfade_seconds', 'shuffle')
    search_fields = ('user__email',)
    autocomplete_fields = ['user', 'default_quality']