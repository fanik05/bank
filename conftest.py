import pytest
from rest_framework.test import APIClient

from accounts.models import User
from banking.models import Account


@pytest.fixture
def alice(db):
    return User.objects.create_user(username="alice", password="alice-pass-123")


@pytest.fixture
def bob(db):
    return User.objects.create_user(username="bob", password="bob-pass-123")


@pytest.fixture
def alice_account(alice):
    return Account.objects.create(owner=alice)


@pytest.fixture
def bob_account(bob):
    return Account.objects.create(owner=bob)


@pytest.fixture
def teller(db):
    return User.objects.create_user(
        username="teller", password="teller-pass-123", is_staff=True
    )


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def alice_client(alice):
    client = APIClient()
    client.force_authenticate(user=alice)
    return client


@pytest.fixture
def teller_client(teller):
    client = APIClient()
    client.force_authenticate(user=teller)
    return client
