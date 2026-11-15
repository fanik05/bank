from django.shortcuts import get_object_or_404
from rest_framework import generics

from .models import Account
from .serializers import AccountSerializer, TransactionSerializer


class AccountListView(generics.ListAPIView):
    serializer_class = AccountSerializer

    def get_queryset(self):
        return Account.objects.filter(owner=self.request.user)


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
