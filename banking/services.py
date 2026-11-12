from decimal import Decimal

from django.db.transaction import atomic

from .models import Account, Transaction


class InsufficientFunds(Exception):
    pass

def _check_amount(amount):
    if amount <= 0:
        raise ValueError('Amount must be greater than zero.')

def deposit(account_id, amount, description=''):
    amount = Decimal(str(amount))
    _check_amount(amount)

    with atomic():
        account = Account.objects.select_for_update().get(pk=account_id)
        account.balance += amount
        account.save(update_fields=['balance'])

        return Transaction.objects.create(
            account=account,
            transaction_type=Transaction.Type.DEPOSIT,
            amount=amount,
            balance_after=account.balance,
            description=description,
        )

def withdraw(account_id, amount, description=''):
    amount = Decimal(str(amount))
    _check_amount(amount)

    with atomic():
        account = Account.objects.select_for_update().get(pk=account_id)

        if account.balance < amount:
            raise InsufficientFunds(
                f'Balance is {account.balance}, cannot withdraw {amount}.'
            )

        account.balance -= amount
        account.save(update_fields=['balance'])

        return Transaction.objects.create(
            account=account,
            transaction_type=Transaction.Type.WITHDRAWAL,
            amount=amount,
            balance_after=account.balance,
            description=description,
        )
    