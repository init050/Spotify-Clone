import secrets
import uuid

from django.conf import settings
from django.db import models
from django.db.models import CheckConstraint, F, Q, UniqueConstraint

from artists.models import BaseModel


class UserFollowing(BaseModel):
    '''
    Represents a follow relationship between a user and another user or an artist.
    '''
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='following'
    )
    followee_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='followers'
    )
    followee_artist = models.ForeignKey(
        'artists.Artist',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='artist_followers'
    )

    class Meta:
        ordering = ['-created_at']
        constraints = [
            UniqueConstraint(
                fields=['follower', 'followee_user'],
                name='unique_user_follow',
                condition=Q(followee_user__isnull=False)
            ),
            UniqueConstraint(
                fields=['follower', 'followee_artist'],
                name='unique_artist_follow',
                condition=Q(followee_artist__isnull=False)
            ),
            CheckConstraint(
                check=(
                    Q(followee_user__isnull=False, followee_artist__isnull=True) |
                    Q(followee_user__isnull=True, followee_artist__isnull=False)
                ),
                name='check_one_followee_type'
            ),
            CheckConstraint(
                check=~Q(follower_id=F('followee_user_id')),
                name='prevent_self_follow'
            )
        ]
        indexes = [
            models.Index(fields=['follower', 'followee_user']),
            models.Index(fields=['follower', 'followee_artist']),
            models.Index(fields=['followee_user']),
        ]

    def __str__(self):
        if self.followee_user:
            return f'{self.follower} follows {self.followee_user}'
        return f'{self.follower} follows {self.followee_artist}'


class ActivityFeedItem(BaseModel):
    '''
    Represents an item in a user's activity feed. Canonical log of all actions.
    '''
    class Verb(models.TextChoices):
        FOLLOW = 'follow', 'Follow'
        LIKE = 'like', 'Like'
        COMMENT = 'comment', 'Comment'
        SHARE = 'share', 'Share'
        CREATE_PLAYLIST = 'create_playlist', 'Create Playlist'
        UPLOAD_TRACK = 'upload_track', 'Upload Track'
        REPOST = 'repost', 'Repost'

    class ObjectType(models.TextChoices):
        TRACK = 'track', 'Track'
        ALBUM = 'album', 'Album'
        PLAYLIST = 'playlist', 'Playlist'
        ARTIST = 'artist', 'Artist'
        USER = 'user', 'User'
        COMMENT = 'comment', 'Comment'

    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    verb = models.CharField(max_length=20, choices=Verb.choices)
    object_type = models.CharField(max_length=20, choices=ObjectType.choices)
    object_id = models.UUIDField()
    target_type = models.CharField(max_length=20, choices=ObjectType.choices, null=True, blank=True)
    target_id = models.UUIDField(null=True, blank=True)
    data = models.JSONField(default=dict, blank=True)
    is_public = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['actor', '-created_at']),
            models.Index(fields=['is_public', '-created_at']),
            models.Index(fields=['object_type', 'object_id']),
        ]

    def __str__(self):
        return f'{self.actor} {self.verb} {self.object_type}:{self.object_id}'


class ShareableContent(BaseModel):
    '''
    Manages shareable links for content with unique tokens.
    '''
    class ContentType(models.TextChoices):
        TRACK = 'track', 'Track'
        ALBUM = 'album', 'Album'
        PLAYLIST = 'playlist', 'Playlist'
        ARTIST = 'artist', 'Artist'

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content_type = models.CharField(max_length=20, choices=ContentType.choices)
    content_id = models.UUIDField()
    share_token = models.CharField(max_length=48, unique=True, default=secrets.token_urlsafe)
    is_unlisted = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            UniqueConstraint(fields=['owner', 'content_type', 'content_id'], name='unique_shareable_content')
        ]
        indexes = [
            models.Index(fields=['share_token']),
        ]

    def __str__(self):
        return f'Share token for {self.content_type}:{self.content_id}'


class SocialInteraction(BaseModel):
    '''
    Generic model for interactions like likes, reposts, saves, etc.
    '''
    class InteractionType(models.TextChoices):
        LIKE = 'like', 'Like'
        SAVE = 'save', 'Save'
        REPOST = 'repost', 'Repost'
        FOLLOWBACK = 'followback', 'Followback'

    class ObjectType(models.TextChoices):
        TRACK = 'track', 'Track'
        ALBUM = 'album', 'Album'
        PLAYLIST = 'playlist', 'Playlist'
        ARTIST = 'artist', 'Artist'
        COMMENT = 'comment', 'Comment'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='interactions')
    interaction_type = models.CharField(max_length=20, choices=InteractionType.choices)
    object_type = models.CharField(max_length=20, choices=ObjectType.choices)
    object_id = models.UUIDField()

    class Meta:
        ordering = ['-created_at']
        constraints = [
            UniqueConstraint(
                fields=['user', 'interaction_type', 'object_type', 'object_id'],
                name='unique_user_interaction'
            )
        ]
        indexes = [
            models.Index(fields=['user', 'interaction_type']),
            models.Index(fields=['object_type', 'object_id']),
        ]

    def __str__(self):
        return f'{self.user} {self.interaction_type} {self.object_type}:{self.object_id}'


class Comment(BaseModel):
    '''
    Model for comments on various content types, with support for threading.
    '''
    class ObjectType(models.TextChoices):
        TRACK = 'track', 'Track'
        ALBUM = 'album', 'Album'
        PLAYLIST = 'playlist', 'Playlist'

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    object_type = models.CharField(max_length=20, choices=ObjectType.choices)
    object_id = models.UUIDField()
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )
    body = models.TextField()
    edited_at = models.DateTimeField(null=True, blank=True)
    deleted = models.BooleanField(default=False)  # Soft delete

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['object_type', 'object_id', 'created_at']),
        ]

    def __str__(self):
        return f'Comment by {self.author} on {self.object_type}:{self.object_id}'


class Notification(BaseModel):
    '''
    Model for user notifications.
    '''
    class NotificationType(models.TextChoices):
        FOLLOW = 'follow', 'Follow'
        LIKE = 'like', 'Like'
        COMMENT = 'comment', 'Comment'
        REPOST = 'repost', 'Repost'
        MENTION = 'mention', 'Mention'
        SYSTEM = 'system', 'System'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    type = models.CharField(max_length=20, choices=NotificationType.choices)
    actor_id = models.UUIDField(null=True, blank=True)
    object_type = models.CharField(
        max_length=20,
        choices=ActivityFeedItem.ObjectType.choices,
        null=True,
        blank=True
    )
    object_id = models.UUIDField(null=True, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    delivered = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f'Notification for {self.user}: {self.type}'
