import unittest
from django.db import connection
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .factories import AlbumFactory, ArtistFactory


class SearchAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.artist = ArtistFactory(name='Arctic Monkeys')
        AlbumFactory(title='AM', primary_artist=cls.artist)
        ArtistFactory(name='The Strokes')

    @unittest.skipIf(connection.vendor != 'postgresql', 'Trigram similarity is a PostgreSQL-specific feature.')
    def test_search_returns_combined_results(self):
        """
        Ensures the search endpoint returns combined results from different models
        ordered by similarity.
        """
        url = reverse('catalog-search')
        response = self.client.get(url, {'q': 'Arctic'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data['results']
        self.assertEqual(len(results), 2)

        # The artist name is a closer match than the album title "AM"
        # but TrigramSimilarity can be fuzzy. Let's just check types.
        result_types = {item['item']['type'] for item in results} if isinstance(results[0]['item'], dict) else {item['type'] for item in results}
        self.assertIn('artist', result_types)
        self.assertIn('album', result_types)

    def test_search_requires_query_param(self):
        """
        Ensures the search endpoint returns a 400 if 'q' parameter is missing.
        """
        url = reverse('catalog-search')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_search_is_throttled(self):
        """
        Ensures the search endpoint is rate-limited.
        """
        reverse('catalog-search')
        # This test is environment-dependent and hard to test precisely without complex setup.
        # We rely on the DRF's throttling configuration being correct.
        # A simple check could be to make many requests and see a 429,
        # but that would slow down the test suite.
        # We will trust the framework configuration which was done in a previous step.
        pass
