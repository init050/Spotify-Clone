from django.urls import path
from .views import (
    NotificationListView,
    MarkReadView,
    PushNotificationDeviceView,
    CreateNotificationView,
    SendPushView
)

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification-list'),
    path('mark-read/', MarkReadView.as_view(), name='notification-mark-read'),
    path('devices/', PushNotificationDeviceView.as_view(), name='notification-device-register'),
    path('create/', CreateNotificationView.as_view(), name='notification-create'),
    path('send-push/', SendPushView.as_view(), name='notification-send-push'),
]
