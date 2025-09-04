from django.utils import timezone
from django.db import models
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, views, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import ValidationError

from artists.models import Track
from .models import AudioFile, StreamingSession, PlaybackSettings, AudioQuality
from .permissions import IsStaffOrArtistManager, IsOwnerOfSession
from .serializers import (
    AudioQualitySerializer,
    PlaybackSettingsSerializer,
    StreamingSessionSerializer,
    StreamingSessionUpdateSerializer,
    StreamingSessionCreateSerializer,
)

class PlaybackSettingsView(generics.RetrieveUpdateAPIView):
    'Get and update the authenticated user\'s playback settings.'
    serializer_class = PlaybackSettingsSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        obj, created = PlaybackSettings.objects.get_or_create(user=self.request.user)
        return obj

class StreamingSessionViewSet(
    viewsets.GenericViewSet,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin
):
    'ViewSet for managing streaming sessions (start, update, end, list).'

    def get_queryset(self):
        return StreamingSession.objects.filter(user=self.request.user).select_related('track', 'audio_file')

    def get_serializer_class(self):
        if self.action == 'create':
            return StreamingSessionCreateSerializer
        if self.action in ['partial_update', 'update']:
            return StreamingSessionUpdateSerializer
        return StreamingSessionSerializer

    def get_permissions(self):
        if self.action in ['retrieve', 'partial_update', 'update', 'end']:
            self.permission_classes = [IsAuthenticated, IsOwnerOfSession]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        track = serializer.validated_data.get('track')

        user_agent = self.request.META.get('HTTP_USER_AGENT', '')
        ip_address = self.request.META.get('REMOTE_ADDR', '')
        device_info = serializer.validated_data.get('device_info', {})
        device_info.update({'user_agent': user_agent, 'ip': ip_address})

        try:
            audio_file = AudioFile.objects.get(track=track, status=Track.ProcessingStatus.COMPLETED)
        except AudioFile.DoesNotExist:
            raise ValidationError('No streamable audio file exists for the given track.')

        instance = serializer.save(
            user=self.request.user,
            audio_file=audio_file,
            device_info=device_info
        )

        display_serializer = StreamingSessionSerializer(instance, context=self.get_serializer_context())
        headers = self.get_success_headers(display_serializer.data)
        return Response(display_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=['post'], url_path='end')
    def end(self, request, pk=None):
        session = self.get_object()
        if session.ended_at:
            return Response({'detail': 'Session has already ended.'}, status=status.HTTP_400_BAD_REQUEST)

        session.ended_at = timezone.now()

        duration_listened = (timezone.now() - session.started_at).total_seconds()
        if duration_listened > 30 or session.last_position_ms > 30000:
            Track.objects.filter(pk=session.track.pk).update(popularity=models.F('popularity') + 1)

        session.save()

        serializer = StreamingSessionSerializer(session)
        return Response(serializer.data)

class TrackStreamView(views.APIView):
    'Returns a signed URL for HLS/DASH streaming.'
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        track = get_object_or_404(Track, slug=kwargs.get('slug'))
        audio_file = get_object_or_404(AudioFile, track=track, status=Track.ProcessingStatus.COMPLETED)

        if not audio_file.hls_master:
            return Response({'error': 'HLS stream not available for this track.'}, status=status.HTTP_404_NOT_FOUND)

        url = audio_file.hls_master.url
        return Response({'url': url})

class TrackUploadView(views.APIView):
    'Handles the upload of the original master audio file.'
    permission_classes = [IsStaffOrArtistManager]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        track = get_object_or_404(Track, slug=kwargs.get('slug'))
        # Placeholder for upload logic
        return Response({'status': f'Upload for track {track.slug} would be processed here.'}, status=status.HTTP_202_ACCEPTED)

class TrackTranscodeView(views.APIView):
    'Initiates a Celery task to transcode the audio file for a track.'
    permission_classes = [IsStaffOrArtistManager]

    def post(self, request, *args, **kwargs):
        track = get_object_or_404(Track, slug=kwargs.get('slug'))
        get_object_or_404(AudioFile, track=track)
        # from .tasks import process_audio_file
        # process_audio_file.delay(audio_file.id)
        return Response({'status': 'Transcoding initiated.'})

class AudioQualitiesView(generics.ListAPIView):
    'Lists available audio qualities for a given track.'
    serializer_class = AudioQualitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        track_slug = self.kwargs.get('slug')
        return AudioQuality.objects.filter(audio_file__track__slug=track_slug).order_by('-bitrate_kbps')

class AudioFilePublishView(views.APIView):
    'A view to publish an audio file (e.g., after transcoding and review).'
    permission_classes = [IsStaffOrArtistManager]

    def post(self, request, *args, **kwargs):
        audio_file = get_object_or_404(AudioFile, pk=kwargs.get('id'))
        # Placeholder: In a real scenario, this might change a status field.
        return Response({'status': f'AudioFile {audio_file.id} has been published.'})
