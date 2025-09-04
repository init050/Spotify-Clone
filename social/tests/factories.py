import factory
from factory.django import DjangoModelFactory

from artists.tests.factories import UserFactory, ArtistFactory
from social.models import UserFollowing, SocialInteraction


class UserFollowingFactory(DjangoModelFactory):
    class Meta:
        model = UserFollowing

    follower = factory.SubFactory(UserFactory)
    # By default, this factory creates a user-to-user follow.
    # To create a user-to-artist follow, pass 'followee_artist' and set 'followee_user=None'.
    followee_user = factory.SubFactory(UserFactory)
    followee_artist = None


class SocialInteractionFactory(DjangoModelFactory):
    class Meta:
        model = SocialInteraction

    user = factory.SubFactory(UserFactory)
    interaction_type = 'like'
    object_type = 'track'
    # object_id should be passed in during test setup, e.g., object_id=track.id
    object_id = factory.Faker('uuid4')
