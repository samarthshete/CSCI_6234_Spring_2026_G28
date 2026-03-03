# Database Bootstrap Guide

## Prerequisites

- **Docker** and **Docker Compose** (v2) installed.
- **Python 3.9+** available as `python3` (or override with `PYTHON=python`).
- No specific venv needs to be pre-activated; the Makefile handles it.

## Quick Start (Fresh Setup on macOS)

From the **BudgetFlowApp/** directory:

```bash
# One command does everything: reset DB, create venv, install deps, migrate, test
make all
```

Or step by step:

```bash
make db-up       # start Postgres container
make db-wait     # block until Postgres accepts connections
make install     # create venv + install requirements (idempotent)
make migrate     # alembic upgrade head
make test        # pytest -q
```

## Environment Variables

The backend reads config from `backend/.env` via pydantic-settings. A template is provided:

```bash
cp backend/.env.example backend/.env
# Edit backend/.env if your Postgres host/port/credentials differ from defaults.
```

Default values in `app/core/config.py` match the `docker-compose.yml` Postgres service, so `.env` is optional for local dev with Docker.

The `DATABASE_URL` is computed from the individual `POSTGRES_*` variables. You do **not** need to set `DATABASE_URL` directly.

## Makefile Targets

All targets run from the **BudgetFlowApp/** root.

| Target         | Description                                             |
|----------------|---------------------------------------------------------|
| `make help`    | Show all targets                                        |
| `make venv`    | Create `backend/.venv` if it doesn't exist              |
| `make install` | Create venv + `pip install -r requirements.txt`         |
| `make db-up`   | Start Postgres container (detached)                     |
| `make db-down` | Stop Postgres container                                 |
| `make db-reset`| Drop volume, recreate container, wait for healthy       |
| `make db-wait` | Block until Postgres healthcheck passes                 |
| `make migrate` | `python -m alembic upgrade head` (from backend/)       |
| `make test`    | `python -m pytest -q` (from backend/)                   |
| `make all`     | `db-reset` → `install` → `migrate` → `test`            |

Override the Python binary: `make all PYTHON=python3.11`

## How `migrate` and `test` Work

The Makefile uses `python -m alembic` and `python -m pytest` instead of calling venv binaries directly. This means whichever `python3` is on your `PATH` (system, pyenv, conda, or a manually activated venv) will be used. If you want to use the project venv specifically, activate it first or run `make install` which ensures `backend/.venv` has all deps.

## Migration History

Linear chain; each revision depends on the previous one:

1. **ca29e518b024** — UC01: `users` table.
2. **0dd224777185** — UC02: `institutions` + `financial_accounts` (original schema with `nickname`).
3. **a1b2c3d4e5f6** — UC02 schema update: renames `nickname → name`, adds `balance`, `is_active`, `created_at`, `updated_at`, `bank_account_number_last4`, `credit_card_last4`, drops old columns, adds `institution_id` index.
4. **b7f8e9a0c1d2** — UC02 cleanup: idempotent safety net that drops `nickname` if it still exists alongside `name`.

Current head: **b7f8e9a0c1d2**

## When Migrations Drift

If `alembic upgrade head` fails because the database schema doesn't match what Alembic expects:

1. **Check current revision:** `cd backend && python -m alembic current`
2. **Check column state:** `docker compose exec db psql -U budgetflow_user -d budgetflow_db -c '\d financial_accounts'`
3. **Option A — Reset (local dev):** `make db-reset && make migrate` (drops volume and re-creates from scratch).
4. **Option B — Stamp and proceed:** If you know the schema matches a later revision: `cd backend && python -m alembic stamp <revision>` then `make migrate`.
5. **Never edit already-applied migrations.** Always add a new forward migration.

## Canonical Column Name

The canonical column for the account display name is **`name`** (not `nickname`). Migration `0dd224777185` originally created `nickname`; migration `a1b2c3d4e5f6` renamed it to `name`; migration `b7f8e9a0c1d2` is a safety net that drops `nickname` if it still lingers.

## Docker Compose Healthcheck

The Postgres service includes a `pg_isready` healthcheck. The `make db-wait` target polls it until the database is accepting connections before proceeding.
