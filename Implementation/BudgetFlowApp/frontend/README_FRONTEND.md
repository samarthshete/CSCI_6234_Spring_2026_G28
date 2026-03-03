# BudgetFlow Frontend

## Prerequisites

- Node.js 18+
- Docker (for Postgres)
- Backend running at `http://localhost:8000`

## Full Stack Quick Start — Docker (from `BudgetFlowApp/` root)

```bash
# 1. Build and start db + backend (first time or after schema changes)
make up
make migrate-docker

# 2. Verify
curl http://localhost:8000/health   # {"status":"ok","db":true,...}

# 3. Start frontend (separate terminal)
cd frontend && npm install && npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

To wipe everything and start fresh: `make reset-docker`

### Alternative: Local dev (no Docker backend)

```bash
make db-up && make db-wait      # Postgres in Docker only
make install && make migrate    # local venv
make run-backend                # uvicorn on host (uses backend/.env → localhost)
cd frontend && npm run dev      # separate terminal
```

## Environment Variables

`frontend/.env.local` (already included):

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | Backend API base URL |

## Pages

| Route | Auth | Description |
|-------|------|-------------|
| `/` | Public | Landing page |
| `/login` | Public | Login form (OAuth2 form encoding) |
| `/signup` | Public | Registration with validation |
| `/dashboard` | Protected | Getting started + spending summary |
| `/accounts` | Protected | Account CRUD + institution management |
| `/import` | Protected | CSV upload + import session history |
| `/transactions` | Protected | Transaction list + categorization |
| `/categories` | Protected | Category CRUD + rules editor |
| `/budgets` | Protected | Budget list + create |
| `/budgets/[id]` | Protected | Budget detail + edit + delete |
| `/analytics` | Protected | Summary, trends, budget-vs-actual |

## Tech Stack

- Next.js 16 (App Router)
- TypeScript
- Tailwind CSS v4
- Recharts (trend chart)
- No other external UI libraries — all components are custom (`src/components/ui/`)
