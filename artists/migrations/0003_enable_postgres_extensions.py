from django.contrib.postgres.operations import CryptoExtension, TrigramExtension, UnaccentExtension
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('artists', '0002_artist_managers'),
    ]

    operations = [
        CryptoExtension(),
        TrigramExtension(),
        UnaccentExtension(),
    ]
