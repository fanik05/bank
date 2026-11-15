from django.urls import path

from . import views

urlpatterns = [
    path("accounts/", views.AccountListView.as_view()),
    path("accounts/<str:account_number>/", views.AccountDetailView.as_view()),
    path(
        "accounts/<str:account_number>/transactions/",
        views.AccountTransactionListView.as_view(),
    ),
    path("accounts/<str:account_number>/deposit/", views.DepositView.as_view()),
    path("accounts/<str:account_number>/withdraw/", views.WithdrawView.as_view()),
    path("accounts/<str:account_number>/transfer/", views.TransferView.as_view()),
]
