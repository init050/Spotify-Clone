from django.core.management.base import BaseCommand
from django.utils.text import slugify
from artists.models import Genre

class Command(BaseCommand):
    help = 'Seeds the database with a list of common music genres.'

    COMMON_GENRES = [
        'Electronic', 'Rock', 'Pop', 'Hip Hop', 'Jazz', 'Blues',
        'Country', 'Classical', 'Reggae', 'Folk', 'Metal', 'R&B',
        'Indie', 'Alternative', 'Punk', 'Funk', 'Soul', 'Dance'
    ]

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding common music genres...')
        count = 0
        for genre_name in self.COMMON_GENRES:
            slug = slugify(genre_name)
            _, created = Genre.objects.get_or_create(
                name=genre_name,
                defaults={'slug': slug}
            )
            if created:
                count += 1
                self.stdout.write(self.style.SUCCESS(f'Successfully created genre: "{genre_name}"'))
        self.stdout.write(f'Finished seeding. {count} new genres created.')
