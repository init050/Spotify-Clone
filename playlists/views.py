from django.db import models, transaction
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .models import Playlist, PlaylistTrack, PlaylistCollaborator, UserLibrary, LibraryItem
from artists.models import Track
from .serializers import (
    PlaylistSerializer,
    PlaylistDetailSerializer,
    PlaylistWriteSerializer,
    PlaylistTrackSerializer,
    CollaboratorSerializer,
    CollaboratorWriteSerializer,
    ReorderSerializer,
    LibrarySerializer,
)
from .permissions import IsPlaylistOwner, IsPlaylistEditorOrOwner, IsPlaylistViewer


class PlaylistViewSet(viewsets.ModelViewSet):
    queryset = Playlist.objects.all()
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PlaylistDetailSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return PlaylistWriteSerializer
        return PlaylistSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsPlaylistOwner]
        # Custom actions permissions are set within the action decorator if needed
        # or handled by check_object_permissions
        elif self.action == 'retrieve':
            self.permission_classes = [IsAuthenticated, IsPlaylistViewer]
        elif self.action == 'list':
            self.permission_classes = [] # Publicly listable, filtered in queryset
        else:
            # For create, user must be authenticated
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        qs = super().get_queryset()

        # Handle the 'list' action with its specific logic first.
        if self.action == 'list':
            if self.request.user.is_authenticated:
                return qs.filter(
                    models.Q(is_public=True) | models.Q(owner=self.request.user)
                ).distinct().select_related('owner')
            return qs.filter(is_public=True).select_related('owner')

        # For all other actions, apply stricter, more secure filtering.
        if not self.request.user.is_authenticated:
            # Unauthenticated users cannot perform detail actions.
            return qs.none()

        # Authenticated users can only act on playlists they own or collaborate on.
        # The IsPlaylistViewer permission will handle public playlists for 'retrieve'.
        collaborator_playlists = PlaylistCollaborator.objects.filter(
            user=self.request.user
        ).values_list('playlist__pk', flat=True)

        secure_qs = qs.filter(
            models.Q(owner=self.request.user) | models.Q(pk__in=list(collaborator_playlists))
        ).distinct()

        # For retrieve, we can union the secure queryset with public playlists.
        # The permission class provides the final check.
        if self.action == 'retrieve':
            public_qs = Playlist.objects.filter(is_public=True)
            final_qs = (secure_qs | public_qs).distinct()
            return final_qs.select_related('owner').prefetch_related(
                'tracks__track__primary_artist',
                'tracks__added_by',
                'collaborators__user'
            )

        return secure_qs

    @action(detail=True, methods=['post'], url_path='tracks')
    def add_track(self, request, slug=None):
        playlist = self.get_object()

        permission = IsPlaylistEditorOrOwner()
        if not permission.has_object_permission(request, self, playlist):
            self.permission_denied(request)

        track_slug = request.data.get('track_slug')
        if not track_slug:
            return Response({'detail': 'track_slug is required.'}, status=status.HTTP_400_BAD_REQUEST)

        track = get_object_or_404(Track, slug=track_slug)

        try:
            with transaction.atomic():
                last_position = playlist.tracks.aggregate(models.Max('position'))['position__max'] or 0
                new_position = last_position + 1000

                pt = PlaylistTrack.objects.create(
                    playlist=playlist,
                    track=track,
                    added_by=request.user,
                    position=new_position
                )
        except Exception as e:
             # Catches the validation error from the model's save method
            return Response({'detail': str(e)}, status=status.HTTP_409_CONFLICT)

        serializer = PlaylistTrackSerializer(pt)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path='tracks/(?P<pt_id>[^/.]+)')
    def remove_track(self, request, slug=None, pt_id=None):
        playlist = self.get_object()

        # Manual permission check for debugging
        permission = IsPlaylistEditorOrOwner()
        if not permission.has_object_permission(request, self, playlist):
            self.permission_denied(request)

        track_instance = get_object_or_404(PlaylistTrack, id=pt_id, playlist=playlist)
        track_instance.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'], url_path='save', permission_classes=[IsAuthenticated])
    def save(self, request, slug=None):
        playlist = self.get_object()
        library, _ = UserLibrary.objects.get_or_create(user=request.user)

        if request.method == 'POST':
            _, created = LibraryItem.objects.get_or_create(library=library, playlist=playlist)
            if not created:
                return Response({'detail': 'Playlist already saved to library.'}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'detail': 'Playlist saved to library.'}, status=status.HTTP_200_OK)

        elif request.method == 'DELETE':
            item = get_object_or_404(LibraryItem, library=library, playlist=playlist)
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class ReorderView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, slug=None):
        playlist = get_object_or_404(Playlist, slug=slug)

        # Manual permission check
        permission = IsPlaylistEditorOrOwner()
        if not permission.has_object_permission(request, self, playlist):
            self.permission_denied(request, message='You do not have permission to reorder this playlist.')

        serializer = ReorderSerializer(data=request.data, context={'view': self})
        serializer.is_valid(raise_exception=True)

        if playlist.version != serializer.validated_data['version']:
            return Response({
                'detail': 'Playlist version mismatch.',
                'current_version': playlist.version
            }, status=status.HTTP_409_CONFLICT)

        with transaction.atomic():
            playlist.version = models.F('version') + 1
            playlist.save(update_fields=['version'])

            moves = serializer.validated_data['moves']
            for move in moves:
                PlaylistTrack.objects.filter(id=move['pt_id'], playlist=playlist).update(position=move['to_index'] * 1000)

            playlist.refresh_from_db()

        return Response({'detail': 'Playlist reordered successfully.', 'new_version': playlist.version}, status=status.HTTP_200_OK)


class CollaboratorViewSet(viewsets.ModelViewSet):
    serializer_class = CollaboratorSerializer
    permission_classes = [IsAuthenticated]

    def get_playlist(self):
        return get_object_or_404(Playlist, slug=self.kwargs['playlist_slug'])

    def check_permissions(self, request):
        super().check_permissions(request)
        playlist = self.get_playlist()
        permission = IsPlaylistOwner()
        if not permission.has_object_permission(request, self, playlist):
            self.permission_denied(request, message='You do not have permission to manage collaborators.')

    def get_queryset(self):
        return PlaylistCollaborator.objects.filter(playlist__slug=self.kwargs['playlist_slug'])

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CollaboratorWriteSerializer
        return CollaboratorSerializer

    def perform_create(self, serializer):
        playlist = self.get_playlist()
        serializer.save(playlist=playlist)


class LibraryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LibrarySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserLibrary.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        instance, _ = UserLibrary.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
