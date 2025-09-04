from django.core.management.base import BaseCommand
from django.db import models
from django.contrib.postgres.search import SearchVector
from artists.models import Artist, Album, Track
from playlists.models import Playlist

class Command(BaseCommand):
    help = 'Rebuilds the search index for all searchable models.'

    def handle(self, *args, **options):
        self.stdout.write('Rebuilding search index for Artist...')
        Artist.objects.update(search_vector=SearchVector('name', 'bio', config='pg_catalog.english'))

        self.stdout.write('Rebuilding search index for Album...')
        Album.objects.update(search_vector=SearchVector('title', 'label', config='pg_catalog.english'))

        self.stdout.write('Rebuilding search index for Track...')
        Track.objects.update(search_vector=SearchVector('title', 'isrc', config='pg_catalog.english'))

        self.stdout.write('Rebuilding search index for Playlist...')
        Playlist.objects.update(search_vector=SearchVector('title', 'description', config='pg_catalog.english'))

        self.stdout.write(self.style.SUCCESS('Successfully rebuilt search index.'))
