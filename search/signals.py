from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.postgres.search import SearchVector
from artists.models import Artist, Album, Track
from playlists.models import Playlist
from django.db import connection

def get_search_vector_kwargs():
    """
    Returns the kwargs for the SearchVector function based on the database backend.
    """
    if 'postgres' in connection.vendor:
        return {'config': 'pg_catalog.english'}
    return {}

@receiver(post_save, sender=Artist)
def update_artist_search_vector(sender, instance, **kwargs):
    """
    Update the search_vector for an Artist instance.
    """
    if 'postgres' in connection.vendor:
        Artist.objects.filter(pk=instance.pk).update(
            search_vector=SearchVector('name', 'bio', **get_search_vector_kwargs())
        )

@receiver(post_save, sender=Album)
def update_album_search_vector(sender, instance, **kwargs):
    """
    Update the search_vector for an Album instance.
    """
    if 'postgres' in connection.vendor:
        Album.objects.filter(pk=instance.pk).update(
            search_vector=SearchVector('title', 'label', **get_search_vector_kwargs())
        )

@receiver(post_save, sender=Track)
def update_track_search_vector(sender, instance, **kwargs):
    """
    Update the search_vector for a Track instance.
    """
    if 'postgres' in connection.vendor:
        Track.objects.filter(pk=instance.pk).update(
            search_vector=SearchVector('title', 'isrc', **get_search_vector_kwargs())
        )

@receiver(post_save, sender=Playlist)
def update_playlist_search_vector(sender, instance, **kwargs):
    """
    Update the search_vector for a Playlist instance.
    """
    if 'postgres' in connection.vendor:
        Playlist.objects.filter(pk=instance.pk).update(
            search_vector=SearchVector('title', 'description', **get_search_vector_kwargs())
        )
