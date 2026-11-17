from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import Account
from .serializers import (
    AccountSerializer,
    AmountSerializer,
    TransactionSerializer,
    TransferSerializer,
)
from .services import InsufficientFunds, deposit, transfer, withdraw


class AccountListView(generics.ListCreateAPIView):
    serializer_class = AccountSerializer

    def get_queryset(self):
        return Account.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class AccountDetailView(generics.RetrieveAPIView):
    serializer_class = AccountSerializer
    lookup_field = "account_number"

    def get_queryset(self):
        return Account.objects.filter(owner=self.request.user)


class AccountTransactionListView(generics.ListAPIView):
    serializer_class = TransactionSerializer

    def get_queryset(self):
        account = get_object_or_404(
            Account,
            account_number=self.kwargs["account_number"],
            owner=self.request.user,
        )
        return account.transactions.all()


class DepositView(generics.GenericAPIView):
    serializer_class = AmountSerializer
    permission_classes = (permissions.IsAdminUser,)

    def post(self, request, account_number):
        account = get_object_or_404(Account, account_number=account_number)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        txn = deposit(account.pk, data["amount"], data["description"])
        return Response(TransactionSerializer(txn).data, status=status.HTTP_201_CREATED)


class WithdrawView(generics.GenericAPIView):
    serializer_class = AmountSerializer

    def post(self, request, account_number):
        account = get_object_or_404(
            Account, account_number=account_number, owner=request.user
        )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            txn = withdraw(account.pk, data["amount"], data["description"])
        except InsufficientFunds as error:
            raise ValidationError({"amount": str(error)})

        return Response(TransactionSerializer(txn).data, status=status.HTTP_201_CREATED)


class TransferView(generics.GenericAPIView):
    serializer_class = TransferSerializer

    def post(self, request, account_number):
        sender = get_object_or_404(
            Account, account_number=account_number, owner=request.user
        )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        receiver = Account.objects.filter(
            account_number=data["to_account_number"]
        ).first()
        if receiver is None:
            raise ValidationError({"to_account_number": "Account not found."})

        try:
            txn = transfer(sender.pk, receiver.pk, data["amount"], data["description"])
        except InsufficientFunds as error:
            raise ValidationError({"amount": str(error)})
        except ValueError as error:
            raise ValidationError({"to_account_number": str(error)})

        return Response(TransactionSerializer(txn).data, status=status.HTTP_201_CREATED)
