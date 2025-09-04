import pyotp
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import CustomUser, UserProfile, UserPreferences, UserSession
from django.core.signing import Signer
from django.core.cache import cache
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.signing import BadSignature
from django.contrib.auth.hashers import check_password

class TwoFactorLoginVerifySerializer(serializers.Serializer):
    user_id_signed = serializers.CharField()
    totp_code = serializers.CharField()

    def validate(self, attrs):
        signer = Signer()
        try:
            user_id = signer.unsign(attrs['user_id_signed'])
            user = CustomUser.objects.get(pk=user_id)
        except (BadSignature, CustomUser.DoesNotExist):
            raise serializers.ValidationError('Invalid user ID.')

        totp = pyotp.TOTP(user.totp_secret)
        if totp.verify(attrs['totp_code']):
            self.user = user
            return attrs

        # Check backup codes
        for hashed_code in user.totp_backup_codes:
            if check_password(attrs['totp_code'], hashed_code):
                # Remove the used backup code
                user.totp_backup_codes.remove(hashed_code)
                user.save(update_fields=['totp_backup_codes'])
                self.user = user
                return attrs

        raise serializers.ValidationError('Invalid 2FA code.')


class UserSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSession
        fields = ['id', 'device_name', 'user_agent', 'ip_address', 'last_active', 'created_at']
        read_only_fields = fields

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['display_name', 'avatar', 'bio', 'country', 'locale']

class UserPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreferences
        fields = ['playback_quality', 'explicit_content_filter', 'language', 'notification_settings']


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError('User with this email does not exist.')
        return value


class TwoFactorVerifySerializer(serializers.Serializer):
    totp_code = serializers.CharField(max_length=6)


class TwoFactorDisableSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    totp_code = serializers.CharField(max_length=6, write_only=True)

    def validate(self, attrs):
        user = self.context['request'].user

        # Check password
        if not user.check_password(attrs['password']):
            raise serializers.ValidationError({'password': 'Incorrect password.'})

        # Check TOTP code
        if not user.two_factor_enabled or not user.totp_secret:
            raise serializers.ValidationError({'totp_code': '2FA is not enabled for this account.'})

        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(attrs['totp_code']):
            raise serializers.ValidationError({'totp_code': 'Invalid 2FA code.'})

        return attrs

class PasswordResetConfirmSerializer(serializers.Serializer):
    uidb64 = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)
    new_password2 = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({'new_password': 'Passwords must match.'})

        try:
            uid = force_str(urlsafe_base64_decode(attrs['uidb64']))
            self.user = CustomUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            raise serializers.ValidationError({'uidb64': 'Invalid user ID.'})

        if not default_token_generator.check_token(self.user, attrs['token']):
            raise serializers.ValidationError({'token': 'Invalid or expired token.'})

        return attrs

    def save(self):
        self.user.set_password(self.validated_data['new_password'])
        self.user.save()

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    LOCKOUT_THRESHOLD = 5
    LOCKOUT_TIME = 15 * 60  # 15 minutes in seconds

    def validate(self, attrs):
        email = attrs.get('email')
        cache_key = f'login_failures_{email}'

        # Check if account is already locked before attempting to validate
        if cache.get(cache_key, 0) >= self.LOCKOUT_THRESHOLD:
            raise AuthenticationFailed('Account locked due to too many failed login attempts. Try again later.')

        try:
            data = super().validate(attrs)
        except Exception as e:
            # Broad exception for debugging, should be narrowed down later
            failures = cache.get(cache_key, 0) + 1
            cache.set(cache_key, failures, self.LOCKOUT_TIME)
            # If this attempt caused a lockout, raise the locked error instead of the original one
            if failures >= self.LOCKOUT_THRESHOLD:
                 raise AuthenticationFailed('Account locked due to too many failed login attempts. Try again later.')
            raise e

        # On successful login, reset the failure count
        cache.delete(cache_key)

        # Custom logic to check for 2FA
        if self.user.two_factor_enabled:
            signer = Signer()
            return {
                '2fa_required': True,
                'user_id_signed': signer.sign(self.user.pk)
            }

        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['email'] = user.email
        return token

class UserRegistrationSerializer(serializers.ModelSerializer):
    '''
    Serializer for user registration.
    '''
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'password2']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': 'Passwords must match.'})
        return attrs

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password']
        )
        user.is_active = False
        user.save()
        return user
