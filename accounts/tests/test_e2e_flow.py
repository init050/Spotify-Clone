from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from accounts.models import CustomUser
from artists.models import Artist, Genre, Album, Track

class EndToEndUserFlowTest(APITestCase):

    def setUp(self):
        """Set up the necessary objects for the test."""
        self.genre = Genre.objects.create(name='Test Genre')
        self.artist = Artist.objects.create(name='Test Artist', slug='test-artist')
        self.album = Album.objects.create(
            title='Test Album',
            primary_artist=self.artist,
            release_date='2023-01-01',
            album_type='album',
            slug='test-album'
        )
        self.track = Track.objects.create(
            title='Test Track',
            album=self.album,
            primary_artist=self.artist,
            track_number=1,
            duration_ms=180000,
            slug='test-track'
        )
        self.track.artists.add(self.artist)
        self.track.genres.add(self.genre)

    def test_full_user_journey(self):
        """
        Tests the full user journey from registration to streaming a track.
        """
        # --- 1. User Registration ---
        register_url = reverse('register')
        register_data = {
            'email': 'newuser@example.com',
            'password': 'strongpassword123',
            'password2': 'strongpassword123'
        }
        response = self.client.post(register_url, register_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = CustomUser.objects.get(email='newuser@example.com')
        # In a real scenario, the user is inactive until email verification.
        # We will simulate the verification step.
        self.assertFalse(user.is_active)

        # --- 2. Email Verification (Simulated) ---
        user.is_active = True
        user.save()
        self.assertTrue(CustomUser.objects.get(email='newuser@example.com').is_active)

        # --- 3. User Login ---
        login_url = reverse('login')
        login_data = {'email': 'newuser@example.com', 'password': 'strongpassword123'}
        response = self.client.post(login_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        access_token = response.data['access']

        # --- 4. Search for a Track (Authenticated) ---
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)
        # The search URL is registered in the 'search' app with the name 'search'.
        search_url = reverse('search') + '?q=Test'
        response = self.client.get(search_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.track.title, str(response.content))

        # --- 5. Request Streaming Information ---
        stream_url = reverse('track-stream', kwargs={'slug': self.track.slug})
        response = self.client.get(stream_url)
        # The stream view should return a signed URL, so we expect a 200 OK
        # and some data representing the URL.
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('manifest_url', response.data)
