from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    CustomUser, 
    UserProfile, 
    UserPreferences, 
    UserSubscription, 
    UserSession
)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Custom User Admin with enhanced functionality
    """
    list_display = (
        'email', 
        'display_name_field', 
        'is_active', 
        'is_staff', 
        'is_email_verified',
        'two_factor_status',
        'last_login',
        'date_joined',
        'active_sessions_count'
    )
    list_filter = (
        'is_active', 
        'is_staff', 
        'is_superuser', 
        'is_email_verified',
        'two_factor_enabled',
        'date_joined',
        'last_login'
    )
    search_fields = ('email', 'first_name', 'last_name', 'profile__display_name')
    ordering = ('-date_joined',)
    readonly_fields = (
        'last_login', 
        'date_joined', 
        'last_login_ip',
        'totp_secret',
        'totp_backup_codes',
        'active_sessions_count',
        'user_sessions_link'
    )

    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        (_('Personal info'), {
            'fields': ('first_name', 'last_name')
        }),
        (_('Permissions'), {
            'fields': (
                'is_active', 
                'is_staff', 
                'is_superuser', 
                'groups', 
                'user_permissions'
            ),
        }),
        (_('Email & Verification'), {
            'fields': ('is_email_verified',)
        }),
        (_('Two-Factor Authentication'), {
            'fields': ('two_factor_enabled', 'totp_secret', 'totp_backup_codes'),
            'classes': ('collapse',)
        }),
        (_('Login Information'), {
            'fields': ('last_login', 'last_login_ip', 'date_joined'),
            'classes': ('collapse',)
        }),
        (_('Session Management'), {
            'fields': ('active_sessions_count', 'user_sessions_link'),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )

    def display_name_field(self, obj):
        """Display name from profile"""
        try:
            return obj.profile.display_name or obj.email.split('@')[0]
        except Exception:
            return obj.email.split('@')[0]
    display_name_field.short_description = 'Display Name'

    def two_factor_status(self, obj):
        """Show 2FA status with color coding"""
        if obj.two_factor_enabled:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Enabled</span>'
            )
        else:
            return format_html(
                '<span style="color: red;">✗ Disabled</span>'
            )
    two_factor_status.short_description = '2FA Status'

    def active_sessions_count(self, obj):
        """Count of active sessions"""
        count = obj.sessions.count()
        if count > 0:
            return format_html(
                '<span style="font-weight: bold;">{} sessions</span>', count
            )
        return '0 sessions'
    active_sessions_count.short_description = 'Active Sessions'

    def user_sessions_link(self, obj):
        """Link to user sessions"""
        if obj.pk:
            url = reverse('admin:accounts_usersession_changelist') + f'?user__id__exact={obj.pk}'
            return format_html(
                '<a href="{}" target="_blank">View Sessions →</a>', url
            )
        return '-'
    user_sessions_link.short_description = 'Manage Sessions'

    def get_queryset(self, request):
        """Optimize queries"""
        return super().get_queryset(request).select_related('profile').prefetch_related('sessions')


class UserProfileInline(admin.StackedInline):
    """Inline for User Profile"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ('display_name', 'avatar', 'bio', 'country', 'locale')


class UserPreferencesInline(admin.StackedInline):
    """Inline for User Preferences"""
    model = UserPreferences
    can_delete = False
    verbose_name_plural = 'Preferences'
    fields = (
        'playback_quality', 
        'explicit_content_filter', 
        'language', 
        'notification_settings'
    )


# Add inlines to CustomUserAdmin
CustomUserAdmin.inlines = [UserProfileInline, UserPreferencesInline]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """User Profile Admin"""
    list_display = ('user_email', 'display_name', 'country', 'locale', 'has_avatar')
    list_filter = ('country', 'locale')
    search_fields = ('user__email', 'display_name')
    readonly_fields = ('user',)

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'

    def has_avatar(self, obj):
        if obj.avatar:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    has_avatar.short_description = 'Avatar'


@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    """User Preferences Admin"""
    list_display = (
        'user_email', 
        'playback_quality', 
        'explicit_content_filter', 
        'language'
    )
    list_filter = ('playback_quality', 'explicit_content_filter', 'language')
    search_fields = ('user__email',)
    readonly_fields = ('user',)

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    """User Subscription Admin"""
    list_display = (
        'user_email', 
        'plan_name', 
        'status', 
        'started_at', 
        'expires_at',
        'is_active_subscription'
    )
    list_filter = ('status', 'plan_name', 'started_at')
    search_fields = ('user__email', 'plan_name', 'stripe_customer_id')
    readonly_fields = ('started_at',)
    date_hierarchy = 'started_at'

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'

    def is_active_subscription(self, obj):
        if obj.status == 'ACTIVE':
            return format_html('<span style="color: green; font-weight: bold;">Active</span>')
        elif obj.status == 'CANCELED':
            return format_html('<span style="color: red;">Canceled</span>')
        elif obj.status == 'PAST_DUE':
            return format_html('<span style="color: orange;">Past Due</span>')
        else:
            return format_html('<span style="color: gray;">Inactive</span>')
    is_active_subscription.short_description = 'Status'


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """User Session Admin"""
    list_display = (
        'user_email', 
        'device_name', 
        'ip_address', 
        'last_active', 
        'created_at',
        'session_duration'
    )
    list_filter = ('created_at', 'last_active', 'device_name')
    search_fields = (
        'user__email', 
        'device_name', 
        'ip_address', 
        'user_agent'
    )
    readonly_fields = (
        'user', 
        'id', 
        'refresh_token_jti', 
        'created_at', 
        'session_duration'
    )
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Session Info', {
            'fields': ('user', 'id', 'device_name', 'user_agent')
        }),
        ('Network Info', {
            'fields': ('ip_address',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'last_active', 'session_duration')
        }),
        ('Token Info', {
            'fields': ('refresh_token_jti',),
            'classes': ('collapse',)
        }),
    )

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'

    def session_duration(self, obj):
        """Calculate session duration"""
        if obj.created_at and obj.last_active:
            duration = obj.last_active - obj.created_at
            days = duration.days
            hours, remainder = divmod(duration.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            if days > 0:
                return f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
        return '-'
    session_duration.short_description = 'Duration'

    def get_queryset(self, request):
        """Optimize queries"""
        return super().get_queryset(request).select_related('user')

    actions = ['revoke_sessions']

    def revoke_sessions(self, request, queryset):
        """Bulk action to revoke sessions"""
        count = queryset.count()
        queryset.delete()
        self.message_user(
            request, 
            f'{count} session(s) have been revoked successfully.'
        )
    revoke_sessions.short_description = 'Revoke selected sessions'


# Customize Admin Site
admin.site.site_header = 'Spotify Clone Administration'
admin.site.site_title = 'Spotify Clone Admin'
admin.site.index_title = 'Welcome to Spotify Clone Administration'