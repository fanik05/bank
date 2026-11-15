from decimal import Decimal

from rest_framework import serializers

from .models import Account, Transaction


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ("account_number", "balance", "created_at")
        read_only_fields = fields


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = (
            "id",
            "transaction_type",
            "amount",
            "balance_after",
            "description",
            "created_at",
        )
        read_only_fields = fields


class AmountSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )
    description = serializers.CharField(max_length=255, default="", allow_blank=True)


class TransferSerializer(AmountSerializer):
    to_account_number = serializers.CharField(max_length=10)
