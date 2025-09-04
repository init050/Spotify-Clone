
from django.conf import settings
from django.db import models

# Using the BaseModel and ProcessingStatus from the 'artists' app for consistency.
from artists.models import BaseModel, Track


class AudioFile(BaseModel):
    'Represents the master audio file and its technical metadata.'
    track = models.OneToOneField(
        Track,
        on_delete=models.CASCADE,
        related_name='audio_file_data'
    )
    status = models.CharField(
        max_length=20,
        choices=Track.ProcessingStatus.choices,
        default=Track.ProcessingStatus.PENDING,
        db_index=True
    )
    original_file = models.FileField(upload_to='tracks/original_masters/')
    hls_master = models.FileField(upload_to='tracks/hls/', null=True, blank=True, help_text='HLS playlist (.m3u8)')
    dash_master = models.FileField(upload_to='tracks/dash/', null=True, blank=True, help_text='DASH manifest (.mpd)')
    waveform_json = models.JSONField(null=True, blank=True)
    bitrate_kbps = models.PositiveSmallIntegerField(null=True, blank=True)
    sample_rate = models.PositiveIntegerField(null=True, blank=True)
    channels = models.PositiveSmallIntegerField(null=True, blank=True)
    loudness_lufs = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    metadata = models.JSONField(default=dict, help_text='duration, codec, format, key, bpm')

    class Meta:
        verbose_name = 'Audio File'
        verbose_name_plural = 'Audio Files'
        ordering = ['-created_at']

    def __str__(self):
        return f'Audio for {self.track.title}'


class AudioQuality(BaseModel):
    'Represents a specific transcoded quality level of an AudioFile.'
    class AudioFormat(models.TextChoices):
        HLS = 'hls', 'HLS'
        DASH = 'dash', 'DASH'
        MP3 = 'mp3', 'MP3'
        AAC = 'aac', 'AAC'
        FLAC = 'flac', 'FLAC'

    audio_file = models.ForeignKey(
        AudioFile,
        on_delete=models.CASCADE,
        related_name='qualities'
    )
    bitrate_kbps = models.PositiveSmallIntegerField()
    resolution_label = models.CharField(max_length=20, help_text='e.g., 64kbps, 128kbps')
    file = models.FileField(upload_to='tracks/transcoded/')
    format = models.CharField(max_length=10, choices=AudioFormat.choices)

    class Meta:
        verbose_name = 'Audio Quality'
        verbose_name_plural = 'Audio Qualities'
        ordering = ['audio_file', '-bitrate_kbps']
        indexes = [
            models.Index(fields=['audio_file', 'bitrate_kbps']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['audio_file', 'bitrate_kbps', 'format'], name='unique_quality_for_file')
        ]

    def __str__(self):
        return f'{self.audio_file.track.title} ({self.resolution_label})'


class StreamingSession(BaseModel):
    'Tracks a user\'s listening session for a particular track.'
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='streaming_sessions',
        null=True, # For anonymous users
        blank=True
    )
    track = models.ForeignKey(
        Track,
        on_delete=models.CASCADE,
        related_name='streaming_sessions'
    )
    audio_file = models.ForeignKey(
        AudioFile,
        on_delete=models.CASCADE,
        related_name='streaming_sessions'
    )
    started_at = models.DateTimeField(auto_now_add=True)
    last_position_ms = models.PositiveIntegerField(default=0)
    ended_at = models.DateTimeField(null=True, blank=True)
    device_info = models.JSONField(null=True, blank=True, help_text='user_agent, IP, device')

    class Meta:
        verbose_name = 'Streaming Session'
        verbose_name_plural = 'Streaming Sessions'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', 'track', 'started_at']),
        ]

    def __str__(self):
        if self.user:
            return f'Session for {self.user} on {self.track.title}'
        return f'Anonymous session on {self.track.title}'


class PlaybackSettings(BaseModel):
    'Stores user-specific playback preferences.'
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='playback_settings'
    )
    default_quality = models.ForeignKey(
        AudioQuality,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    autoplay_next = models.BooleanField(default=True)
    crossfade_seconds = models.PositiveSmallIntegerField(default=0)
    shuffle = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Playback Settings'
        verbose_name_plural = 'Playback Settings'

    def __str__(self):
        return f'Playback settings for {self.user.username}'
