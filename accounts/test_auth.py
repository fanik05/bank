LOGIN_URL = "/api/auth/token/"
REFRESH_URL = "/api/auth/token/refresh/"
LOGOUT_URL = "/api/auth/logout/"


def login(client, username, password):
    return client.post(
        LOGIN_URL, {"username": username, "password": password}, format="json"
    )


def test_login_returns_access_and_refresh_tokens(api_client, alice):
    response = login(api_client, "alice", "alice-pass-123")

    assert response.status_code == 200
    assert "access" in response.data
    assert "refresh" in response.data


def test_wrong_password_returns_401(api_client, alice):
    response = login(api_client, "alice", "wrong-password")

    assert response.status_code == 401


def test_access_token_lets_you_use_the_api(api_client, alice, alice_account):
    tokens = login(api_client, "alice", "alice-pass-123").data
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

    response = api_client.get("/api/accounts/")

    assert response.status_code == 200
    assert response.data[0]["account_number"] == alice_account.account_number


def test_refresh_gives_new_tokens_and_blacklists_old_one(api_client, alice):
    old_refresh = login(api_client, "alice", "alice-pass-123").data["refresh"]

    response = api_client.post(REFRESH_URL, {"refresh": old_refresh}, format="json")

    assert response.status_code == 200
    assert response.data["refresh"] != old_refresh

    reused = api_client.post(REFRESH_URL, {"refresh": old_refresh}, format="json")
    assert reused.status_code == 401


def test_logout_blacklists_refresh_token(api_client, alice):
    refresh = login(api_client, "alice", "alice-pass-123").data["refresh"]

    response = api_client.post(LOGOUT_URL, {"refresh": refresh}, format="json")

    assert response.status_code == 200
    after = api_client.post(REFRESH_URL, {"refresh": refresh}, format="json")
    assert after.status_code == 401
