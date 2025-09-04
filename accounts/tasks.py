from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from .models import CustomUser


@shared_task
def send_password_reset_email(user_id):
    '''
    Sends a password reset email to the user.
    '''
    try:
        user = CustomUser.objects.get(pk=user_id)
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # NOTE: The domain and path should be configured for production
        reset_link = f'http://localhost:3000/reset-password-confirm/?uidb64={uid}&token={token}'

        subject = 'Reset your password'
        message = f'Hi {user.email},\n\nPlease click the link below to reset your password:\n{reset_link}\n\nThanks,'

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
    except CustomUser.DoesNotExist:
        pass


@shared_task
def send_verification_email(user_id):
    '''
    Sends a verification email to the user.
    '''
    try:
        user = CustomUser.objects.get(pk=user_id)
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # NOTE: The domain should be configured in settings or an env var for production
        verification_link = f'http://localhost:8000/api/v1/auth/verify-email/?uidb64={uid}&token={token}'

        subject = 'Verify your email address'
        message = f'Hi {user.email},\n\nPlease click the link below to verify your email address:\n{verification_link}\n\nThanks,'

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
    except CustomUser.DoesNotExist:
        # Handle user not found case
        pass
