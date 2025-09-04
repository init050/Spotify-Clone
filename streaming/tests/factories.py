import factory
from django.core.files.base import ContentFile

from artists.tests.factories import UserFactory, TrackFactory
from streaming.models import (
    AudioFile,
    AudioQuality,
    PlaybackSettings,
    StreamingSession,
)
from artists.models import Track


class AudioFileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AudioFile

    track = factory.SubFactory(TrackFactory)
    status = Track.ProcessingStatus.COMPLETED
    original_file = factory.django.FileField(
        from_func=lambda: ContentFile(b'dummy audio content', 'master.mp3')
    )
    hls_master = factory.django.FileField(
        from_func=lambda: ContentFile(b'#EXTM3U', 'master.m3u8')
    )

class AudioQualityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AudioQuality

    audio_file = factory.SubFactory(AudioFileFactory)
    bitrate_kbps = 128
    resolution_label = factory.LazyAttribute(lambda o: f'{o.bitrate_kbps}kbps')
    format = 'hls'
    file = factory.django.FileField(
        from_func=lambda: ContentFile(b'dummy segment content', 'segment.ts')
    )


class StreamingSessionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StreamingSession

    user = factory.SubFactory(UserFactory)
    track = factory.SubFactory(TrackFactory)
    audio_file = factory.SubFactory(
        AudioFileFactory,
        track=factory.SelfAttribute('..track') # Ensure audio_file and session have the same track
    )


class PlaybackSettingsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PlaybackSettings

    user = factory.SubFactory(UserFactory)
    autoplay_next = True
    crossfade_seconds = 0
    shuffle = False
