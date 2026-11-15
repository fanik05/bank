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
