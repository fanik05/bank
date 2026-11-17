# Bank

A banking backend built with Django and Django REST Framework. It provides a JSON API for a separate frontend: customers log in with JWT, view their accounts and transaction history, withdraw money and transfer between accounts. Staff (tellers) handle deposits.

**Stack:** Python 3.15 · Django 6.1 · Django REST Framework · Simple JWT · PostgreSQL 18 (Docker) · pytest · uv

## Project structure

```
bank/
├── manage.py              Django's command-line tool
├── pyproject.toml         Dependencies and tool settings (pytest, Ruff)
├── uv.lock                Exact dependency versions (managed by uv)
├── compose.yaml           PostgreSQL container for local development
├── .env.example           Template for the environment variables in .env
├── conftest.py            Shared pytest fixtures (users, accounts, API clients)
│
├── config/                Project configuration
│   ├── settings.py        Settings; secrets and database are read from .env
│   └── urls.py            Root URLs: /admin/, /api/, /api/auth/
│
├── accounts/              Users and authentication
│   ├── models.py          Custom User model (adds phone_number)
│   ├── serializers.py     User and registration serializers
│   ├── views.py           Register and "me" endpoints
│   ├── urls.py            Auth routes: register, me, JWT login, refresh, logout
│   ├── test_auth.py       Authentication tests
│   └── test_register.py   Registration and "me" tests
│
└── banking/               Accounts and money
    ├── models.py          Account and Transaction (the ledger)
    ├── services.py        deposit(), withdraw(), transfer(): the only code that changes balances
    ├── serializers.py     JSON conversion and input validation
    ├── views.py           API endpoints
    ├── urls.py            Banking routes under /api/
    ├── test_services.py   Tests for the money rules
    └── test_api.py        Tests for the API (permissions, owner isolation)
```

### Design rules

- **Balances only change through `banking/services.py`.** Each operation runs inside a database transaction (`atomic()`) and locks the affected rows (`select_for_update()`). Transfers lock both accounts in ID order to avoid deadlocks.
- **The ledger is append-only.** Every balance change creates a `Transaction` record with `balance_after`. Transactions can't be edited or deleted, even in the admin.
- **No negative balances.** This is checked in code and enforced by a database constraint (`balance_not_negative`).
- **Money is `Decimal`, never `float`.** The API sends amounts as strings, for example `"125.00"`.
- **Customers only see their own data.** Every query is filtered by `owner=request.user`, and another user's account returns 404.

## Setup

### Requirements

- [uv](https://docs.astral.sh/uv/). It installs the right Python version (3.15) automatically.
- Docker with Docker Compose
- Git

### 1. Clone and install dependencies

```bash
git clone https://github.com/fanik05/bank.git
cd bank
uv sync
```

### 2. Create `.env`

```bash
cp .env.example .env
```

Replace the `change-me` values with random secrets:

```bash
uv run python -c "import secrets; print(secrets.token_urlsafe(50))"   # SECRET_KEY
uv run python -c "import secrets; print(secrets.token_urlsafe(24))"   # POSTGRES_PASSWORD
```

`.env` is ignored by Git. Never commit it.

| Variable | Purpose |
|---|---|
| `DEBUG` | `True` for local development, `False` in production |
| `SECRET_KEY` | Signs sessions and JWTs. Changing it logs everyone out |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Database name and credentials, used by both Docker and Django |
| `POSTGRES_HOST`, `POSTGRES_PORT` | Where Django connects (`localhost:5432` with the Docker setup) |

Set `POSTGRES_PASSWORD` **before** starting the database for the first time. Postgres only reads it when it creates the database.

### 3. Start PostgreSQL

```bash
docker compose up -d
```

### 4. Create the tables and an admin user

```bash
uv run python manage.py migrate
uv run python manage.py createsuperuser
```

### 5. Run the development server

```bash
uv run python manage.py runserver
```

- API: http://127.0.0.1:8000/api/
- Admin: http://127.0.0.1:8000/admin/

Customers sign up with `POST /api/auth/register/` and open bank accounts with `POST /api/accounts/`. Deposits are made by staff, either through the API or in the admin.

## API

All endpoints require authentication except register, login and refresh. Send the access token in a header:

```
Authorization: Bearer <access-token>
```

### Authentication (`/api/auth/`)

| Method | URL | Body | Returns |
|---|---|---|---|
| POST | `/api/auth/register/` | `username`, `password`, optional `email`, `first_name`, `last_name`, `phone_number` | the new user (without the password) |
| POST | `/api/auth/token/` | `username`, `password` | `access` and `refresh` tokens |
| POST | `/api/auth/token/refresh/` | `refresh` | new `access` and `refresh` tokens |
| POST | `/api/auth/logout/` | `refresh` | `{}`; the refresh token is blacklisted |
| GET | `/api/auth/me/` | | the logged-in user's `username`, `email`, `first_name`, `last_name`, `phone_number` |

Passwords must pass Django's password validators: at least 8 characters, not too common, not only numbers, not too similar to the username.

Access tokens last 5 minutes. Refresh tokens last 1 day and rotate: each refresh returns a new one and blacklists the old one.

### Banking (`/api/accounts/`)

| Method | URL | Who | Body |
|---|---|---|---|
| GET | `/api/accounts/` | Owner | |
| POST | `/api/accounts/` | Any logged-in user | none; opens a new account with balance `0.00` |
| GET | `/api/accounts/<account_number>/` | Owner | |
| GET | `/api/accounts/<account_number>/transactions/` | Owner | |
| POST | `/api/accounts/<account_number>/deposit/` | Staff only | `amount`, `description` (optional) |
| POST | `/api/accounts/<account_number>/withdraw/` | Owner | `amount`, `description` (optional) |
| POST | `/api/accounts/<account_number>/transfer/` | Owner of the sending account | `amount`, `to_account_number`, `description` (optional) |

`amount` must be positive with at most 2 decimal places. Errors return `400` with a message per field, for example `{"amount": ["Balance is 20.00, cannot withdraw 50.00."]}`.

## Development

### Tests

```bash
uv run pytest -v
```

Tests run against a separate temporary database (`test_bank`), so your development data isn't affected. Docker must be running.

### Formatting and linting

```bash
uvx ruff format .
uvx ruff check .
```

Migrations are excluded from Ruff.

### Before every commit

```bash
uvx ruff format .
uv run pytest
```

Only commit when all tests pass.

### Useful commands

| Command | What it does |
|---|---|
| `uv run python manage.py shell` | Python shell with the project loaded |
| `uv run python manage.py makemigrations` | Create migrations after changing models |
| `docker compose stop` | Stop PostgreSQL (data is kept) |
| `docker compose logs db` | Show PostgreSQL logs |
| `docker compose down -v` | ⚠️ Delete PostgreSQL **and all its data** |
