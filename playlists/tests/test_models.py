from django.test import TestCase
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from .factories import (
    PlaylistFactory,
    PlaylistTrackFactory,
    UserFactory,
    TrackFactory,
    PlaylistCollaboratorFactory,
    LibraryItemFactory,
    UserLibraryFactory,
)

class PlaylistModelTest(TestCase):
    def test_playlist_creation(self):
        playlist = PlaylistFactory(title='My Test Playlist')
        self.assertEqual(str(playlist), 'My Test Playlist')
        self.assertIsNotNone(playlist.slug)
        self.assertFalse(playlist.is_public)
        self.assertEqual(playlist.version, 1)

class PlaylistTrackModelTest(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.track = TrackFactory()
        self.playlist_no_duplicates = PlaylistFactory(owner=self.user, allow_duplicates=False)
        self.playlist_allow_duplicates = PlaylistFactory(owner=self.user, allow_duplicates=True)

    def test_allow_duplicates(self):
        """
        Test that duplicates are allowed when the flag is True.
        """
        PlaylistTrackFactory(playlist=self.playlist_allow_duplicates, track=self.track)
        try:
            PlaylistTrackFactory(playlist=self.playlist_allow_duplicates, track=self.track)
        except ValidationError:
            self.fail("ValidationError was raised unexpectedly when duplicates are allowed.")
        self.assertEqual(self.playlist_allow_duplicates.tracks.count(), 2)

    def test_disallow_duplicates(self):
        """
        Test that a ValidationError is raised when adding a duplicate track
        to a playlist that disallows them.
        """
        PlaylistTrackFactory(playlist=self.playlist_no_duplicates, track=self.track)
        with self.assertRaises(ValidationError):
            # This should fail because the model's save method raises ValidationError
            PlaylistTrackFactory(playlist=self.playlist_no_duplicates, track=self.track)
        self.assertEqual(self.playlist_no_duplicates.tracks.count(), 1)

class PlaylistCollaboratorModelTest(TestCase):
    def test_unique_collaborator(self):
        """
        Test that a user can only be a collaborator on a playlist once.
        """
        user = UserFactory()
        playlist = PlaylistFactory()
        PlaylistCollaboratorFactory(user=user, playlist=playlist)
        with self.assertRaises(IntegrityError):
            PlaylistCollaboratorFactory(user=user, playlist=playlist)

class LibraryItemModelTest(TestCase):
    def test_unique_playlist_in_library(self):
        """
        Test that a playlist can only be saved to a user's library once.
        """
        library = UserLibraryFactory()
        playlist = PlaylistFactory()
        LibraryItemFactory(library=library, playlist=playlist)
        with self.assertRaises(IntegrityError):
            LibraryItemFactory(library=library, playlist=playlist)
