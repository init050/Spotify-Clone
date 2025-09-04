from rest_framework import serializers
from artists.models import Track
from .models import (
    Playlist,
    PlaylistTrack,
    PlaylistCollaborator,
    UserLibrary,
    LibraryItem,
)
from accounts.serializers import UserProfileSerializer
from artists.serializers import TrackSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class PlaylistTrackSerializer(serializers.ModelSerializer):
    track = TrackSerializer(read_only=True)
    added_by = UserProfileSerializer(read_only=True)

    class Meta:
        model = PlaylistTrack
        fields = [
            'id',
            'track',
            'position',
            'added_by',
            'added_at',
        ]


class PlaylistSerializer(serializers.ModelSerializer):
    owner = UserProfileSerializer(read_only=True)

    class Meta:
        model = Playlist
        fields = [
            'id',
            'title',
            'slug',
            'owner',
            'is_public',
            'is_unlisted',
            'cover_image',
            'followers_count',
            'saves_count',
            'plays_count',
        ]


class PlaylistDetailSerializer(PlaylistSerializer):
    tracks = PlaylistTrackSerializer(many=True, read_only=True)
    collaborators = serializers.SerializerMethodField()

    class Meta(PlaylistSerializer.Meta):
        fields = PlaylistSerializer.Meta.fields + [
            'description',
            'tracks',
            'collaborators',
            'version',
        ]

    def get_collaborators(self, obj):
        collaborators = obj.collaborators.all()
        return CollaboratorSerializer(collaborators, many=True).data


class PlaylistWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Playlist
        fields = [
            'title',
            'description',
            'is_public',
            'is_unlisted',
            'allow_duplicates',
        ]


class CollaboratorSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True, source='user.profile')
    user_id = serializers.UUIDField(source='user.id', read_only=True)

    class Meta:
        model = PlaylistCollaborator
        fields = ['id', 'user_id', 'user', 'role']


class CollaboratorWriteSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        slug_field='email',
        queryset=User.objects.all()
    )

    class Meta:
        model = PlaylistCollaborator
        fields = ['user', 'role']


class ReorderMoveSerializer(serializers.Serializer):
    pt_id = serializers.CharField()
    to_index = serializers.IntegerField(min_value=0)


class ReorderSerializer(serializers.Serializer):
    version = serializers.IntegerField(min_value=1)
    moves = ReorderMoveSerializer(many=True)

    def validate(self, data):
        moves = data.get('moves')
        if not moves:
            raise serializers.ValidationError('Moves list cannot be empty.')

        view = self.context.get('view')
        if not view:
            return data # Cannot validate further without view context

        playlist_slug = view.kwargs.get('slug')
        pt_ids = {move['pt_id'] for move in moves}

        tracks_count = PlaylistTrack.objects.filter(
            id__in=pt_ids,
            playlist__slug=playlist_slug
        ).count()

        if tracks_count != len(pt_ids):
            raise serializers.ValidationError('One or more track IDs are invalid or do not belong to this playlist.')

        return data


class LibraryItemSerializer(serializers.ModelSerializer):
    playlist = PlaylistSerializer(read_only=True)

    class Meta:
        model = LibraryItem
        fields = ['id', 'playlist', 'is_pinned']


class LibrarySerializer(serializers.ModelSerializer):
    saved_playlists = LibraryItemSerializer(source='libraryitem_set', many=True, read_only=True)

    class Meta:
        model = UserLibrary
        fields = ['id', 'saved_playlists']
