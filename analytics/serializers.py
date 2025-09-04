from rest_framework import serializers
from .models import PlayHistory, UserAnalytics, ContentAnalytics

class PlayHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayHistory
        fields = (
            'user',
            'track_id',
            'started_at',
            'ended_at',
            'position_ms',
            'duration_ms',
            'device_info'
        )

class PlayEventSerializer(serializers.Serializer):
    user_id = serializers.UUIDField(required=False, allow_null=True) # Allow anonymous events
    track_id = serializers.UUIDField()
    event = serializers.ChoiceField(choices=['start', 'progress', 'complete', 'pause'])
    position_ms = serializers.IntegerField()
    duration_ms = serializers.IntegerField(required=False, allow_null=True)
    device_info = serializers.JSONField(required=False)
    timestamp = serializers.DateTimeField()

    def validate_user_id(self, value):
        # In a real app, you might want to ensure the user exists
        # For now, we just accept the UUID
        return value

class UserAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAnalytics
        fields = ('date', 'play_seconds', 'plays', 'unique_tracks')

class ContentAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentAnalytics
        fields = ('date', 'plays', 'completes', 'skips', 'avg_listen_ms')
