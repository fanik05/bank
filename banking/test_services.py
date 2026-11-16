from decimal import Decimal

import pytest
from django.db import IntegrityError

from banking.models import Account, Transaction
from banking.services import InsufficientFunds, deposit, transfer, withdraw


def test_deposit_increases_balance(alice_account):
    deposit(alice_account.pk, "100.00")

    alice_account.refresh_from_db()
    assert alice_account.balance == Decimal("100.00")


def test_deposit_records_transaction(alice_account):
    txn = deposit(alice_account.pk, "50", "Salary")

    assert txn.transaction_type == Transaction.Type.DEPOSIT
    assert txn.amount == Decimal("50.00")
    assert txn.balance_after == Decimal("50.00")
    assert txn.description == "Salary"


@pytest.mark.parametrize("amount", ["0", "-5"])
def test_deposit_rejects_zero_and_negative(alice_account, amount):
    with pytest.raises(ValueError):
        deposit(alice_account.pk, amount)


def test_withdraw_decreases_balance(alice_account):
    deposit(alice_account.pk, "100")
    withdraw(alice_account.pk, "30.50")

    alice_account.refresh_from_db()
    assert alice_account.balance == Decimal("69.50")


def test_cannot_withdraw_more_than_balance(alice_account):
    deposit(alice_account.pk, "30")

    with pytest.raises(InsufficientFunds):
        withdraw(alice_account.pk, "31")

    alice_account.refresh_from_db()
    assert alice_account.balance == Decimal("30.00")
    assert alice_account.transactions.count() == 1


def test_database_refuses_negative_balance(alice_account):
    alice_account.balance = Decimal("-1.00")

    with pytest.raises(IntegrityError):
        alice_account.save()


def test_transfer_moves_money(alice_account, bob_account):
    deposit(alice_account.pk, "100")
    transfer(alice_account.pk, bob_account.pk, "40")

    alice_account.refresh_from_db()
    bob_account.refresh_from_db()
    assert alice_account.balance == Decimal("60.00")
    assert bob_account.balance == Decimal("40.00")


def test_transfer_keeps_total_money_the_same(alice_account, bob_account):
    deposit(alice_account.pk, "100")
    total_before = sum(account.balance for account in Account.objects.all())

    transfer(alice_account.pk, bob_account.pk, "25")

    total_after = sum(account.balance for account in Account.objects.all())
    assert total_after == total_before


def test_transfer_records_both_sides(alice_account, bob_account):
    deposit(alice_account.pk, "100")

    sent = transfer(alice_account.pk, bob_account.pk, "40")

    received = bob_account.transactions.get()
    assert sent.transaction_type == Transaction.Type.TRANSFER_OUT
    assert received.transaction_type == Transaction.Type.TRANSFER_IN
    assert received.amount == Decimal("40.00")


def test_failed_transfer_changes_nothing(alice_account, bob_account):
    deposit(alice_account.pk, "10")

    with pytest.raises(InsufficientFunds):
        transfer(alice_account.pk, bob_account.pk, "50")

    alice_account.refresh_from_db()
    bob_account.refresh_from_db()
    assert alice_account.balance == Decimal("10.00")
    assert bob_account.balance == Decimal("0.00")
    assert bob_account.transactions.count() == 0


def test_cannot_transfer_to_same_account(alice_account):
    deposit(alice_account.pk, "10")

    with pytest.raises(ValueError):
        transfer(alice_account.pk, alice_account.pk, "5")
