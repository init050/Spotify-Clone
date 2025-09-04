import uuid
from django.db import models
from django.conf import settings

class SearchHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text='The user who performed the search. Null for anonymous users.'
    )
    query = models.TextField()
    filters = models.JSONField(null=True, blank=True, help_text="e.g. {'type': 'track', 'genre': 'rock'}")
    results_count = models.IntegerField()
    clicked_item = models.JSONField(null=True, blank=True, help_text='Metadata of the first clicked item.')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Search for "{self.query}" by {self.user or "Anonymous"}'

    class Meta:
        verbose_name_plural = 'Search Histories'
        ordering = ['-created_at']


class SearchAnalytics(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    query = models.TextField(db_index=True)
    count = models.PositiveIntegerField(default=1, help_text='Aggregated number of times this query was searched.')
    avg_click_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0.0)
    last_seen_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Analytics for "{self.query}"'

    class Meta:
        verbose_name_plural = 'Search Analytics'
        ordering = ['-last_seen_at']


class Recommendation(models.Model):
    class ItemType(models.TextChoices):
        TRACK = 'track', 'Track'
        ALBUM = 'album', 'Album'
        ARTIST = 'artist', 'Artist'
        PLAYLIST = 'playlist', 'Playlist'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text='The user for whom the recommendation is. Null for global recommendations.'
    )
    item_type = models.CharField(max_length=10, choices=ItemType.choices)
    item_id = models.UUIDField(help_text='Points to the ID of the Track/Album/Artist/Playlist.')
    score = models.DecimalField(max_digits=8, decimal_places=6)
    model_version = models.CharField(max_length=32, help_text='Which recommendation model version produced this.')
    metadata = models.JSONField(null=True, blank=True, help_text='Why this item was recommended.')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Recommendation for {self.user or "Global"}: {self.item_type} {self.item_id}'

    class Meta:
        ordering = ['-score']


class TrendingContent(models.Model):
    class ContentType(models.TextChoices):
        TRACK = 'track', 'Track'
        ALBUM = 'album', 'Album'
        ARTIST = 'artist', 'Artist'
        PLAYLIST = 'playlist', 'Playlist'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_type = models.CharField(max_length=10, choices=ContentType.choices)
    content_id = models.UUIDField()
    score = models.DecimalField(max_digits=10, decimal_places=6, help_text='Final trending score.')
    window_start = models.DateTimeField()
    window_end = models.DateTimeField()
    computed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Trending {self.content_type}: {self.content_id}'

    class Meta:
        verbose_name_plural = 'Trending Contents'
        ordering = ['-score']
