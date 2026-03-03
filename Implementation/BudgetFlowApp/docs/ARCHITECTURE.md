# BudgetFlow — Architecture Proposal

**Version:** 1.0  
**Status:** For review before implementation milestones  
**Contract:** `/analysis` UML diagrams (Domain Model, Use Case, Robustness, Activity) are the source of truth.

---

## 1. Overview

BudgetFlow is an Intelligent Personal Finance Management System built as a production-grade, academically rigorous full-stack web application. This document defines the **complete architecture** before implementation: folder structure, database schema, API surface, authentication, user isolation, and data flow aligned with Phase 1 use cases (UC01–UC07).

---

## 2. Folder Structure

```
BudgetFlowApp/
├── backend/
│   ├── alembic/
│   │   ├── env.py                    # Async engine, run_migrations_online
│   │   ├── script.py.mako
│   │   └── versions/                 # One migration per milestone where schema changes
│   ├── app/
│   │   ├── main.py                   # FastAPI app, CORS, router includes
│   │   ├── core/
│   │   │   ├── config.py             # Settings (pydantic-settings)
│   │   │   ├── database.py           # AsyncSession, get_db
│   │   │   ├── security.py           # bcrypt, JWT (access + refresh)
│   │   │   └── exceptions.py         # Centralized HTTP exception → readable JSON
│   │   ├── models/                   # SQLAlchemy 2.0 async domain models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── account.py            # Institution, FinancialAccount STI, Bank/Credit/Investment
│   │   │   ├── transaction.py       # Transaction, Merchant (UC03, UC04, UC07)
│   │   │   ├── category.py           # Category (rules in JSONB column) (UC04)
│   │   │   ├── budget.py             # Budget, BudgetItem (UC05, UC06)
│   │   │   ├── alert.py              # BudgetAlert (UC06)
│   │   │   └── import_session.py     # ImportSession (UC03)
│   │   ├── schemas/                  # Pydantic request/response
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── token.py
│   │   │   ├── account.py
│   │   │   ├── transaction.py
│   │   │   ├── category.py
│   │   │   ├── budget.py
│   │   │   ├── alert.py
│   │   │   └── import_session.py
│   │   ├── services/                 # Business logic, user isolation at query level
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── account_service.py
│   │   │   ├── import_service.py     # CSV parse, validate, duplicate detection
│   │   │   ├── categorization_service.py  # Rules-first (Category.rules) → fallback → confidence → manual (Phase 1: no LLM; fallback = needs_manual)
│   │   │   ├── budget_service.py
│   │   │   ├── alert_service.py      # BudgetMonitor, NotificationService adapter
│   │   │   └── analytics_service.py
│   │   ├── api/
│   │   │   ├── deps.py               # get_db, get_current_user (JWT)
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── auth.py
│   │   │       ├── accounts.py
│   │   │       ├── transactions.py   # list, import, categorize
│   │   │       ├── categories.py
│   │   │       ├── budgets.py
│   │   │       ├── alerts.py
│   │   │       └── analytics.py
│   │   └── middleware/               # Optional: request ID, logging
│   ├── tests/
│   │   ├── conftest.py               # Async client, DB override, fixtures
│   │   ├── test_auth.py
│   │   ├── test_accounts.py
│   │   ├── test_import.py
│   │   ├── test_categorization.py
│   │   ├── test_budgets.py
│   │   ├── test_alerts.py
│   │   └── test_analytics.py
│   ├── utils/                        # CSV schema, LLM client abstraction
│   │   ├── csv_schema.py             # Required columns, validation, docs
│   │   └── llm_provider.py           # Phase 2 only: abstract + OpenAI impl for LLM fallback
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── alembic.ini
│   └── .env.example
├── frontend/                         # Next.js (TypeScript) + Tailwind
│   ├── app/                          # App Router
│   │   ├── layout.tsx
│   │   ├── page.tsx                  # Landing
│   │   ├── login/
│   │   ├── signup/
│   │   ├── dashboard/
│   │   ├── accounts/
│   │   ├── import/
│   │   ├── transactions/             # List + categorize UI
│   │   ├── budgets/
│   │   ├── alerts/
│   │   └── analytics/
│   ├── components/
│   ├── hooks/
│   ├── lib/                          # API client, auth context
│   └── styles/
├── analysis/                         # Symlink or copy of repo /analysis
│   ├── DomainModel/
│   ├── Robustness/
│   └── ActivityDiagram/
└── docs/
    ├── ARCHITECTURE.md               # This file
    ├── API.md                        # Endpoint list + error format
    └── CSV_IMPORT_SCHEMA.md          # Required columns, formats, rejection messages
```

---

## 3. Database Schema (UML-Aligned)

All entity and relationship names match **Analysis/DomainModel/Updated DomainModel/DomainModel_FINAL.puml**. Additional tables for implementation (ImportSession) are documented as extensions. **Option A:** No separate CategorizationRule entity; rules are stored in `categories.rules` (JSONB).

### 3.1 Tables and Columns

| Table | Columns | Notes |
|-------|---------|--------|
| **users** | id (PK UUID), name, email (unique, indexed), hashed_password | — |
| **institutions** | id (PK UUID), name (unique, indexed) | Global; no user_id |
| **financial_accounts** | id (PK UUID), user_id (FK→users, CASCADE, indexed), institution_id (FK→institutions, SET NULL), type (discriminator), nickname, currency, is_active (bool), routing_number_last4, card_last4, credit_limit, broker_name | Single-table inheritance: type ∈ {bank, credit, investment} |
| **transactions** | id (PK UUID), account_id (FK→financial_accounts, CASCADE, indexed), posted_date (date), amount (numeric), description, category_id (FK→categories, SET NULL), merchant_id (FK→merchants, SET NULL), created_at | account ownership implies user isolation |
| **merchants** | id (PK UUID), name (indexed) | Can be global or per-user; we use global with name uniqueness for dedup |
| **categories** | id (PK UUID), name, type (e.g. income/expense), user_id (nullable for system categories), **rules** (JSONB, default `[]`) | Per-user or shared; see §3.5 for rules shape. |
| **budgets** | id (PK UUID), user_id (FK→users, CASCADE, indexed), name, period_start (date), period_end (date), period_type (e.g. monthly, weekly) | |
| **budget_items** | id (PK UUID), budget_id (FK→budgets, CASCADE), category_id (FK→categories), limit_amount (numeric) | Budget 1 — 1..* BudgetItem |
| **budget_alerts** | id (PK UUID), user_id (FK→users, CASCADE, indexed), budget_id (FK→budgets, SET NULL), threshold_percent (int), is_read (bool), created_at (timestamptz) | User receives alerts; optional link to budget |
| **import_sessions** | id (PK UUID), user_id (FK, indexed), account_id (FK), status, total_count, imported_count, failed_count, started_at, completed_at, raw_metadata (jsonb) | One record per import run |

### 3.2 Relationships and Cardinality (from UML)

- User 1 — 0..* FinancialAccount (owns); User 1 — 0..* Budget (creates); User 1 — 0..* BudgetAlert (receives).
- Institution 1 — 0..* FinancialAccount (provides).
- FinancialAccount 1 — 0..* Transaction (contains).
- Transaction * — 0..1 Category (belongsTo); Transaction * — 0..1 Merchant (paidTo).
- Budget 1 — 1..* BudgetItem (contains); BudgetItem * — 1 Category (tracksSpendingIn).
- BudgetAlert * — 0..1 Budget (monitors).

### 3.3 Indexes

- users: `ix_users_email` (unique).
- institutions: `ix_institutions_name` (unique).
- financial_accounts: `ix_financial_accounts_user_id`, `ix_financial_accounts_institution_id`.
- transactions: `ix_transactions_account_id`, `ix_transactions_posted_date`, `ix_transactions_category_id`.
- categories: `ix_categories_user_id`, `ix_categories_name`.
- budgets: `ix_budgets_user_id`, `ix_budgets_period_start`, `ix_budgets_period_end`.
- budget_items: `ix_budget_items_budget_id`, `ix_budget_items_category_id`.
- budget_alerts: `ix_budget_alerts_user_id`, `ix_budget_alerts_budget_id`, `ix_budget_alerts_created_at`.
- import_sessions: `ix_import_sessions_user_id`, `ix_import_sessions_account_id`.

### 3.4 Cascade Rules

- On User delete: CASCADE financial_accounts, budgets, budget_alerts, import_sessions. (Transactions cascade via account. Categories may be user-scoped or system; user-owned categories handled per product decision.)
- On FinancialAccount delete: CASCADE transactions.
- On Budget delete: CASCADE budget_items.
- On Institution delete: SET NULL on financial_accounts.institution_id.
- On Category delete: SET NULL on transactions.category_id; BudgetItem may restrict or SET NULL per product decision.

### 3.5 Category.rules JSONB (Option A)

No separate `categorization_rules` table. Each category has a `rules` column (JSONB, default `[]`). Rule-based categorization reads from all user-visible categories’ `rules` and matches transaction description (and optionally merchant) against patterns.

**Suggested shape per rule (application-level):** `{ "pattern": string (keyword or regex), "priority": number }`. Order/priority determines which category wins when multiple rules match. Rule editing: `PATCH /api/v1/categories/{id}` with `rules: [...]` or dedicated `PATCH /api/v1/categories/{id}/rules`.

---

## 4. API Endpoints (Phase 1)

All authenticated routes require `Authorization: Bearer <access_token>`. Every query that returns or mutates user-specific data **filters by `user_id`** (from `get_current_user`) at the service/repository layer.

### 4.1 UC01 — Authenticate User

| Method | Path | Description | Request / Response |
|--------|------|-------------|--------------------|
| POST | `/api/v1/auth/signup` | Register | Body: `{ email, name, password }` → 201 UserOut |
| POST | `/api/v1/auth/login` | Login (OAuth2 form) | `username=email, password` → 200 `{ access_token, refresh_token, token_type }` |
| POST | `/api/v1/auth/refresh` | Refresh access token | Body: `{ refresh_token }` → 200 `{ access_token, token_type }` |

Errors: 400 (email exists, invalid input), 401 (invalid credentials).

### 4.2 UC02 — Manage Accounts

| Method | Path | Description | Request / Response |
|--------|------|-------------|--------------------|
| GET | `/api/v1/accounts` | List current user's accounts | → 200 List\<FinancialAccountOut\> |
| GET | `/api/v1/accounts/{id}` | Get one account (user-isolated) | → 200 FinancialAccountOut or 404 |
| POST | `/api/v1/accounts` | Create account (bank/credit/investment) | Body: subtype schema → 201 FinancialAccountOut |
| PATCH | `/api/v1/accounts/{id}` | Update account (user-isolated) | Body: partial → 200 FinancialAccountOut or 404 |
| DELETE | `/api/v1/accounts/{id}` | Delete account (user-isolated) | → 204 or 404 |
| GET | `/api/v1/institutions` | List institutions (global) | → 200 List\<InstitutionOut\> |

### 4.3 UC03 — Import Transactions

| Method | Path | Description | Request / Response |
|--------|------|-------------|--------------------|
| POST | `/api/v1/transactions/import` | Upload CSV or trigger Bank API sim | Body: multipart file + account_id (or source=bank_api) → 202 ImportSessionOut (status pending/processing) |
| GET | `/api/v1/transactions/import/sessions` | List user's import sessions | Query: limit, offset → 200 List\<ImportSessionOut\> |
| GET | `/api/v1/transactions/import/sessions/{id}` | Get import session result (user-isolated) | → 200 ImportSessionOut + summary (imported, failed, duplicates) |

CSV schema: see **docs/CSV_IMPORT_SCHEMA.md**. Validation errors return 422 with readable messages.

### 4.4 UC04 — Categorize Expenses

| Method | Path | Description | Request / Response |
|--------|------|-------------|--------------------|
| GET | `/api/v1/transactions` | List transactions (user-isolated, filters) | Query: account_id, category_id, date_from, date_to → 200 List\<TransactionOut\> |
| POST | `/api/v1/transactions/{id}/categorize` | Run categorization pipeline for one transaction | Body: optional `{ category_id }` for manual → 200 TransactionOut (category_id, confidence, **needs_manual** when no rule matches in Phase 1) |
| GET | `/api/v1/categories` | List categories (user + system) | → 200 List\<CategoryOut\> (includes `rules` JSONB) |
| PATCH | `/api/v1/categories/{id}` | Update category (name, type, **rules**) (user-isolated where applicable) | Body: partial { name?, type?, rules? } → 200 CategoryOut |
| PATCH | `/api/v1/categories/{id}/rules` | Update only category rules (JSONB) (optional dedicated endpoint) | Body: `{ rules: [{ pattern, priority }, ...] }` → 200 CategoryOut |

**Pipeline (UML-compliant):** Rules-first (read rules from `Category.rules` across user-visible categories) → fallback → confidence check → manual if low. Persist result; optionally append new rule to the matched category’s `rules` array. **Phase 1:** No LLM; when no rule matches, return `needs_manual=true` and do not assign category until user provides one via manual flow. **Phase 2:** LLM fallback when no rule matches.

### 4.5 UC05 — Set Budget Thresholds

| Method | Path | Description | Request / Response |
|--------|------|-------------|--------------------|
| GET | `/api/v1/budgets` | List user's budgets | Query: period_from, period_to → 200 List\<BudgetOut\> |
| GET | `/api/v1/budgets/{id}` | Get budget with items (user-isolated) | → 200 BudgetOut + items or 404 |
| POST | `/api/v1/budgets` | Create budget + items | Body: name, period_start, period_end, period_type, items[{ category_id, limit_amount }] → 201 BudgetOut |
| PATCH | `/api/v1/budgets/{id}` | Update budget/items (user-isolated) | → 200 BudgetOut or 404 |
| DELETE | `/api/v1/budgets/{id}` | Delete budget (user-isolated) | → 204 or 404 |

Thresholds: 80%, 90%, 100% (configurable) used by UC06.

### 4.6 UC06 — Receive Budget Alerts

| Method | Path | Description | Request / Response |
|--------|------|-------------|--------------------|
| GET | `/api/v1/alerts` | List user's budget alerts | Query: is_read, budget_id, limit → 200 List\<BudgetAlertOut\> |
| PATCH | `/api/v1/alerts/{id}/read` | Mark alert read (user-isolated) | → 200 BudgetAlertOut or 404 |

Alerts are **created** by a background process (BudgetMonitor) when thresholds are crossed; NotificationService adapter (e.g. email stub) dispatches. No “create alert” from client.

### 4.7 UC07 — View Analytics Dashboard

| Method | Path | Description | Request / Response |
|--------|------|-------------|--------------------|
| GET | `/api/v1/analytics/summary` | Spending summary (user-isolated) | Query: date_from, date_to, account_ids[], category_ids[] → 200 { total_spending, by_category, by_account } |
| GET | `/api/v1/analytics/trends` | Time-series for charts | Query: date_from, date_to, group_by=day|week|month → 200 [{ period, amount }] |
| GET | `/api/v1/analytics/budget-vs-actual` | Budget vs actual per category | Query: budget_id, date_from, date_to → 200 [{ category_id, limit, spent, percent }] |

All aggregations filter by `user_id` via account/budget ownership.

### 4.8 Error Response Format

Every error returns JSON with a **readable, user-facing message**:

```json
{
  "detail": "Human-readable message",
  "code": "OPTIONAL_ERROR_CODE",
  "errors": []
}
```

Use 400 for validation/business logic, 401 for unauthenticated, 403 for forbidden, 404 for not found, 422 for schema validation (e.g. CSV).

---

## 5. Data Flow (Per Use Case)

- **UC01:** Client → Auth API → AuthService (hash, create/find user) → DB. Login/refresh → Security (JWT create/verify) → Token response.
- **UC02:** Client → Accounts API → AccountService (all queries `WHERE user_id = current_user.id`) → DB. Institutions: read-only global table.
- **UC03:** Client → Import API → ImportService: validate CSV schema → TransactionParser → DuplicateDetector (same user/account/date/amount/description) → persist Transaction rows + ImportSession → optionally trigger categorization (UC04).
- **UC04:** CategorizationController: load rules from each Category’s `rules` JSONB (user-visible categories) → Rule-based match → else fallback (Phase 1: set needs_manual=true, no LLM; Phase 2: LLM) → ConfidenceEvaluator → if low or needs_manual, surface manual selection; else persist category_id and optionally append rule to that category’s `rules`.
- **UC05:** Client → Budgets API → BudgetService (all filters by `user_id`) → CRUD Budget + BudgetItems; AlertConfigManager sets up threshold triggers for UC06.
- **UC06:** BudgetMonitor (scheduled or event-driven) compares spending to BudgetItem limits → when threshold crossed → AlertFactory creates BudgetAlert → NotificationDispatcher (adapter: email stub) → user receives; API only reads/updates alerts (user-isolated).
- **UC07:** Client → Analytics API → AnalyticsService (aggregations with `user_id` via accounts/budgets) → return chart-ready payloads; frontend uses Recharts.

---

## 6. Alembic Migration Strategy

- **Bootstrap:** Initial migration creates `users` (UC01).
- **Per-milestone migrations:** One migration per UC that adds/changes tables (e.g. UC02 institutions + financial_accounts; UC03 import_sessions + transactions + merchants; UC04 categories with `rules` JSONB; UC05 budgets + budget_items; UC06 budget_alerts).
- **Order:** Linear chain; no branches. Down revisions: run `downgrade` for rollback.
- **Async:** `env.py` uses `run_async` with `create_async_engine` and `async_sessionmaker` so migrations run against the same async engine as the app.
- **Naming:** `{revision}_description.py` (e.g. `add_transactions_and_import_sessions_uc03.py`).

---

## 7. Authentication Flow

- **Signup:** Store user with bcrypt-hashed password.
- **Login:** Validate credentials → issue **access token** (short-lived, e.g. 15–60 min) and **refresh token** (long-lived, e.g. 7 days), both signed JWT. Store refresh token in DB or signed only (stateless refresh); if stored, revoke on logout.
- **Access:** `get_current_user` dependency: extract Bearer token → decode JWT → `sub` = user id → load User from DB; if missing/invalid → 401/403 with readable message.
- **Refresh:** POST `/api/v1/auth/refresh` with `refresh_token` → verify → issue new access token (and optionally new refresh token).
- **User isolation:** No endpoint accepts `user_id` from the client; `current_user.id` is the only source for all scoped queries.

---

## 8. User Isolation Enforcement

- **Rule:** Every query that reads or writes user-specific data **must** include a filter by `user_id` (or by a relation that belongs to the user, e.g. account_id IN user’s accounts).
- **Layers:**  
  - **API:** Only passes `current_user` from `get_current_user` to services.  
  - **Service:** All list/get/update/delete use `user_id = current_user.id` or join through user-owned entities (e.g. transactions via account → user).  
- **Tests:** Each milestone includes integration tests: User A cannot see or modify User B’s accounts, transactions, budgets, alerts, or import sessions (expect 404 or 403).

---

## 9. UML Alignment and Design Decisions

| Item | UML / Spec | Decision |
|------|------------|----------|
| FinancialAccount | abstract, STI with discriminator | Single table `financial_accounts` with `type` discriminator; subtype-specific columns nullable. |
| User ↔ FinancialAccount | 1 — 0..* owns | Enforced by `user_id` FK and all queries. |
| Transaction ↔ Category | * — 0..1 | category_id nullable. |
| Transaction ↔ Merchant | * — 0..1 | merchant_id nullable. |
| Budget ↔ BudgetItem | 1 — 1..* | budget_items.budget_id FK, CASCADE delete. |
| BudgetAlert ↔ Budget | * — 0..1 | budget_id nullable so alerts still exist if budget deleted. |
| ImportSession | Not in domain diagram | Added for UC03; documented in API and schema. |
| Category rules | Not a separate entity in domain diagram | **Option A:** No CategorizationRule table; rules stored in `categories.rules` (JSONB, default `[]`). Rule-based categorization reads from Category.rules; rule editing via PATCH Category or PATCH /categories/{id}/rules. |
| is_active (FinancialAccount) | In DomainModel_FINAL | Column added; default True. |
| JWT | Access + refresh | Implemented; refresh endpoint and optional refresh token storage. |

If any implementation detail forces a diagram change, the corresponding `.puml` (and exported `.png`) in `/analysis` will be updated and the change documented here or in an ADR.

---

## 10. Phase 1 Milestones (Summary)

| Milestone | Use Case | Deliverables |
|-----------|----------|--------------|
| M1 | UC01 Auth | Migrations (users), JWT access+refresh, signup/login/refresh, get_current_user, tests, frontend login/signup |
| M2 | UC02 Accounts | Institutions + financial_accounts (STI), CRUD API, user isolation, tests, frontend accounts CRUD |
| M3 | UC03 Import | import_sessions, transactions, merchants; CSV validation, duplicate detection, import API, tests, frontend import flow |
| M4 | UC04 Categorize | categories (with `rules` JSONB); rules-first → fallback (Phase 1: needs_manual only, no LLM) → confidence → manual; APIs (incl. PATCH category/rules), tests, frontend categorize UI |
| M5 | UC05 Budgets | budgets, budget_items; CRUD, threshold config, tests, frontend budget setup |
| M6 | UC06 Alerts | budget_alerts, BudgetMonitor, NotificationService adapter, list/mark-read API, tests, frontend alert history |
| M7 | UC07 Dashboard | Analytics endpoints, filters, chart-ready data, tests, frontend Recharts dashboard |

Each milestone: Alembic migration, models, schemas, services (with user isolation), API routes, pytest (happy path, isolation, validation, errors), frontend page(s). Phase 2 starts only after all Phase 1 tests pass.

---

## 11. Next Steps

1. **Review:** Confirm this architecture with stakeholders; align any open points with UML.
2. **Implement:** Proceed milestone-by-milestone (M1 → M7); no skipping.
3. **Document:** Keep **CSV_IMPORT_SCHEMA.md** and **API.md** updated as endpoints and schema evolve.
4. **CI/CD:** GitHub Actions run tests and lint on every push; deployment to Vercel (frontend) + Render/Railway (backend) + Railway/Supabase (DB) per deployment guide.

---

*End of Architecture Proposal.*
