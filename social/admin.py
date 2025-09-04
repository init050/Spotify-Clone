from django.contrib import admin
from .models import (
    UserFollowing,
    ActivityFeedItem,
    ShareableContent,
    SocialInteraction,
    Comment,
    Notification,
)


@admin.register(UserFollowing)
class UserFollowingAdmin(admin.ModelAdmin):
    '''Admin view for UserFollowing.'''
    list_display = ('id', 'follower', 'followee_user', 'followee_artist', 'created_at')
    search_fields = ('follower__email', 'followee_user__email', 'followee_artist__name')
    list_filter = ('created_at',)
    autocomplete_fields = ['follower', 'followee_user', 'followee_artist']
    list_per_page = 50


@admin.register(ActivityFeedItem)
class ActivityFeedItemAdmin(admin.ModelAdmin):
    '''Admin view for ActivityFeedItem.'''
    list_display = ('id', 'actor', 'verb', 'object_type', 'object_id', 'created_at')
    search_fields = ('actor__email', 'verb')
    list_filter = ('verb', 'object_type', 'created_at', 'is_public')
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_per_page = 50


@admin.register(ShareableContent)
class ShareableContentAdmin(admin.ModelAdmin):
    '''Admin view for ShareableContent.'''
    list_display = ('id', 'owner', 'content_type', 'content_id', 'share_token', 'created_at', 'expires_at')
    search_fields = ('owner__email', 'share_token')
    list_filter = ('content_type', 'is_unlisted', 'created_at')
    readonly_fields = ('id', 'share_token', 'created_at', 'updated_at')
    list_per_page = 50


@admin.register(SocialInteraction)
class SocialInteractionAdmin(admin.ModelAdmin):
    '''Admin view for SocialInteraction.'''
    list_display = ('id', 'user', 'interaction_type', 'object_type', 'object_id', 'created_at')
    search_fields = ('user__email', 'object_id')
    list_filter = ('interaction_type', 'object_type', 'created_at')
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_per_page = 50


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    '''Admin view for Comment.'''
    list_display = ('id', 'author', 'object_type', 'object_id', 'parent', 'created_at', 'deleted')
    search_fields = ('author__email', 'body')
    list_filter = ('object_type', 'created_at', 'deleted')
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ['author', 'parent']
    list_per_page = 50


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    '''Admin view for Notification.'''
    list_display = ('id', 'user', 'type', 'actor_id', 'object_type', 'object_id', 'is_read', 'delivered', 'created_at')
    search_fields = ('user__email', 'type')
    list_filter = ('type', 'is_read', 'delivered', 'created_at')
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ['user']
    list_per_page = 50
