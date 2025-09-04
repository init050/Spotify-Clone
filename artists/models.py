import uuid

from django.conf import settings
from django.db import models
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db.models import (
    CheckConstraint,
    Q,
    UniqueConstraint,
)


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Genre(BaseModel):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children'
    )

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            GinIndex(fields=['name'], name='genre_name_gin_idx', opclasses=['gin_trgm_ops']),
        ]

    def __str__(self):
        return self.name


class Artist(BaseModel):
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=255, unique=True)
    bio = models.TextField(null=True, blank=True)
    country = models.CharField(max_length=2, null=True, blank=True)  # ISO 3166-1 alpha-2
    avatar = models.ImageField(upload_to='artists/avatars/', null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    monthly_listeners = models.PositiveIntegerField(default=0)
    followers_count = models.PositiveIntegerField(default=0)
    managers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='managed_artists',
        blank=True
    )

    search_vector = SearchVectorField(null=True, editable=False)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            GinIndex(fields=['name'], name='artist_name_gin_idx', opclasses=['gin_trgm_ops']),
            GinIndex(fields=['search_vector'], name='artist_search_vector_idx'),
        ]

    def __str__(self):
        return self.name


class Album(BaseModel):
    class AlbumType(models.TextChoices):
        ALBUM = 'album', 'Album'
        SINGLE = 'single', 'Single'
        EP = 'ep', 'EP'
        COMPILATION = 'compilation', 'Compilation'

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=255, unique=True)
    primary_artist = models.ForeignKey(
        Artist,
        on_delete=models.PROTECT,
        related_name='albums_as_primary_artist'
    )
    artists = models.ManyToManyField(
        Artist,
        through='AlbumArtist',
        related_name='albums'
    )
    release_date = models.DateField(null=True, blank=True, db_index=True)
    cover = models.ImageField(upload_to='albums/covers/', null=True, blank=True)
    album_type = models.CharField(max_length=20, choices=AlbumType.choices, default=AlbumType.ALBUM)
    label = models.CharField(max_length=120, null=True, blank=True)
    total_tracks = models.PositiveSmallIntegerField(default=0)
    is_explicit = models.BooleanField(default=False)
    likes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)

    search_vector = SearchVectorField(null=True, editable=False)

    class Meta:
        ordering = ['-release_date', 'title']
        indexes = [
            models.Index(fields=['title']),
            GinIndex(fields=['title'], name='album_title_gin_idx', opclasses=['gin_trgm_ops']),
            GinIndex(fields=['search_vector'], name='album_search_vector_idx'),
        ]
        constraints = [
            CheckConstraint(check=Q(total_tracks__gte=0), name='total_tracks_gte_0'),
        ]

    def __str__(self):
        return self.title


class AlbumArtist(BaseModel):
    class ArtistRole(models.TextChoices):
        PRIMARY = 'primary', 'Primary'
        FEATURED = 'featured', 'Featured'

    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ArtistRole.choices, default=ArtistRole.PRIMARY)

    class Meta:
        constraints = [
            UniqueConstraint(fields=['album', 'artist'], name='unique_album_artist')
        ]
        ordering = ['album', 'artist']


class Track(BaseModel):
    class ProcessingStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    title = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=255, unique=True)
    album = models.ForeignKey(
        Album,
        on_delete=models.CASCADE,
        related_name='tracks'
    )
    primary_artist = models.ForeignKey(
        Artist,
        on_delete=models.PROTECT,
        related_name='tracks_as_primary_artist'
    )
    artists = models.ManyToManyField(
        Artist,
        through='TrackArtist',
        related_name='tracks'
    )
    genres = models.ManyToManyField(Genre, related_name='tracks', blank=True)
    track_number = models.PositiveSmallIntegerField()
    disc_number = models.PositiveSmallIntegerField(default=1)
    duration_ms = models.PositiveIntegerField()
    is_explicit = models.BooleanField(default=False)
    isrc = models.CharField(max_length=12, null=True, blank=True)
    audio_original = models.FileField(upload_to='tracks/original/')
    audio_hls_master = models.FileField(upload_to='tracks/hls/', null=True, blank=True)
    waveform_json = models.JSONField(null=True, blank=True)
    bitrate_kbps = models.PositiveSmallIntegerField(null=True, blank=True)
    loudness_lufs = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    sample_rate = models.PositiveIntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    popularity = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING,
        db_index=True
    )
    likes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    reposts_count = models.PositiveIntegerField(default=0)

    search_vector = SearchVectorField(null=True, editable=False)

    class Meta:
        ordering = ['album', 'disc_number', 'track_number']
        indexes = [
            models.Index(fields=['popularity']),
            models.Index(fields=['album', 'track_number']),
            GinIndex(fields=['title'], name='track_title_gin_idx', opclasses=['gin_trgm_ops']),
            GinIndex(fields=['search_vector'], name='track_search_vector_idx'),
        ]
        constraints = [
            UniqueConstraint(fields=['album', 'disc_number', 'track_number'], name='unique_track_in_album'),
            CheckConstraint(check=Q(duration_ms__gt=0), name='duration_ms_gt_0'),
            CheckConstraint(check=Q(popularity__gte=0) & Q(popularity__lte=100), name='popularity_between_0_and_100'),
            UniqueConstraint(fields=['isrc'], condition=Q(isrc__isnull=False), name='unique_isrc_if_not_null'),
        ]

    def __str__(self):
        return self.title


class TrackArtist(BaseModel):
    class ArtistRole(models.TextChoices):
        PRIMARY = 'primary', 'Primary'
        FEATURED = 'featured', 'Featured'
        REMIXER = 'remixer', 'Remixer'
        PRODUCER = 'producer', 'Producer'

    track = models.ForeignKey(Track, on_delete=models.CASCADE)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ArtistRole.choices, default=ArtistRole.PRIMARY)

    class Meta:
        constraints = [
            UniqueConstraint(fields=['track', 'artist'], name='unique_track_artist')
        ]
        ordering = ['track', 'artist']


