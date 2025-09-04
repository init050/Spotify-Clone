import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model
from django.utils.text import slugify
import uuid

from artists.models import Album, Artist, Genre, Track

User = get_user_model()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ('email',)

    email = factory.Faker('email')
    password = factory.PostGenerationMethodCall('set_password', 'defaultpassword')


class GenreFactory(DjangoModelFactory):
    class Meta:
        model = Genre

    name = factory.Faker('music_genre')
    slug = factory.LazyAttribute(lambda o: slugify(f'{o.name}-{uuid.uuid4().hex[:8]}'))


class ArtistFactory(DjangoModelFactory):
    class Meta:
        model = Artist

    name = factory.Faker('name')
    slug = factory.LazyAttribute(lambda o: slugify(f'{o.name}-{uuid.uuid4().hex[:8]}'))


class AlbumFactory(DjangoModelFactory):
    class Meta:
        model = Album

    title = factory.Faker('catch_phrase')
    slug = factory.LazyAttribute(lambda o: slugify(f'{o.title}-{uuid.uuid4().hex[:8]}'))
    primary_artist = factory.SubFactory(ArtistFactory)
    album_type = 'album'


class TrackFactory(DjangoModelFactory):
    class Meta:
        model = Track

    title = factory.Faker('sentence', nb_words=3)
    slug = factory.LazyAttribute(lambda o: slugify(f'{o.title}-{uuid.uuid4().hex[:8]}'))
    album = factory.SubFactory(AlbumFactory)
    primary_artist = factory.SelfAttribute('album.primary_artist')
    track_number = factory.Sequence(lambda n: n + 1)
    duration_ms = 200000
    audio_original = factory.django.FileField(filename='test.mp3')
