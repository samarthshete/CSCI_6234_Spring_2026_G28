# BudgetFlow

Intelligent personal finance management application with rule-based transaction categorization, budget tracking, and spending analytics.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, TypeScript, Tailwind CSS v4, Recharts |
| Backend | FastAPI, Python 3.11, Pydantic v2 |
| Database | PostgreSQL 15, SQLAlchemy 2.0 (async), Alembic |
| Auth | JWT (python-jose), bcrypt |
| DevOps | Docker Compose, Makefile |

## Architecture

```
┌──────────────┐     HTTP/JSON     ┌──────────────┐     asyncpg     ┌──────────────┐
│   Next.js    │ ───────────────── │   FastAPI     │ ─────────────── │  PostgreSQL   │
│  (port 3000) │                   │  (port 8000)  │                 │  (port 5432)  │
└──────────────┘                   └──────────────┘                 └──────────────┘
```

The frontend communicates with the backend via REST API (`/api/v1/*`). The backend uses async SQLAlchemy with PostgreSQL. All data is user-isolated via JWT authentication.

## Project Structure

```
BudgetFlowApp/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Route handlers
│   │   ├── core/            # Config, DB, security
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   └── services/        # Business logic
│   ├── alembic/             # Database migrations
│   ├── tests/               # pytest test suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js App Router pages
│   │   ├── components/      # Reusable UI components
│   │   └── lib/             # API client, auth helpers
│   └── package.json
├── docs/                    # Architecture, API, CSV schema docs
├── docker-compose.yml
├── Makefile
└── .env.example
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 18+
- Python 3.9+ (only for local backend development)

### Option A: Docker (recommended)

Runs PostgreSQL and the FastAPI backend in containers. Only the frontend runs on your machine.

```bash
# 1. Clone and navigate
cd Implementation/BudgetFlowApp

# 2. Start database + backend
make up

# 3. Run database migrations (required on first run)
make migrate-docker

# 4. Verify backend is healthy
curl http://localhost:8000/health
# → {"status":"ok","db":true,"app":"BudgetFlow"}

# 5. Start frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000** — sign up, log in, and start managing finances.

### Option B: Fully Local

Runs only PostgreSQL in Docker. Backend runs directly on your machine.

```bash
# 1. Start Postgres
make db-up
make db-wait

# 2. Create venv and install dependencies
make install

# 3. Copy environment config
cp .env.example backend/.env

# 4. Run migrations
make migrate

# 5. Start backend (terminal 1)
make run-backend

# 6. Start frontend (terminal 2)
cd frontend && npm install && npm run dev
```

### Useful Make Targets

| Command | Description |
|---------|------------|
| `make up` | Build and start db + backend containers |
| `make down` | Stop all containers |
| `make ps` | Show container status |
| `make migrate-docker` | Run migrations inside backend container |
| `make reset-docker` | Wipe DB, rebuild, and re-migrate |
| `make logs-backend` | Tail backend logs |
| `make test` | Run pytest (local backend) |
| `make help` | Show all available targets |

## Running Tests

```bash
# Local (requires running Postgres and venv)
make test

# Or directly
cd backend && .venv/bin/python -m pytest -q
```

## Environment Variables

See `.env.example` for all configurable values. Key variables:

| Variable | Default | Used By |
|----------|---------|---------|
| `DATABASE_URL` | `postgresql+asyncpg://...@localhost:5432/budgetflow_db` | Backend |
| `SECRET_KEY` | `change_me_in_production` | Backend (JWT signing) |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | Frontend |

## API Documentation

With the backend running, visit **http://localhost:8000/docs** for the interactive Swagger UI.

## License

This project is for educational purposes (OOD course project).
