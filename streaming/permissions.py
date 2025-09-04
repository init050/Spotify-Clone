from rest_framework.permissions import BasePermission, SAFE_METHODS
from artists.models import Track


class IsStaffOrArtistManager(BasePermission):
    '''
    Allows access only to staff users or managers of the artist associated with the track.
    Assumes the view has a 'slug' or 'track_slug' kwarg in the URL.
    '''
    message = 'You do not have permission to perform this action for this artist.'

    def has_permission(self, request, view):
        # Allow any user to make safe requests (GET, HEAD, OPTIONS).
        if request.method in SAFE_METHODS:
            return True

        # For write requests, user must be authenticated.
        if not request.user or not request.user.is_authenticated:
            return False

        # Staff users have full access.
        if request.user.is_staff:
            return True

        # Get the track slug from the URL kwargs.
        track_slug = view.kwargs.get('slug') or view.kwargs.get('track_slug')
        if not track_slug:
            # If we can't identify the track, deny permission for safety.
            return False

        try:
            # Fetch the track and its related artists' managers.
            track = Track.objects.select_related('primary_artist').prefetch_related('artists__managers').get(slug=track_slug)

            # Check if the user manages the primary artist.
            if track.primary_artist.managers.filter(id=request.user.id).exists():
                return True

            # Check if the user manages any of the other featured artists.
            for artist in track.artists.all():
                if artist.managers.filter(id=request.user.id).exists():
                    return True

        except Track.DoesNotExist:
            # If the track doesn't exist, deny access.
            return False

        # If none of the above conditions are met, deny access.
        return False


class IsOwnerOfSession(BasePermission):
    '''
    Object-level permission to only allow the owner of a streaming session to modify it.
    '''
    message = 'You can only modify your own streaming sessions.'

    def has_object_permission(self, request, view, obj):
        # The session must belong to the user making the request.
        return obj.user == request.user
