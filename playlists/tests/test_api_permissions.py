from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from accounts.models import CustomUser
from ..models import Playlist

class PlaylistPermissionTests(APITestCase):
    def setUp(self):
        # Create User A
        self.user_a = CustomUser.objects.create_user(
            email='usera@example.com',
            password='password123'
        )
        # Create User B
        self.user_b = CustomUser.objects.create_user(
            email='userb@example.com',
            password='password123'
        )

        # User A creates a private playlist
        self.private_playlist_a = Playlist.objects.create(
            owner=self.user_a,
            title='User A Private Playlist',
            slug='user-a-private-playlist',
            is_public=False
        )

    def test_user_cannot_access_other_users_private_playlist(self):
        """
        Ensure that a request for another user's private playlist returns
        a 404 Not Found, not a 403 Forbidden. This prevents leaking
        the existence of private playlists.
        """
        # Authenticate as User B
        self.client.force_authenticate(user=self.user_b)

        # User B attempts to retrieve User A's private playlist
        url = reverse('playlist-detail', kwargs={'slug': self.private_playlist_a.slug})
        response = self.client.get(url)

        # The correct behavior is to not even acknowledge the playlist's existence.
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
