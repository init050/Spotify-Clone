from django.db.models import F
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import UserFollowing
from accounts.models import UserProfile
from artists.models import Artist


@receiver(post_save, sender=UserFollowing, dispatch_uid='increment_follow_counts')
def increment_follow_counts(sender, instance, created, **kwargs):
    '''
    When a follow relationship is created, atomically increment the follower's
    following_count and the followee's followers_count.
    '''
    if created:
        # Use select_for_update to lock the rows and prevent race conditions,
        # although F() expressions are generally safe.
        UserProfile.objects.filter(user=instance.follower).update(following_count=F('following_count') + 1)

        if instance.followee_user:
            UserProfile.objects.filter(user=instance.followee_user).update(followers_count=F('followers_count') + 1)
        elif instance.followee_artist:
            Artist.objects.filter(id=instance.followee_artist_id).update(followers_count=F('followers_count') + 1)


@receiver(post_delete, sender=UserFollowing, dispatch_uid='decrement_follow_counts')
def decrement_follow_counts(sender, instance, **kwargs):
    '''
    When a follow relationship is deleted, atomically decrement the counters.
    We check if the related objects still exist to prevent errors during cascading deletes.
    '''
    follower_profile_qs = UserProfile.objects.filter(user=instance.follower)
    if follower_profile_qs.exists():
        follower_profile_qs.update(following_count=F('following_count') - 1)

    if instance.followee_user:
        followee_profile_qs = UserProfile.objects.filter(user=instance.followee_user)
        if followee_profile_qs.exists():
            followee_profile_qs.update(followers_count=F('followers_count') - 1)
    elif instance.followee_artist:
        # Artist model might be deleted before the signal is processed
        artist_qs = Artist.objects.filter(id=instance.followee_artist_id)
        if artist_qs.exists():
            artist_qs.update(followers_count=F('followers_count') - 1)
