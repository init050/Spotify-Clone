from rest_framework import serializers
from django.contrib.auth import get_user_model
import uuid
from artists.models import Artist

User = get_user_model()


class FollowSerializer(serializers.Serializer):
    '''
    Serializer for follow and unfollow actions.
    Validates the type and existence of the followee.
    '''
    type = serializers.ChoiceField(choices=['user', 'artist'])
    id = serializers.CharField()

    def validate(self, data):
        '''
        Check that the user is not trying to follow themselves.
        '''
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError('Request context is required.')

        # By the time this runs, data['id'] has been converted to an int or UUID by validate_id
        if data.get('type') == 'user' and data.get('id') == request.user.id:
            raise serializers.ValidationError('You cannot follow yourself.')

        return data

    def validate_id(self, value):
        '''
        Validate the incoming ID based on the type and convert it to the correct
        data type (int for user, UUID for artist).
        '''
        type = self.initial_data.get('type')

        if type == 'user':
            try:
                user_id = int(value)
                if not User.objects.filter(id=user_id).exists():
                    raise serializers.ValidationError('User with this ID does not exist.')
                return user_id  # Return the validated integer ID
            except (ValueError, TypeError):
                raise serializers.ValidationError('User ID must be a valid integer.')
        elif type == 'artist':
            try:
                artist_id = uuid.UUID(value)
                if not Artist.objects.filter(id=artist_id).exists():
                    raise serializers.ValidationError('Artist with this ID does not exist.')
                return artist_id  # Return the validated UUID object
            except (ValueError, TypeError):
                raise serializers.ValidationError('Artist ID must be a valid UUID.')

        # This should not be reached if type is validated by ChoiceField
        raise serializers.ValidationError('Invalid type specified.')
