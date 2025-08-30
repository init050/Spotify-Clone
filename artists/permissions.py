from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import Artist


class IsStaffOrArtistManager(BasePermission):
    '''
    Custom permission to only allow staff or users in the 'artist_manager' group.
    '''
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_staff:
            return True

        # Check if the user is in the 'artist_manager' group.
        # This assumes a Group named 'artist_manager' exists.
        return request.user.groups.filter(name='artist_manager').exists()


class IsAdminUserOrReadOnly(BasePermission):
    """
    Allows read-only access for anyone, but write access only to staff users.
    """
    def has_permission(self, request, view):
        return bool(
            request.method in SAFE_METHODS or
            request.user and request.user.is_staff
        )


class IsArtistOwnerOrStaff(BasePermission):
    '''
    Object-level permission to only allow staff or the artist's manager to edit.
    '''

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        if request.user.is_staff:
            return True

        # Determine the artist to check against
        artist_to_check = None
        if isinstance(obj, Artist):
            artist_to_check = obj
        elif hasattr(obj, 'primary_artist'): # For Album, Track
            artist_to_check = obj.primary_artist

        if not artist_to_check:
            return False

        # Check if the user is one of the artist's managers
        return artist_to_check.managers.filter(pk=request.user.pk).exists()
