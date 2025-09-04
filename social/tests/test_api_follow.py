from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

from artists.tests.factories import ArtistFactory, UserFactory
from ..models import UserFollowing

User = get_user_model()


class FollowAPITest(APITestCase):
    def setUp(self):
        self.follower = UserFactory()
        self.followee_user = UserFactory()
        self.followee_artist = ArtistFactory()

        self.client.force_authenticate(user=self.follower)

        self.follow_url = reverse('social:follow')
        self.unfollow_url = reverse('social:unfollow')

    def test_follow_user_success(self):
        data = {'type': 'user', 'id': str(self.followee_user.id)}
        response = self.client.post(self.follow_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(UserFollowing.objects.filter(
            follower=self.follower,
            followee_user=self.followee_user
        ).exists())

        # Check counters
        self.follower.profile.refresh_from_db()
        self.followee_user.profile.refresh_from_db()
        self.assertEqual(self.follower.profile.following_count, 1)
        self.assertEqual(self.followee_user.profile.followers_count, 1)

    def test_follow_artist_success(self):
        data = {'type': 'artist', 'id': str(self.followee_artist.id)}
        response = self.client.post(self.follow_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(UserFollowing.objects.filter(
            follower=self.follower,
            followee_artist=self.followee_artist
        ).exists())

        # Check counters
        self.follower.profile.refresh_from_db()
        self.followee_artist.refresh_from_db()
        self.assertEqual(self.follower.profile.following_count, 1)
        self.assertEqual(self.followee_artist.followers_count, 1)

    def test_follow_self_fail(self):
        data = {'type': 'user', 'id': str(self.follower.id)}
        response = self.client.post(self.follow_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('You cannot follow yourself.', str(response.data['non_field_errors'][0]))

    def test_follow_non_existent_fail(self):
        import uuid
        data = {'type': 'user', 'id': '99999'} # Non-existent user ID
        response = self.client.post(self.follow_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('does not exist', response.data['id'][0])

    def test_follow_idempotency(self):
        # Follow once
        data = {'type': 'user', 'id': str(self.followee_user.id)}
        self.client.post(self.follow_url, data, format='json')

        # Follow again
        response = self.client.post(self.follow_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(UserFollowing.objects.count(), 1)

        self.follower.profile.refresh_from_db()
        self.assertEqual(self.follower.profile.following_count, 1)

    def test_unfollow_user_success(self):
        # First, follow
        UserFollowing.objects.create(follower=self.follower, followee_user=self.followee_user)
        self.follower.profile.following_count = 1
        self.follower.profile.save()
        self.followee_user.profile.followers_count = 1
        self.followee_user.profile.save()

        # Then, unfollow
        data = {'type': 'user', 'id': str(self.followee_user.id)}
        response = self.client.delete(self.unfollow_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(UserFollowing.objects.filter(
            follower=self.follower,
            followee_user=self.followee_user
        ).exists())

        # Check counters
        self.follower.profile.refresh_from_db()
        self.followee_user.profile.refresh_from_db()
        self.assertEqual(self.follower.profile.following_count, 0)
        self.assertEqual(self.followee_user.profile.followers_count, 0)

    def test_unfollow_artist_success(self):
        # First, follow
        UserFollowing.objects.create(follower=self.follower, followee_artist=self.followee_artist)
        self.follower.profile.following_count = 1
        self.follower.profile.save()
        self.followee_artist.followers_count = 1
        self.followee_artist.save()

        # Then, unfollow
        data = {'type': 'artist', 'id': str(self.followee_artist.id)}
        response = self.client.delete(self.unfollow_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(UserFollowing.objects.filter(
            follower=self.follower,
            followee_artist=self.followee_artist
        ).exists())

        # Check counters
        self.follower.profile.refresh_from_db()
        self.followee_artist.refresh_from_db()
        self.assertEqual(self.follower.profile.following_count, 0)
        self.assertEqual(self.followee_artist.followers_count, 0)

    def test_unfollow_not_following_fail(self):
        data = {'type': 'user', 'id': str(self.followee_user.id)}
        response = self.client.delete(self.unfollow_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
