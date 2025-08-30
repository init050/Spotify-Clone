from django.db.models import F
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Artist, ArtistFollower


@receiver(post_save, sender=ArtistFollower)
def increment_follower_count(sender, instance, created, **kwargs):
    '''
    When a follow relationship is created, increment the artist's followers_count.
    '''
    if created:
        Artist.objects.filter(pk=instance.artist.pk).update(followers_count=F('followers_count') + 1)


@receiver(post_delete, sender=ArtistFollower)
def decrement_follower_count(sender, instance, **kwargs):
    '''
    When a follow relationship is deleted, decrement the artist's followers_count.
    We check if the artist still exists to prevent errors during cascading deletes.
    '''
    artist_query = Artist.objects.filter(pk=instance.artist.pk)
    if artist_query.exists():
        artist_query.update(followers_count=F('followers_count') - 1)
