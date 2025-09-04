from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from datetime import timedelta
from django.utils import timezone

from .models import UserAnalytics, ContentAnalytics
from .serializers import UserAnalyticsSerializer, ContentAnalyticsSerializer, PlayEventSerializer
from .tasks import ingest_play_event

class IngestPlayEventView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = PlayEventSerializer(data=request.data)
        if serializer.is_valid():
            ingest_play_event.delay(serializer.validated_data)
            return Response(status=status.HTTP_202_ACCEPTED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserAnalyticsView(generics.ListAPIView):
    serializer_class = UserAnalyticsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        if str(self.request.user.id) != str(user_id) and not self.request.user.is_staff:
            return UserAnalytics.objects.none()

        start_date = self.request.query_params.get('from', None)
        end_date = self.request.query_params.get('to', None)
        queryset = UserAnalytics.objects.filter(user_id=user_id)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        return queryset

class ContentAnalyticsView(generics.ListAPIView):
    serializer_class = ContentAnalyticsSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        track_id = self.kwargs['track_id']
        window = self.request.query_params.get('window', '7d')

        days = 7
        if window == '30d':
            days = 30
        elif window == '1d':
            days = 1

        start_date = timezone.now().date() - timedelta(days=days)

        queryset = ContentAnalytics.objects.filter(
            track_id=track_id,
            date__gte=start_date
        ).order_by('date')
        return queryset
