from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from artists.models import BaseModel, Track
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex


class Playlist(BaseModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='playlists')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    is_public = models.BooleanField(default=False)
    is_unlisted = models.BooleanField(default=False)
    share_token = models.CharField(max_length=32, null=True, blank=True, db_index=True)
    cover_image = models.ImageField(upload_to='playlists/covers/', null=True, blank=True)
    followers_count = models.PositiveIntegerField(default=0)
    saves_count = models.PositiveIntegerField(default=0)
    plays_count = models.PositiveIntegerField(default=0)
    version = models.PositiveIntegerField(default=1)
    allow_duplicates = models.BooleanField(default=True)
    likes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    reposts_count = models.PositiveIntegerField(default=0)
    search_vector = SearchVectorField(null=True, editable=False)

    class Meta:
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['owner', '-updated_at']),
            models.Index(fields=['is_public', '-plays_count']),
            GinIndex(fields=['search_vector'], name='playlist_search_vector_idx'),
        ]
        ordering = ['-updated_at']

    def __str__(self):
        return self.title


class PlaylistTrack(BaseModel):
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='tracks')
    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name='playlist_tracks')
    position = models.IntegerField(db_index=True)
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='added_playlist_tracks'
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['position']

    def save(self, *args, **kwargs):
        if not self.playlist.allow_duplicates:
            if PlaylistTrack.objects.filter(playlist=self.playlist, track=self.track).exists():
                raise ValidationError('This track already exists in the playlist and duplicates are not allowed.')
        super().save(*args, **kwargs)


class PlaylistCollaborator(BaseModel):
    class Role(models.TextChoices):
        EDITOR = 'editor', 'Editor'
        VIEWER = 'viewer', 'Viewer'

    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='collaborators')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='collaborations')
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.VIEWER)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['playlist', 'user'], name='unique_collaborator_in_playlist')
        ]
        ordering = ['-created_at']




class UserLibrary(BaseModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='library')
    saved_playlists = models.ManyToManyField(Playlist, through='LibraryItem')

    def __str__(self):
        return f"{self.user.email}'s Library"


class LibraryItem(BaseModel):
    library = models.ForeignKey(UserLibrary, on_delete=models.CASCADE)
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    is_pinned = models.BooleanField(default=False)
    # folder = models.ForeignKey('LibraryFolder', on_delete=models.SET_NULL, null=True, blank=True) # Optional

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['library', 'playlist'], name='unique_playlist_in_library')
        ]
        ordering = ['-created_at']
