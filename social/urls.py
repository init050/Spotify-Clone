from django.urls import path
from . import views

app_name = 'social'

urlpatterns = [
    path('follow/', views.FollowView.as_view(), name='follow'),
    path('unfollow/', views.UnfollowView.as_view(), name='unfollow'),
]
