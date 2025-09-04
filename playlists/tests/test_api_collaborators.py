from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .factories import PlaylistFactory, UserFactory, PlaylistCollaboratorFactory

class CollaboratorAPITest(APITestCase):
    def setUp(self):
        self.owner = UserFactory()
        self.collaborator_user = UserFactory()
        self.other_user = UserFactory()
        self.playlist = PlaylistFactory(owner=self.owner)
        self.collaborator = PlaylistCollaboratorFactory(
            playlist=self.playlist,
            user=self.collaborator_user,
            role='viewer'
        )
        self.list_url = reverse('playlist-collaborators-list', kwargs={'playlist_slug': self.playlist.slug})
        self.detail_url = reverse('playlist-collaborators-detail', kwargs={'playlist_slug': self.playlist.slug, 'pk': self.collaborator.pk})

    def test_list_collaborators_by_owner(self):
        """
        Ensure the playlist owner can list collaborators.
        """
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['user_id'], str(self.collaborator_user.id))

    def test_add_collaborator_by_owner(self):
        """
        Ensure the playlist owner can add a collaborator.
        """
        self.client.force_authenticate(user=self.owner)
        new_user = UserFactory()
        data = {'user': new_user.email, 'role': 'editor'}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.playlist.collaborators.count(), 2)

    def test_add_collaborator_by_other_user_forbidden(self):
        """
        Ensure non-owners cannot add collaborators.
        """
        self.client.force_authenticate(user=self.other_user)
        new_user = UserFactory()
        data = {'user': new_user.email, 'role': 'editor'}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_collaborator_role_by_owner(self):
        """
        Ensure the playlist owner can change a collaborator's role.
        """
        self.client.force_authenticate(user=self.owner)
        data = {'role': 'editor'}
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.collaborator.refresh_from_db()
        self.assertEqual(self.collaborator.role, 'editor')

    def test_delete_collaborator_by_owner(self):
        """
        Ensure the playlist owner can remove a collaborator.
        """
        self.client.force_authenticate(user=self.owner)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.playlist.collaborators.count(), 0)
