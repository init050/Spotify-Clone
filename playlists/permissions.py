from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import PlaylistCollaborator

class IsPlaylistOwner(BasePermission):
    """
    Allows access only to the owner of the playlist.
    """
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user

class IsPlaylistEditorOrOwner(BasePermission):
    """
    Allows access to the owner or collaborators with the 'editor' role.
    """
    def has_object_permission(self, request, view, obj):
        if obj.owner == request.user:
            return True
        return PlaylistCollaborator.objects.filter(
            playlist=obj,
            user=request.user,
            role=PlaylistCollaborator.Role.EDITOR
        ).exists()

class IsPlaylistViewer(BasePermission):
    """
    Allows read access if the playlist is public, or if the user is the owner or a collaborator.
    Write access is determined by other permissions.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for public playlists or for collaborators/owners
        if request.method in SAFE_METHODS:
            if obj.is_public:
                return True
            if request.user.is_authenticated:
                if obj.owner == request.user:
                    return True
                return PlaylistCollaborator.objects.filter(
                    playlist=obj,
                    user=request.user
                ).exists()
            return False

        # Write permissions are not handled by this class,
        # they should be handled by IsPlaylistEditorOrOwner or IsPlaylistOwner
        return False
