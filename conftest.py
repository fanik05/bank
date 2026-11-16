import pytest

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
