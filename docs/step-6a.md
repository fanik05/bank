# Bank project: working guide

## Where I am

| Step | Status |
|---|---|
| 1. Django project (`config/`) | ✅ |
| 2. `accounts` app + custom User model | ✅ |
| 3. `banking` app + Account model | ✅ |
| 3.5 PostgreSQL in Docker + `.env` | ✅ |
| 4. Deposits, withdrawals, transaction ledger (`banking/services.py`) | ✅ |
| 5. Transfers between accounts | ✅ |
| **6a. API: read-only endpoints** | **⬅ doing now** |
| 6b. API: deposit / withdraw / transfer endpoints | |
| 6c. API: token login + CORS for the frontend | |
| 7. Tests with pytest-django | |

The bank uses a **separate frontend**, so Django only provides a JSON API (Django REST Framework).

---

## Setting up a new computer (one time)

1. Install `git`, `uv` and Docker (with Docker Compose). Python is not needed: uv installs 3.15 by itself.
2. Get the code:
   ```bash
   git clone https://github.com/fanik05/bank.git
   cd bank
   uv sync
   ```
3. Create `.env` (it is not in Git, on purpose):
   ```bash
   cp .env.example .env
   ```
   Fill in new secrets:
   ```bash
   uv run python -c "import secrets; print(secrets.token_urlsafe(50))"   # SECRET_KEY
   uv run python -c "import secrets; print(secrets.token_urlsafe(24))"   # POSTGRES_PASSWORD
   ```
   Set the password **before** the first `docker compose up`. Postgres reads it only once.
4. Fresh database (data does not travel between computers):
   ```bash
   docker compose up -d
   uv run python manage.py migrate
   uv run python manage.py createsuperuser
   ```
   Then create a couple of accounts in `/admin` and put money in with the shell (see "Test data" below).

## Every work session

**Start:**
```bash
git pull
uv sync
docker compose up -d
uv run python manage.py migrate
uv run python manage.py runserver
```

**Finish:**
```bash
uvx ruff format .
git add -A
git commit -m "Add ..."        # verb first: Add / Fix / Remove ...
git push
docker compose stop
```

Half-finished work goes on a separate branch, not `main`:
```bash
git switch -c wip-6a
git add -A
git commit -m "WIP: step 6a"
git push -u origin wip-6a
```

## Test data

```bash
uv run python manage.py shell
```
```python
from banking.models import Account
from banking.services import deposit, withdraw, transfer

acc = Account.objects.first()
deposit(acc.pk, "200", "Salary")
```

---

## Step 6a: Read-only endpoints

### The big picture

```
Frontend  ──  GET /api/accounts/  ──▶  Django
                                       1. urls.py     finds which view handles this URL
                                       2. view        checks who is asking, loads their data
                                       3. serializer  converts Python objects into JSON
Frontend  ◀──  [{"account_number": "4821...", "balance": "125.00"}]
```

- **JSON**: plain text that every language can read; looks like Python dicts and lists.
- **GET** = "give me data". **POST** (step 6b) = "do something / create something".

### 1. Turn on DRF: `config/settings.py`

Add `"rest_framework"` to `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    ...
    "rest_framework",
    "accounts",
    "banking",
]
```

Add at the bottom:
```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}
```

- **Authentication** = "who are you?" For now, a browser login session, so you can test in the browser. Step 6c switches to tokens for the frontend.
- **Permission** = "are you allowed?" `IsAuthenticated` means every endpoint needs login by default. For a bank: lock everything, then open things on purpose.

### 2. Serializers: new file `banking/serializers.py`

```python
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
```

- `ModelSerializer` reads your model and builds the conversion for you (inheritance again).
- `fields` is a whitelist: only listed fields go out. `owner` and the account's internal `id` are not sent.
- `read_only_fields = fields`: these serializers only *show* data. Money only changes through `services.py`.
- Decimals are sent as **strings** (`"125.00"`). On purpose: JavaScript has the same float problem as Python.

### 3. Views: replace everything in `banking/views.py`

```python
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
```

- `ListAPIView` returns a **list**, `RetrieveAPIView` returns **one** object. DRF does the rest; you only say *which data* in `get_queryset()`.
- `self.request.user` is the logged-in user making the request.
- 🔒 **`owner=self.request.user` is the most important security line in the API.** Without it, any logged-in user could see everyone's accounts. Every query that touches money must be filtered by owner.
- `lookup_field = "account_number"`: URLs use the account number, not the database ID.
- `self.kwargs["account_number"]` is the value taken from the URL.
- `get_object_or_404` returns 404 if the account doesn't exist **or isn't yours**. We never say "exists, but not yours", because that tells an attacker which account numbers are real.

### 4. URLs: new file `banking/urls.py`

```python
from django.urls import path

from . import views

urlpatterns = [
    path("accounts/", views.AccountListView.as_view()),
    path("accounts/<str:account_number>/", views.AccountDetailView.as_view()),
    path(
        "accounts/<str:account_number>/transactions/",
        views.AccountTransactionListView.as_view(),
    ),
]
```

- `<str:account_number>` captures that part of the URL and gives it to the view as `self.kwargs["account_number"]`.
- `.as_view()` turns a view class into something Django's URL system can call.

Then `config/urls.py`:
```python
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("banking.urls")),
    path("api-auth/", include("rest_framework.urls")),
]
```

- `include("banking.urls")` puts banking's URLs under `api/`, so `accounts/` becomes `/api/accounts/`.
- `api-auth/` gives login/logout pages for DRF's browsable API (testing only).

### 5. Try it in the browser

1. Run the server and open http://127.0.0.1:8000/api/accounts/. You should get **403 Forbidden** (not logged in, so the lock works).
2. Log in at http://127.0.0.1:8000/api-auth/login/ with your superuser.
3. Open `/api/accounts/` again to see your accounts.
4. Copy an account number and open `/api/accounts/<number>/` and `/api/accounts/<number>/transactions/`.

### 6. 🔒 Security test (most important)

1. In `/admin`, create a **second user** (normal user, not staff) and give them an account.
2. In the shell, deposit money into their account.
3. Logged in as **yourself**, open `/api/accounts/<their-number>/transactions/`.
4. You must get **404**. If you can see their transactions, something is wrong: stop and get it checked.

### Checklist

- [ ] 403 when logged out
- [ ] Can see own accounts and transactions
- [ ] 404 for another user's account
- [ ] `uvx ruff format .` run, then committed and pushed

---

## When something breaks

1. **Read the last lines of the error first.** They name the file, the line and what's wrong. The lines above are Django's internal steps.
2. Check for typos, missing commas and wrong indentation. A one-item tuple needs a trailing comma: `("transaction_type",)`.
3. `ModuleNotFoundError` or `ImportError`: check the file name and the `from .xxx import ...` line.
4. "connection refused" or "could not connect to server": Postgres isn't running, so run `docker compose up -d`.
5. "password authentication failed": the `.env` password changed after Postgres was first created. If the data doesn't matter: `docker compose down -v`, then `docker compose up -d`, `migrate`, `createsuperuser`.
6. `relation "..." does not exist`: run `uv run python manage.py migrate`.
7. Compare your code line by line with this guide.
8. Still stuck: commit to a `wip-...` branch, push, and bring it back to the office.

## Coming next

- **6b**: POST endpoints for deposit, withdraw and transfer that call the functions in `services.py`, and turn `InsufficientFunds` into a proper error response.
- **6c**: token login for the frontend, plus CORS (lets a frontend on another address call the API).
- **7**: automated tests, including "the total of all balances doesn't change after a transfer".
