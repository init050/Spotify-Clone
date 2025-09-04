from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    Album,
    Artist,
    Genre,
    Track,
)
import uuid

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.contrib.postgres.search import TrigramSimilarity
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.views import APIView

from .permissions import (
    IsAdminUserOrReadOnly,
    IsArtistOwnerOrStaff,
    IsStaffOrArtistManager,
)
from .serializers import (
    AlbumSerializer,
    AlbumWriteSerializer,
    ArtistDetailSerializer,
    ArtistSerializer,
    ArtistWriteSerializer,
    GenreSerializer,
    SearchResultSerializer,
    TrackSerializer,
    TrackWriteSerializer,
    UploadCompleteSerializer,
    UploadInitSerializer,
)
from .tasks import process_audio_upload


class GenreViewSet(viewsets.ModelViewSet):
    '''
    API endpoint for genres.
    Supports searching by name.
    Initially shows top-level genres, but can be filtered to show all.
    Write operations are restricted to staff users.
    '''
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsAdminUserOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = super().get_queryset()
        # For list view, only return top-level genres unless 'all' is specified
        if self.action == 'list' and self.request.query_params.get('all', 'false').lower() != 'true':
            return queryset.filter(parent__isnull=True)
        return queryset


class ArtistViewSet(viewsets.ModelViewSet):
    '''
    API endpoint for artists.
    Supports filtering by country and verification status,
    searching by name and bio, and ordering.
    '''
    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsArtistOwnerOrStaff]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['country', 'is_verified']
    search_fields = ['name', 'bio']
    ordering_fields = ['name', 'followers_count', 'monthly_listeners']
    ordering = ['name']
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ArtistWriteSerializer
        if self.action == 'retrieve':
            return ArtistDetailSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action == 'retrieve':
            return qs.prefetch_related('tracks', 'albums')
        return qs


class AlbumViewSet(viewsets.ModelViewSet):
    '''
    API endpoint for albums.
    Supports filtering by artist, album type, release date, and genre.
    Supports searching by title and artist name.
    '''
    queryset = Album.objects.select_related('primary_artist').all()
    serializer_class = AlbumSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        - Create action is limited to staff or artist managers.
        - Other write actions (update, delete) are object-level, checked against artist ownership.
        """
        if self.action == 'create':
            self.permission_classes = [IsAuthenticated, IsStaffOrArtistManager]
        else:
            self.permission_classes = [IsAuthenticatedOrReadOnly, IsArtistOwnerOrStaff]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return AlbumWriteSerializer
        return self.serializer_class
    filterset_fields = {
        'primary_artist__slug': ['exact'],
        'album_type': ['exact'],
        'release_date': ['gte', 'lte'],
        'artists__slug': ['in'],
    }
    search_fields = ['title', 'primary_artist__name', 'artists__name']
    ordering_fields = ['release_date', 'title']
    ordering = ['-release_date']
    lookup_field = 'slug'


class TrackViewSet(viewsets.ModelViewSet):
    '''
    API endpoint for tracks.
    Supports filtering by artist, album, genre, explicit content, and duration.
    Supports searching by title, artist name, and album title.
    '''
    queryset = Track.objects.select_related('album', 'primary_artist').prefetch_related('artists', 'genres').all()
    serializer_class = TrackSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [IsAuthenticated, IsStaffOrArtistManager]
        else:
            self.permission_classes = [IsAuthenticatedOrReadOnly, IsArtistOwnerOrStaff]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return TrackWriteSerializer
        return self.serializer_class
    filterset_fields = {
        'primary_artist__slug': ['exact'],
        'album__slug': ['exact'],
        'genres__slug': ['in'],
        'is_explicit': ['exact'],
        'duration_ms': ['gte', 'lte'],
    }
    search_fields = ['title', 'primary_artist__name', 'album__title']
    ordering_fields = ['popularity', 'title', 'duration_ms']
    ordering = ['-popularity']
    lookup_field = 'slug'


class SearchView(APIView, PageNumberPagination):
    '''
    A view for performing a site-wide search across artists, albums, tracks, and genres.
    It uses trigram similarity to find and rank results.
    '''
    throttle_scope = 'search'
    permission_classes = []  # Public search endpoint
    page_size = 10 # Default page size

    def get(self, request, *args, **kwargs):
        query = request.query_params.get('q', None)
        if not query:
            return Response(
                {'detail': 'Query parameter "q" is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # A lower threshold is more inclusive but might return less relevant results.
        similarity_threshold = 0.08

        # Annotate each queryset with a 'similarity' score and filter
        artist_qs = Artist.objects.annotate(
            similarity=TrigramSimilarity('name', query)
        ).filter(similarity__gt=similarity_threshold)

        album_qs = Album.objects.select_related('primary_artist').annotate(
            similarity=TrigramSimilarity('title', query)
        ).filter(similarity__gt=similarity_threshold)

        track_qs = Track.objects.select_related('album', 'primary_artist').annotate(
            similarity=TrigramSimilarity('title', query)
        ).filter(similarity__gt=similarity_threshold)

        genre_qs = Genre.objects.annotate(
            similarity=TrigramSimilarity('name', query)
        ).filter(similarity__gt=similarity_threshold)

        # Package results into a common structure
        results = []
        results.extend([{'type': 'artist', 'score': r.similarity, 'instance': r} for r in artist_qs])
        results.extend([{'type': 'album', 'score': r.similarity, 'instance': r} for r in album_qs])
        results.extend([{'type': 'track', 'score': r.similarity, 'instance': r} for r in track_qs])
        results.extend([{'type': 'genre', 'score': r.similarity, 'instance': r} for r in genre_qs])

        # Sort all results by the similarity score in descending order
        sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)

        # Paginate the sorted results
        paginated_results = self.paginate_queryset(sorted_results, request, view=self)
        serializer = SearchResultSerializer(paginated_results, many=True)
        return self.get_paginated_response(serializer.data)


class UploadInitView(APIView):
    throttle_scope = 'upload'
    permission_classes = [IsAuthenticated, IsStaffOrArtistManager]

    def post(self, request, *args, **kwargs):
        serializer = UploadInitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # TODO: Add validation for file size and type from settings
        # For now, we proceed directly.

        file_name = serializer.validated_data['filename']
        # Use a temporary upload location
        object_name = f'uploads/original/{uuid.uuid4()}/{file_name}'

        s3_client = boto3.client(
            's3',
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            config=boto3.session.Config(signature_version='s3v4')
        )

        try:
            # TODO: Make content length range configurable
            response = s3_client.generate_presigned_post(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=object_name,
                Fields={'Content-Type': serializer.validated_data['mime_type']},
                Conditions=[
                    {'Content-Type': serializer.validated_data['mime_type']},
                    ['content-length-range', 1, 30 * 1024 * 1024]  # 30MB limit
                ],
                ExpiresIn=3600  # 1 hour
            )
            # Add upload_id for tracking
            response['upload_id'] = str(uuid.uuid4())
            response['object_name'] = object_name

        except ClientError:
            return Response({'detail': 'Could not generate pre-signed URL.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(response, status=status.HTTP_200_OK)


class UploadCompleteView(APIView):
    throttle_scope = 'upload'
    permission_classes = [IsAuthenticated, IsStaffOrArtistManager]

    def post(self, request, *args, **kwargs):
        serializer = UploadCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        track_id = serializer.validated_data['track_id']
        object_name = serializer.validated_data['object_name']

        try:
            track = Track.objects.get(pk=track_id)
        except Track.DoesNotExist:
            return Response({'detail': 'Track not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Manually check object-level permissions
        obj_perm = IsArtistOwnerOrStaff()
        if not obj_perm.has_object_permission(request, self, track):
            self.permission_denied(request, message='You do not have permission to modify this track.')

        # Associate the uploaded file with the track object
        track.audio_original.name = object_name
        track.status = Track.ProcessingStatus.PROCESSING
        track.save(update_fields=['audio_original', 'status', 'updated_at'])

        # Launch the background processing task
        process_audio_upload.delay(str(track.id))

        return Response(
            {'detail': 'Upload complete. Processing has started.'},
            status=status.HTTP_202_ACCEPTED
        )


class StreamManifestView(APIView):
    throttle_scope = 'stream'
    permission_classes = [IsAuthenticated]

    def get(self, request, track_slug, *args, **kwargs):
        track = get_object_or_404(Track, slug=track_slug, status=Track.ProcessingStatus.COMPLETED)

        if not track.audio_hls_master or not track.audio_hls_master.name:
            return Response({'detail': 'HLS manifest is not available for this track.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            s3_client = boto3.client(
                's3',
                endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                config=boto3.session.Config(signature_version='s3v4')
            )
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': track.audio_hls_master.name},
                ExpiresIn=3600  # URL is valid for 1 hour
            )
        except ClientError:
            return Response(
                {'detail': 'Could not generate streaming URL.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({'manifest_url': url})
