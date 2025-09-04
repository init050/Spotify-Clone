from rest_framework import serializers
from .models import Notification, PushNotificationDevice, NotificationSettings

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('id', 'type', 'payload', 'is_read', 'created_at')

class NotificationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSettings
        fields = ('email_enabled', 'push_enabled', 'inapp_enabled', 'daily_digest')

class PushNotificationDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PushNotificationDevice
        fields = ('id', 'provider', 'token', 'platform')
        read_only_fields = ('id',)

    def create(self, validated_data):
        # Get the user from the request
        user = self.context['request'].user
        # Create the device
        device, created = PushNotificationDevice.objects.update_or_create(
            user=user,
            token=validated_data['token'],
            defaults=validated_data
        )
        return device
