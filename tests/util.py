from django.test import TestCase
from django.contrib.auth.models import Group, AnonymousUser
from django.conf import settings
import peeringdb_server.models as models
import django_namespace_perms as nsp
from peeringdb_server import settings as pdb_settings


class ClientCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # create user and guest group

        cls.guest_group = Group.objects.create(name="guest", id=settings.GUEST_GROUP_ID)
        cls.user_group = Group.objects.create(name="user", id=settings.USER_GROUP_ID)

        settings.USER_GROUP_ID = cls.user_group.id
        settings.GUEST_GROUP_ID = cls.guest_group.id

        cls.guest_user = models.User.objects.create_user(
            "guest", "guest@localhost", "guest"
        )
        cls.guest_group.user_set.add(cls.guest_user)

        nsp.models.GroupPermission.objects.create(
            group=cls.guest_group, namespace="peeringdb.organization", permissions=0x01
        )

        nsp.models.GroupPermission.objects.create(
            group=cls.user_group, namespace="peeringdb.organization", permissions=0x01
        )

        nsp.models.GroupPermission.objects.create(
            group=cls.user_group,
            namespace="peeringdb.organization.*.network.*.poc_set.users",
            permissions=0x01,
        )

        nsp.models.GroupPermission.objects.create(
            group=cls.guest_group,
            namespace="peeringdb.organization.*.network.*.poc_set.public",
            permissions=0x01,
        )


class SettingsCase(ClientCase):

    """
    Since we read settings from peeringdb_server.settings
    we can't use the `settings` fixture from pytest-django

    This class instead does something similar for peeringdb_server.settings,
    where it will override settings specified and then reset after test case
    is finished
    """

    settings = {}

    @classmethod
    def setUp(cls):
        cls._restore = {}
        for k, v in list(cls.settings.items()):
            cls._restore[k] = getattr(pdb_settings, k, getattr(settings, k, None))
            setattr(pdb_settings, k, v)
            setattr(settings, k, v)

    @classmethod
    def tearDown(cls):
        for k, v in list(cls._restore.items()):
            setattr(pdb_settings, k, v)
            setattr(settings, k, v)


def reset_group_ids():
    """
    Guest and user groups will get recreated for each tests,
    however mysql sequential ids wont be reset between tests.

    Tests that require USER_GROUP_ID and GUEST_GROUP_ID to
    point to to correct groups should call this function
    to make sure the settings are updated
    """

    settings.USER_GROUP_ID = Group.objects.get(name="user").id
    settings.GUEST_GROUP_ID = Group.objects.get(name="guest").id
