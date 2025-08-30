from django.db.utils import IntegrityError
from django.test import TestCase

from .factories import ArtistFactory, ArtistFollowerFactory, UserFactory


class ArtistFollowerSignalTest(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.artist = ArtistFactory()

    def test_follower_count_increments_on_follow(self):
        initial_count = self.artist.followers_count
        self.assertEqual(initial_count, 0)

        ArtistFollowerFactory(user=self.user, artist=self.artist)
        self.artist.refresh_from_db()

        self.assertEqual(self.artist.followers_count, initial_count + 1)

    def test_follower_count_decrements_on_unfollow(self):
        follow = ArtistFollowerFactory(user=self.user, artist=self.artist)
        self.artist.refresh_from_db()
        initial_count = self.artist.followers_count
        self.assertEqual(initial_count, 1)

        follow.delete()
        self.artist.refresh_from_db()

        self.assertEqual(self.artist.followers_count, initial_count - 1)

    def test_unique_follow_constraint(self):
        """
        Tests that a user cannot follow the same artist more than once.
        """
        ArtistFollowerFactory(user=self.user, artist=self.artist)
        with self.assertRaises(IntegrityError):
            ArtistFollowerFactory(user=self.user, artist=self.artist)
