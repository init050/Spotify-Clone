from rest_framework import serializers

from artists.models import Track
from .models import (
    AudioFile,
    AudioQuality,
    PlaybackSettings,
    StreamingSession,
)


class AudioQualitySerializer(serializers.ModelSerializer):
    'Serializer for the AudioQuality model.'
    class Meta:
        model = AudioQuality
        fields = [
            'id',
            'resolution_label',
            'bitrate_kbps',
            'format',
            'file',
        ]


class AudioFileSerializer(serializers.ModelSerializer):
    'Serializer for the AudioFile model, including its available qualities.'
    qualities = AudioQualitySerializer(many=True, read_only=True)
    track_id = serializers.UUIDField(source='track.id', read_only=True)

    class Meta:
        model = AudioFile
        fields = [
            'id',
            'track_id',
            'original_file',
            'hls_master',
            'dash_master',
            'waveform_json',
            'metadata',
            'qualities',
        ]


class PlaybackSettingsSerializer(serializers.ModelSerializer):
    'Serializer for user playback settings.'

    class Meta:
        model = PlaybackSettings
        fields = [
            'default_quality',
            'autoplay_next',
            'crossfade_seconds',
            'shuffle',
        ]
        # The user is implicitly the current authenticated user from the request.
        # We don't need to expose it in the API fields.


class StreamingSessionSerializer(serializers.ModelSerializer):
    'Serializer for creating and listing streaming sessions.'
    user = serializers.StringRelatedField()
    track = serializers.StringRelatedField()

    class Meta:
        model = StreamingSession
        fields = [
            'id',
            'user',
            'track',
            'audio_file',
            'started_at',
            'last_position_ms',
            'ended_at',
            'device_info',
        ]
        read_only_fields = [
            'id',
            'user',
            'track',
            'audio_file',
            'started_at',
            'ended_at',
        ]


class StreamingSessionUpdateSerializer(serializers.ModelSerializer):
    'A specific serializer just for updating the position of a session.'
    class Meta:
        model = StreamingSession
        fields = ['last_position_ms']


class StreamingSessionCreateSerializer(serializers.ModelSerializer):
    'Serializer for starting a new streaming session.'
    track = serializers.PrimaryKeyRelatedField(
        queryset=Track.objects.filter(
            audio_file_data__status=Track.ProcessingStatus.COMPLETED
        )
    )

    class Meta:
        model = StreamingSession
        fields = ['track', 'device_info']
