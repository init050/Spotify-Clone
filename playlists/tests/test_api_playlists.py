from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .factories import PlaylistFactory, UserFactory, TrackFactory, PlaylistTrackFactory, PlaylistCollaboratorFactory
from playlists.models import Playlist, LibraryItem, UserLibrary

class PlaylistAPITest(APITestCase):
    def setUp(self):
        self.owner = UserFactory()
        self.editor = UserFactory()
        self.viewer = UserFactory()
        self.other_user = UserFactory()
        self.public_playlist = PlaylistFactory(owner=self.owner, is_public=True)
        self.private_playlist = PlaylistFactory(owner=self.owner, is_public=False)

        PlaylistCollaboratorFactory(playlist=self.private_playlist, user=self.editor, role='editor')
        PlaylistCollaboratorFactory(playlist=self.private_playlist, user=self.viewer, role='viewer')

    def test_list_public_playlists_unauthenticated(self):
        """
        Ensure unauthenticated users can only see public playlists.
        """
        response = self.client.get(reverse('playlist-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['slug'], self.public_playlist.slug)

    def test_create_playlist_authenticated(self):
        """
        Ensure authenticated users can create a playlist.
        """
        self.client.force_authenticate(user=self.owner)
        url = reverse('playlist-list')
        data = {'title': 'My New Playlist', 'description': 'A cool new playlist.'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Playlist.objects.count(), 3)
        self.assertEqual(Playlist.objects.latest('created_at').owner, self.owner)

    def test_retrieve_private_playlist_by_owner(self):
        self.client.force_authenticate(user=self.owner)
        url = reverse('playlist-detail', kwargs={'slug': self.private_playlist.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['slug'], self.private_playlist.slug)

    def test_retrieve_private_playlist_by_collaborator(self):
        self.client.force_authenticate(user=self.editor)
        url = reverse('playlist-detail', kwargs={'slug': self.private_playlist.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['slug'], self.private_playlist.slug)

    def test_retrieve_private_playlist_by_other_user_forbidden(self):
        self.client.force_authenticate(user=self.other_user)
        url = reverse('playlist-detail', kwargs={'slug': self.private_playlist.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_playlist_by_owner(self):
        self.client.force_authenticate(user=self.owner)
        url = reverse('playlist-detail', kwargs={'slug': self.private_playlist.slug})
        data = {'title': 'Updated Title'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.private_playlist.refresh_from_db()
        self.assertEqual(self.private_playlist.title, 'Updated Title')

    def test_update_playlist_by_editor_forbidden(self):
        self.client.force_authenticate(user=self.editor)
        url = reverse('playlist-detail', kwargs={'slug': self.private_playlist.slug})
        data = {'title': 'Updated Title'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_playlist_by_owner(self):
        self.client.force_authenticate(user=self.owner)
        url = reverse('playlist-detail', kwargs={'slug': self.private_playlist.slug})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Playlist.objects.filter(slug=self.private_playlist.slug).exists())

    def test_add_track_by_editor(self):
        self.client.force_authenticate(user=self.editor)
        track = TrackFactory()
        url = f'/api/v1/playlists/playlists/{self.private_playlist.slug}/tracks/'
        data = {'track_slug': track.slug}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.private_playlist.tracks.count(), 1)

    def test_remove_track_by_viewer_forbidden(self):
        self.client.force_authenticate(user=self.viewer)
        pt = PlaylistTrackFactory(playlist=self.private_playlist)
        url = f'/api/v1/playlists/playlists/{self.private_playlist.slug}/tracks/{pt.id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_reorder_version_mismatch(self):
        self.client.force_authenticate(user=self.owner)
        pt1 = PlaylistTrackFactory(playlist=self.private_playlist, position=1000)
        url = f'/api/v1/playlists/playlists/{self.private_playlist.slug}/reorder/'
        data = {
            'version': self.private_playlist.version + 1, # Wrong version
            'moves': [{'pt_id': str(pt1.id), 'to_index': 1}]
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_reorder_success(self):
        self.client.force_authenticate(user=self.owner)
        pt1 = PlaylistTrackFactory(playlist=self.private_playlist, position=1000)
        url = f'/api/v1/playlists/playlists/{self.private_playlist.slug}/reorder/'
        data = {
            'version': self.private_playlist.version, # Correct version
            'moves': [{'pt_id': str(pt1.id), 'to_index': 1}]
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_save_playlist_to_library(self):
        self.client.force_authenticate(user=self.other_user)
        url = f'/api/v1/playlists/playlists/{self.public_playlist.slug}/save/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        library = UserLibrary.objects.get(user=self.other_user)
        self.assertTrue(LibraryItem.objects.filter(library=library, playlist=self.public_playlist).exists())
