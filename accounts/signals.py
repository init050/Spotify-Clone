from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, UserProfile, UserPreferences

@receiver(post_save, sender=CustomUser)
def create_user_profile_and_preferences(sender, instance, created, **kwargs):
    '''
    Create UserProfile and UserPreferences when a new CustomUser is created.
    '''
    if created:
        UserProfile.objects.create(user=instance)
        UserPreferences.objects.create(user=instance)

@receiver(post_save, sender=CustomUser)
def save_user_profile_and_preferences(sender, instance, **kwargs):
    '''
    Save UserProfile and UserPreferences when a CustomUser is saved.
    '''
    instance.profile.save()
    instance.preferences.save()
