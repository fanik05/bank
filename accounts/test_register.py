from accounts.models import User

REGISTER_URL = "/api/auth/register/"
ME_URL = "/api/auth/me/"


def test_register_creates_user(api_client, db):
    response = api_client.post(
        REGISTER_URL,
        {
            "username": "carol",
            "password": "a-long-Secret-77",
            "email": "carol@example.com",
        },
        format="json",
    )

    assert response.status_code == 201
    user = User.objects.get(username="carol")
    assert user.check_password("a-long-Secret-77")
    assert not user.is_staff


def test_register_never_returns_password(api_client, db):
    response = api_client.post(
        REGISTER_URL,
        {"username": "carol", "password": "a-long-Secret-77"},
        format="json",
    )

    assert "password" not in response.data


def test_register_rejects_weak_password(api_client, db):
    response = api_client.post(
        REGISTER_URL, {"username": "carol", "password": "12345"}, format="json"
    )

    assert response.status_code == 400
    assert "password" in response.data
    assert not User.objects.filter(username="carol").exists()


def test_register_rejects_taken_username(api_client, alice):
    response = api_client.post(
        REGISTER_URL,
        {"username": "alice", "password": "a-long-Secret-77"},
        format="json",
    )

    assert response.status_code == 400
    assert "username" in response.data


def test_register_cannot_make_yourself_staff(api_client, db):
    api_client.post(
        REGISTER_URL,
        {"username": "mallory", "password": "a-long-Secret-77", "is_staff": True},
        format="json",
    )

    assert not User.objects.get(username="mallory").is_staff


def test_me_returns_current_user(alice_client, alice):
    response = alice_client.get(ME_URL)

    assert response.status_code == 200
    assert response.data["username"] == "alice"


def test_me_requires_login(api_client):
    response = api_client.get(ME_URL)

    assert response.status_code == 401
