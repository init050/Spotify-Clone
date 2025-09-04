from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .factories import UserFactory, PlaylistFactory, LibraryItemFactory, UserLibraryFactory
from playlists.models import LibraryItem

class LibraryAPITest(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.playlist1 = PlaylistFactory(is_public=True)
        self.playlist2 = PlaylistFactory(is_public=True)

        # Pre-save one playlist to the user's library
        self.library = UserLibraryFactory(user=self.user)
        LibraryItemFactory(library=self.library, playlist=self.playlist1)

        self.library_list_url = reverse('user-library')
        self.save_url = reverse('playlist-save', kwargs={'slug': self.playlist2.slug})
        self.unsave_url = reverse('playlist-save', kwargs={'slug': self.playlist1.slug})

    def test_list_library_items(self):
        """
        Ensure a user can list the playlists saved in their library.
        """
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.library_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # The serializer is for UserLibrary, which contains the items
        saved_playlists = response.data.get('saved_playlists', [])
        self.assertEqual(len(saved_playlists), 1)
        self.assertEqual(saved_playlists[0]['playlist']['slug'], self.playlist1.slug)

    def test_save_playlist_to_library(self):
        """
        Ensure a user can save a new playlist to their library.
        """
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.save_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(LibraryItem.objects.filter(library__user=self.user, playlist=self.playlist2).exists())

    def test_unsave_playlist_from_library(self):
        """
        Ensure a user can remove (unsave) a playlist from their library.
        """
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.unsave_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(LibraryItem.objects.filter(library__user=self.user, playlist=self.playlist1).exists())

    def test_library_access_unauthenticated(self):
        """
        Ensure unauthenticated users cannot access library endpoints.
        """
        response = self.client.get(self.library_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.post(self.save_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.delete(self.unsave_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
