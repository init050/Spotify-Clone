from django.test import TestCase
from unittest.mock import patch, MagicMock
from .factories import PlaylistFactory, PlaylistTrackFactory
from artists.tests.factories import TrackFactory, AlbumFactory
from playlists.tasks import rebalance_positions, generate_playlist_collage
from django.core.files.base import ContentFile

class PlaylistTasksTest(TestCase):
    def test_rebalance_positions_task(self):
        """
        Test that the rebalance_positions task correctly re-spaces track positions.
        """
        playlist = PlaylistFactory()
        # Create tracks with messy positions
        PlaylistTrackFactory(playlist=playlist, position=1)
        PlaylistTrackFactory(playlist=playlist, position=2)
        PlaylistTrackFactory(playlist=playlist, position=5)

        # Run the task
        rebalance_positions(playlist.id)

        # Check the new positions
        positions = list(playlist.tracks.order_by('position').values_list('position', flat=True))
        self.assertEqual(positions, [1000, 2000, 3000])

    @patch('playlists.tasks.requests.get')
    def test_generate_playlist_collage_task(self, mock_requests_get):
        """
        Test the collage generation task.
        """
        # Mock the response from requests.get
        mock_response = MagicMock()
        mock_response.status_code = 200
        # A simple 1x1 black pixel JPEG
        mock_response.content = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x03\x02\x02\x02\x02\x02\x03\x02\x02\x02\x03\x03\x03\x03\x04\x06\x04\x04\x04\x04\x04\x08\x06\x06\x05\x06\t\x08\n\n\t\x08\t\t\n\x0c\x0f\x0c\n\x0b\x0e\x0b\t\t\r\x11\r\x0e\x0f\x10\x10\x11\x10\n\x0c\x12\x13\x12\x10\x13\x0f\x10\x10\x10\xff\xc9\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xcc\x00\x06\x00\x10\x10\x05\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xd2\xcf \xff\xd9'
        mock_requests_get.return_value = mock_response

        playlist = PlaylistFactory()
        # Create 4 tracks with album covers
        for _ in range(4):
            album = AlbumFactory(cover=ContentFile(b'fake_image_content', name='cover.jpg'))
            track = TrackFactory(album=album)
            PlaylistTrackFactory(playlist=playlist, track=track)

        self.assertFalse(playlist.cover_image)

        # Run the task
        generate_playlist_collage(playlist.id)

        playlist.refresh_from_db()
        self.assertTrue(playlist.cover_image)
        self.assertTrue(playlist.cover_image.name.endswith('_collage.jpg'))

    def test_collage_generation_no_covers(self):
        """
        Test that collage generation handles playlists with no track covers.
        """
        playlist = PlaylistFactory()
        for _ in range(4):
            album = AlbumFactory(cover=None) # No cover
            track = TrackFactory(album=album)
            PlaylistTrackFactory(playlist=playlist, track=track)

        generate_playlist_collage(playlist.id)

        playlist.refresh_from_db()
        self.assertFalse(playlist.cover_image)
