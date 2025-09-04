from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from .models import Notification, PushNotificationDevice
from .serializers import NotificationSerializer, PushNotificationDeviceSerializer
from .tasks import deliver_notification

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = user.user_notifications.all()
        unread = self.request.query_params.get('unread', None)
        if unread is not None:
            queryset = queryset.filter(is_read=False)
        return queryset

class MarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not isinstance(ids, list):
            return Response({'detail': 'IDs must be a list.'}, status=status.HTTP_400_BAD_REQUEST)

        marked_count = Notification.objects.filter(
            user=request.user,
            id__in=ids,
            is_read=False
        ).update(is_read=True)

        return Response({'marked': marked_count}, status=status.HTTP_200_OK)

class PushNotificationDeviceView(generics.CreateAPIView):
    serializer_class = PushNotificationDeviceSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class CreateNotificationView(generics.CreateAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAdminUser] # Internal service or staff only

class SendPushView(APIView):
    permission_classes = [IsAdminUser] # Internal service or staff only

    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        title = request.data.get('title')
        body = request.data.get('body')
        data = request.data.get('data', {})

        if not all([user_id, title, body]):
            return Response({'detail': 'user_id, title, and body are required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Create the notification first
        try:
            notification = Notification.objects.create(
                user_id=user_id,
                type='system', # Or some other type
                payload={'title': title, 'body': body, 'data': data}
            )
            # Enqueue the task
            deliver_notification.delay(notification.id)
            return Response(status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
