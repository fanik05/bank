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

def transfer(from_account_id, to_account_id, amount, description=''):
    amount = Decimal(str(amount))
    _check_amount(amount)

    if from_account_id == to_account_id:
        raise ValueError('Cannot transfer to the same account')

    with atomic():
        locked = {}
        for pk in sorted([from_account_id, to_account_id]):
            locked[pk] = Account.objects.select_for_update().get(pk=pk)

        sender = locked[from_account_id]
        receiver = locked[to_account_id]

        if sender.balance < amount:
            raise InsufficientFunds(
                f'Balance is {sender.balance}, cannot transfer {amount}'
            )

        sender.balance -= amount
        receiver.balance += amount
        sender.save(update_fields=['balance'])
        receiver.save(update_fields=['balance'])

        Transaction.objects.create(
            account=sender,
            transaction_type=Transaction.Type.TRANSFER_OUT,
            amount=amount,
            balance_after=sender.balance,
            description=description or f'Transfer to {receiver.account_number}',
        )
        Transaction.objects.create(
            account=receiver,
            transaction_type=Transaction.Type.TRANSFER_IN,
            amount=amount,
            balance_after=receiver.balance,
            description=description or f'Transfer from {sender.account_number}'
        )
    