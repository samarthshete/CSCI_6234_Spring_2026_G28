# BudgetFlow

Intelligent personal finance management application with rule-based transaction categorization, budget tracking, spending analytics, exportable PDF/CSV reports, an AI-powered financial advisor, and a deterministic investment recommendation engine.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, TypeScript, Tailwind CSS v4, Recharts |
| Backend | FastAPI, Python 3.11, Pydantic v2 |
| Database | PostgreSQL 15, SQLAlchemy 2.0 (async), Alembic |
| Auth | JWT (python-jose), bcrypt |
| Storage | MinIO (S3-compatible), boto3, ReportLab |
| AI | OpenAI API (advisor), NumPy (Monte Carlo engine) |
| DevOps | Docker Compose, Makefile |

## Architecture

```
┌──────────────┐     HTTP/JSON     ┌──────────────┐     asyncpg     ┌──────────────┐
│   Next.js    │ ───────────────── │   FastAPI     │ ─────────────── │  PostgreSQL   │
│  (port 3000) │                   │  (port 8000)  │                 │  (port 5432)  │
└──────────────┘                   └──────────────┘                 └──────────────┘
                                          │
                                     S3 / MinIO
                                    (port 9000)
```

The frontend communicates with the backend via REST API (`/api/v1/*`). The backend uses async SQLAlchemy with PostgreSQL. The AI Advisor uses OpenAI function calling to query existing analytics, budgets, transactions, and alerts services, returning grounded answers with real numbers. All data is user-isolated via JWT authentication.

## Project Structure

```
BudgetFlowApp/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Route handlers
│   │   ├── core/            # Config, DB, security
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   │   └── advisor/     # AI advisor (tool registry, LLM orchestrator)
│   │   ├── renderers/       # PDF + CSV report renderers
│   │   └── storage/         # S3/MinIO storage abstraction
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

Runs PostgreSQL, MinIO, and the FastAPI backend in containers. Only the frontend runs on your machine.

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
| `S3_ENDPOINT_URL` | `http://localhost:9000` | Backend (report storage) |
| `S3_ACCESS_KEY` | `minioadmin` | Backend |
| `S3_SECRET_KEY` | `minioadmin` | Backend |
| `S3_BUCKET` | `budgetflow-reports` | Backend |
| `OPENAI_API_KEY` | *(required for Advisor)* | Backend (AI advisor) |
| `OPENAI_MODEL` | `gpt-4o-mini` | Backend |
| `ADVISOR_ENABLED` | `true` | Backend |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | Frontend |

## AI Advisor

The Advisor is a conversational financial assistant powered by OpenAI function calling. It queries your actual data (transactions, budgets, alerts, analytics) and responds with grounded answers.

**How it works:**
1. User sends a natural language question (e.g., "How much did I spend last month?")
2. The LLM decides which internal tools to call (get_summary, list_transactions, etc.)
3. Tools execute user-scoped SQL queries against the database
4. The LLM synthesizes tool results into a concise answer with real numbers

**Available tools:** `get_summary`, `get_trends`, `get_budget_vs_actual`, `list_budgets`, `get_budget`, `list_alerts`, `list_transactions`

**Setup:** Set `OPENAI_API_KEY` in your `.env` file. The advisor is disabled when the key is empty.

### Demo Script (6 Questions)

Use these questions to demonstrate the advisor in class:

1. **"How much did I spend last month?"** — Calls `get_summary` with last month's dates. Shows total spending and category breakdown.
2. **"What are my spending trends over the last 3 months?"** — Calls `get_trends` grouped by month. Shows monthly totals.
3. **"Am I over budget?"** — Calls `list_budgets` then `get_budget_vs_actual`. Shows budget utilization percentages.
4. **"Do I have any unread alerts?"** — Calls `list_alerts` with is_read=false. Shows threshold breaches.
5. **"Show me my last 10 transactions"** — Calls `list_transactions` with limit=10. Lists recent activity.
6. **"Which category am I spending the most on?"** — Calls `get_summary`. Identifies the top category by amount.

## Investment Recommendation Engine (UC08)

A deterministic, explainable engine that analyzes your financial data and produces personalized investment recommendations. No LLM dependency — pure rules and math.

**How it works:**
1. Computes monthly spending avg, income estimate, and emergency fund coverage from transaction data
2. Applies safety gates: blocks investing recommendations if emergency fund < 1 month, negative cashflow, or severe budget breaches
3. Maps risk profile (5-question questionnaire + horizon + liquidity need) to a risk bucket
4. Outputs: prioritized action plan, ETF-based model allocation, and Monte Carlo growth projection

**Risk Buckets:** Conservative, Moderate Conservative, Balanced, Moderate Growth, Growth

**Safety first:** Users with insufficient emergency funds or negative cashflow receive stabilization guidance instead of investment advice.

**Monte Carlo:** 500-path simulation using geometric Brownian motion, seeded per run_id for reproducibility. Shows median, 10th percentile, and 90th percentile outcomes.

## API Documentation

With the backend running, visit **http://localhost:8000/docs** for the interactive Swagger UI.

## License

This project is for educational purposes (OOD course project).
