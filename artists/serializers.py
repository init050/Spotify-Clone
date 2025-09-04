from rest_framework import serializers

from .models import (
    Album,
    Artist,
    Genre,
    Track,
)


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = [
            'id',
            'name',
            'slug',
            'parent',
        ]


class ArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = [
            'id',
            'name',
            'slug',
            'avatar',
            'is_verified',
            'followers_count',
            'monthly_listeners',
        ]


class ArtistDetailSerializer(ArtistSerializer):
    top_tracks = serializers.SerializerMethodField()
    latest_albums = serializers.SerializerMethodField()

    class Meta(ArtistSerializer.Meta):
        fields = ArtistSerializer.Meta.fields + ['bio', 'country', 'top_tracks', 'latest_albums']

    def get_top_tracks(self, obj):
        '''Returns the top 5 tracks by popularity.'''
        top_tracks = obj.tracks.order_by('-popularity')[:5]
        return TrackSerializer(top_tracks, many=True, context=self.context).data

    def get_latest_albums(self, obj):
        '''Returns the latest 5 albums by release date.'''
        # Note: This gets albums where the artist is a collaborator, not just primary.
        # The model might need adjustment if only primary artist's albums are desired.
        latest_albums = obj.albums.order_by('-release_date').distinct()[:5]
        return AlbumSerializer(latest_albums, many=True, context=self.context).data


class ArtistWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = [
            'name',
            'slug',
            'bio',
            'country',
            'avatar',
            'is_verified',
            'managers',
        ]


class AlbumWriteSerializer(serializers.ModelSerializer):
    primary_artist = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Artist.objects.all(),
    )

    class Meta:
        model = Album
        fields = [
            'title',
            'slug',
            'primary_artist',
            'release_date',
            'cover',
            'album_type',
            'label',
            'artists', # For M2M relationships
        ]


class TrackWriteSerializer(serializers.ModelSerializer):
    album = serializers.SlugRelatedField(slug_field='slug', queryset=Album.objects.all())
    primary_artist = serializers.SlugRelatedField(slug_field='slug', queryset=Artist.objects.all())
    genres = serializers.SlugRelatedField(slug_field='slug', queryset=Genre.objects.all(), many=True, required=False)
    artists = serializers.SlugRelatedField(slug_field='slug', queryset=Artist.objects.all(), many=True, required=False)

    class Meta:
        model = Track
        fields = [
            'title', 'slug', 'album', 'primary_artist', 'artists', 'genres',
            'track_number', 'disc_number', 'duration_ms', 'is_explicit', 'isrc'
        ]


class UploadInitSerializer(serializers.Serializer):
    filename = serializers.CharField(max_length=255)
    file_size = serializers.IntegerField(min_value=1)
    mime_type = serializers.CharField(max_length=100)


class UploadCompleteSerializer(serializers.Serializer):
    upload_id = serializers.UUIDField()
    object_name = serializers.CharField(max_length=1024)
    track_id = serializers.UUIDField()

    def validate_track_id(self, value):
        if not Track.objects.filter(pk=value).exists():
            raise serializers.ValidationError('Track with this ID does not exist.')
        return value


class SearchResultSerializer(serializers.Serializer):
    type = serializers.CharField(read_only=True)
    score = serializers.FloatField(read_only=True)
    item = serializers.SerializerMethodField()

    def get_item(self, obj):
        model_type = obj.get('type')
        instance = obj.get('instance')

        if model_type == 'artist':
            return ArtistSerializer(instance, context=self.context).data
        if model_type == 'album':
            return AlbumSerializer(instance, context=self.context).data
        if model_type == 'track':
            return TrackSerializer(instance, context=self.context).data
        if model_type == 'genre':
            return GenreSerializer(instance, context=self.context).data
        return None


class AlbumSerializer(serializers.ModelSerializer):
    primary_artist = serializers.StringRelatedField()

    class Meta:
        model = Album
        fields = [
            'id',
            'title',
            'slug',
            'primary_artist',
            'release_date',
            'cover',
            'album_type',
        ]


class TrackSerializer(serializers.ModelSerializer):
    album = serializers.StringRelatedField()
    primary_artist = serializers.StringRelatedField()
    artists = serializers.StringRelatedField(many=True)
    genres = serializers.StringRelatedField(many=True)

    class Meta:
        model = Track
        fields = [
            'id',
            'title',
            'slug',
            'album',
            'primary_artist',
            'artists',
            'genres',
            'track_number',
            'duration_ms',
            'is_explicit',
            'popularity',
        ]
