import uuid
from django.contrib.auth.models import (
    AbstractUser,
    BaseUserManager,
)
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    '''
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    '''
    def normalize_email(self, email):
        """
        Normalize the email address by lowercasing it.
        """
        return email.lower()

    def create_user(self, email, password, **extra_fields):
        '''
        Create and save a User with the given email and password.
        '''
        if not email:
            raise ValueError(_('The Email must be set'))

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        '''
        Create and save a SuperUser with the given email and password.
        '''
        email = self.normalize_email(email) # Added this line for safety
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    '''
    Custom user model.
    '''
    username = None
    email = models.EmailField(_('email address'), unique=True)

    is_email_verified = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    two_factor_enabled = models.BooleanField(default=False)
    totp_secret = models.CharField(max_length=255, blank=True, null=True)
    totp_backup_codes = models.JSONField(default=list, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email


class UserProfile(models.Model):
    '''
    User profile model.
    '''
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    display_name = models.CharField(max_length=255, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(blank=True)
    country = models.CharField(max_length=2, blank=True)
    locale = models.CharField(max_length=10, blank=True)
    followers_count = models.PositiveIntegerField(default=0)
    following_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'{self.user.email} Profile'


class UserPreferences(models.Model):
    '''
    User preferences model.
    '''
    class PlaybackQuality(models.TextChoices):
        LOW = 'LOW', _('Low')
        NORMAL = 'NORMAL', _('Normal')
        HIGH = 'HIGH', _('High')
        LOSSLESS = 'LOSSLESS', _('Lossless')

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='preferences'
    )
    playback_quality = models.CharField(
        max_length=10,
        choices=PlaybackQuality.choices,
        default=PlaybackQuality.NORMAL
    )
    explicit_content_filter = models.BooleanField(default=True)
    language = models.CharField(max_length=10, default='en')
    notification_settings = models.JSONField(default=dict)

    def __str__(self):
        return f'{self.user.email} Preferences'


class UserSubscription(models.Model):
    '''
    User subscription model.
    '''
    class SubscriptionStatus(models.TextChoices):
        ACTIVE = 'ACTIVE', _('Active')
        CANCELED = 'CANCELED', _('Canceled')
        PAST_DUE = 'PAST_DUE', _('Past Due')
        INACTIVE = 'INACTIVE', _('Inactive')

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    plan_name = models.CharField(max_length=100)
    status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.INACTIVE
    )
    started_at = models.DateTimeField()
    expires_at = models.DateTimeField(null=True, blank=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f'{self.user.email} - {self.plan_name} ({self.status})'


class UserSession(models.Model):
    '''
    Model to store active user sessions for session management.
    '''
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sessions')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device_name = models.CharField(max_length=255)
    user_agent = models.CharField(max_length=512)
    ip_address = models.GenericIPAddressField()
    last_active = models.DateTimeField(auto_now=True)
    refresh_token_jti = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.email} on {self.device_name}'
