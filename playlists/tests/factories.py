import factory
from factory.django import DjangoModelFactory
from django.utils.text import slugify
import uuid

from artists.tests.factories import UserFactory, TrackFactory
from playlists.models import (
    Playlist,
    PlaylistTrack,
    PlaylistCollaborator,
    UserLibrary,
    LibraryItem,
)


class PlaylistFactory(DjangoModelFactory):
    class Meta:
        model = Playlist

    owner = factory.SubFactory(UserFactory)
    title = factory.Faker('catch_phrase')
    slug = factory.LazyAttribute(lambda o: slugify(f'{o.title}-{uuid.uuid4().hex[:8]}'))
    is_public = False


class PlaylistTrackFactory(DjangoModelFactory):
    class Meta:
        model = PlaylistTrack

    playlist = factory.SubFactory(PlaylistFactory)
    track = factory.SubFactory(TrackFactory)
    added_by = factory.SubFactory(UserFactory)
    position = factory.Sequence(lambda n: (n + 1) * 1000)


class PlaylistCollaboratorFactory(DjangoModelFactory):
    class Meta:
        model = PlaylistCollaborator

    playlist = factory.SubFactory(PlaylistFactory)
    user = factory.SubFactory(UserFactory)
    role = PlaylistCollaborator.Role.VIEWER


class UserLibraryFactory(DjangoModelFactory):
    class Meta:
        model = UserLibrary

    user = factory.SubFactory(UserFactory)


class LibraryItemFactory(DjangoModelFactory):
    class Meta:
        model = LibraryItem

    library = factory.SubFactory(UserLibraryFactory)
    playlist = factory.SubFactory(PlaylistFactory)
    is_pinned = False
