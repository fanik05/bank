import secrets
from decimal import Decimal

from django.conf import settings
from django.db import models


def generate_account_number():
    return ''.join(secrets.choice('0123456789') for _ in range(10))

class Account(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='bank_accounts',
    )
    account_number = models.CharField(
        max_length=10,
        unique=True,
        default=generate_account_number,
        editable=False,
    )
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(balance__gte=0),
                name="balance_not_negative",
            ),
        ]

    def __str__(self):
        return f'{self.account_number} ({self.owner})'

class Transaction(models.Model):
    class Type(models.TextChoices):
        DEPOSIT = 'DEPOSIT', 'Deposit'
        WITHDRAWAL = 'WITHDRAWAL', 'Withdrawal'

    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='transactions',
    )
    transaction_type = models.CharField(max_length=20, choices=Type.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.transaction_type} {self.amount} on {self.account.account_number}'