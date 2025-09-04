from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from artists.models import Artist
from .models import UserFollowing
from .serializers import FollowSerializer

User = get_user_model()


class FollowView(APIView):
    '''
    View to follow a user or an artist.
    '''
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = FollowSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        followee_id = data['id']
        follow_type = data['type']

        follow_params = {'follower': request.user}
        if follow_type == 'user':
            follow_params['followee_user_id'] = followee_id
        else:  # artist
            follow_params['followee_artist_id'] = followee_id

        # get_or_create handles idempotency and prevents duplicate followings.
        instance, created = UserFollowing.objects.get_or_create(**follow_params)

        if not created:
            return Response({'detail': 'You are already following this target.'}, status=status.HTTP_400_BAD_REQUEST)

        # Here you could return relationship metadata as requested in the prompt
        # For now, a simple success message.
        return Response({'detail': 'Successfully followed.'}, status=status.HTTP_201_CREATED)


class UnfollowView(APIView):
    '''
    View to unfollow a user or an artist.
    '''
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        serializer = FollowSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        followee_id = data['id']
        follow_type = data['type']

        filter_kwargs = {'follower': request.user}
        if follow_type == 'user':
            filter_kwargs['followee_user_id'] = followee_id
        else:  # artist
            filter_kwargs['followee_artist_id'] = followee_id

        # Using get_object_or_404 to find the specific follow relationship
        instance = get_object_or_404(UserFollowing, **filter_kwargs)

        instance.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
