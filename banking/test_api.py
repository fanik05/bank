from decimal import Decimal

import pytest

from banking.services import deposit


def test_logged_out_user_gets_401(api_client, alice_account):
    response = api_client.get("/api/accounts/")

    assert response.status_code == 401


def test_account_list_shows_only_my_accounts(alice_client, alice_account, bob_account):
    response = alice_client.get("/api/accounts/")

    assert response.status_code == 200
    numbers = [account["account_number"] for account in response.data]
    assert numbers == [alice_account.account_number]


@pytest.mark.parametrize("path", ["", "transactions/"])
def test_cannot_see_other_users_account(alice_client, bob_account, path):
    response = alice_client.get(f"/api/accounts/{bob_account.account_number}/{path}")

    assert response.status_code == 404


def test_customer_cannot_deposit(alice_client, alice_account):
    response = alice_client.post(
        f"/api/accounts/{alice_account.account_number}/deposit/",
        {"amount": "100"},
        format="json",
    )

    assert response.status_code == 403
    alice_account.refresh_from_db()
    assert alice_account.balance == Decimal("0.00")


def test_teller_can_deposit_into_any_account(teller_client, alice_account):
    response = teller_client.post(
        f"/api/accounts/{alice_account.account_number}/deposit/",
        {"amount": "100"},
        format="json",
    )

    assert response.status_code == 201
    assert response.data["balance_after"] == "100.00"


def test_withdraw(alice_client, alice_account):
    deposit(alice_account.pk, "100")

    response = alice_client.post(
        f"/api/accounts/{alice_account.account_number}/withdraw/",
        {"amount": "30"},
        format="json",
    )

    assert response.status_code == 201
    assert response.data["balance_after"] == "70.00"


def test_withdraw_more_than_balance_returns_400(alice_client, alice_account):
    deposit(alice_account.pk, "10")

    response = alice_client.post(
        f"/api/accounts/{alice_account.account_number}/withdraw/",
        {"amount": "50"},
        format="json",
    )

    assert response.status_code == 400
    assert "amount" in response.data


def test_cannot_withdraw_from_other_users_account(alice_client, bob_account):
    deposit(bob_account.pk, "100")

    response = alice_client.post(
        f"/api/accounts/{bob_account.account_number}/withdraw/",
        {"amount": "50"},
        format="json",
    )

    assert response.status_code == 404
    bob_account.refresh_from_db()
    assert bob_account.balance == Decimal("100.00")


@pytest.mark.parametrize("amount", ["0", "-5", "10.555", "abc"])
def test_invalid_amount_returns_400(alice_client, alice_account, amount):
    deposit(alice_account.pk, "100")

    response = alice_client.post(
        f"/api/accounts/{alice_account.account_number}/withdraw/",
        {"amount": amount},
        format="json",
    )

    assert response.status_code == 400


def test_transfer(alice_client, alice_account, bob_account):
    deposit(alice_account.pk, "100")

    response = alice_client.post(
        f"/api/accounts/{alice_account.account_number}/transfer/",
        {"amount": "40", "to_account_number": bob_account.account_number},
        format="json",
    )

    assert response.status_code == 201
    bob_account.refresh_from_db()
    assert bob_account.balance == Decimal("40.00")


def test_transfer_to_unknown_account_returns_400(alice_client, alice_account):
    deposit(alice_account.pk, "100")

    response = alice_client.post(
        f"/api/accounts/{alice_account.account_number}/transfer/",
        {"amount": "40", "to_account_number": "0000000000"},
        format="json",
    )

    assert response.status_code == 400
    assert "to_account_number" in response.data
