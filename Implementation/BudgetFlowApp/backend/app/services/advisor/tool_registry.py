"""
Advisor tool definitions. Each tool is an async function that reads
our DB (user-scoped) and returns a JSON-serializable dict.
"""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Callable, Coroutine, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import FinancialAccount
from app.models.transaction import Transaction
from app.services import analytics_service, budget_service, alert_service, recommendation_service


ToolFn = Callable[..., Coroutine[Any, Any, dict]]

TOOL_DEFINITIONS: dict[str, dict] = {}
_TOOL_FUNCTIONS: dict[str, ToolFn] = {}


def _serialize(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, list):
        return [_serialize(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    return obj


def _parse_date(val: Optional[str]) -> Optional[date]:
    if not val:
        return None
    return datetime.strptime(val, "%Y-%m-%d").date()


def _parse_uuid_list(val: Optional[list]) -> Optional[list[uuid.UUID]]:
    if not val:
        return None
    return [uuid.UUID(v) for v in val]


# --- Tool implementations ---------------------------------------------------

async def _get_summary(db: AsyncSession, user_id: uuid.UUID, args: dict) -> dict:
    result = await analytics_service.get_summary(
        db, user_id,
        date_from=_parse_date(args.get("date_from")),
        date_to=_parse_date(args.get("date_to")),
        account_ids=_parse_uuid_list(args.get("account_ids")),
        category_ids=_parse_uuid_list(args.get("category_ids")),
    )
    return _serialize(result)


async def _get_trends(db: AsyncSession, user_id: uuid.UUID, args: dict) -> dict:
    group_by = args.get("group_by", "month")
    date_from = _parse_date(args.get("date_from"))
    date_to = _parse_date(args.get("date_to"))
    if not date_from or not date_to:
        return {"error": "date_from and date_to are required for trends"}
    result = await analytics_service.get_trends(db, user_id, date_from, date_to, group_by)
    return {"trends": _serialize(result)}


async def _get_budget_vs_actual(db: AsyncSession, user_id: uuid.UUID, args: dict) -> dict:
    budget_id_str = args.get("budget_id")
    if not budget_id_str:
        return {"error": "budget_id is required"}
    result = await analytics_service.get_budget_vs_actual(db, user_id, uuid.UUID(budget_id_str))
    return {"budget_vs_actual": _serialize(result)}


async def _list_budgets(db: AsyncSession, user_id: uuid.UUID, args: dict) -> dict:
    budgets = await budget_service.list_budgets(
        db, user_id,
        period_from=args.get("period_from"),
        period_to=args.get("period_to"),
    )
    return {"budgets": [
        _serialize({
            "id": str(b.id), "name": b.name,
            "period_start": b.period_start, "period_end": b.period_end,
            "period_type": b.period_type, "item_count": len(b.items),
        })
        for b in budgets
    ]}


async def _get_budget(db: AsyncSession, user_id: uuid.UUID, args: dict) -> dict:
    budget_id_str = args.get("budget_id")
    if not budget_id_str:
        return {"error": "budget_id is required"}
    b = await budget_service.get_budget(db, user_id, uuid.UUID(budget_id_str))
    return _serialize({
        "id": str(b.id), "name": b.name,
        "period_start": b.period_start, "period_end": b.period_end,
        "period_type": b.period_type, "thresholds": b.thresholds,
        "items": [{"category_id": str(i.category_id), "limit_amount": i.limit_amount} for i in b.items],
    })


async def _list_alerts(db: AsyncSession, user_id: uuid.UUID, args: dict) -> dict:
    is_read = args.get("is_read")
    if isinstance(is_read, str):
        is_read = is_read.lower() == "true"
    alerts = await alert_service.list_alerts(db, user_id, is_read)
    return {"alerts": [
        _serialize({
            "id": str(a.id),
            "threshold_percent": a.threshold_percent,
            "spent_amount": a.spent_amount,
            "limit_amount": a.limit_amount,
            "period_start": a.period_start,
            "period_end": a.period_end,
            "is_read": a.is_read,
        })
        for a in alerts[:20]
    ]}


async def _list_transactions(db: AsyncSession, user_id: uuid.UUID, args: dict) -> dict:
    limit = min(int(args.get("limit", 50)), 100)
    date_from = _parse_date(args.get("date_from"))
    date_to = _parse_date(args.get("date_to"))

    stmt = (
        select(Transaction)
        .join(FinancialAccount, FinancialAccount.id == Transaction.account_id)
        .where(FinancialAccount.user_id == user_id)
        .order_by(Transaction.posted_date.desc())
        .limit(limit)
    )
    if date_from:
        stmt = stmt.where(Transaction.posted_date >= date_from)
    if date_to:
        stmt = stmt.where(Transaction.posted_date <= date_to)
    if args.get("account_ids"):
        stmt = stmt.where(Transaction.account_id.in_(_parse_uuid_list(args["account_ids"])))
    if args.get("category_ids"):
        stmt = stmt.where(Transaction.category_id.in_(_parse_uuid_list(args["category_ids"])))

    result = await db.execute(stmt)
    txns = result.scalars().all()
    return {"transactions": [
        _serialize({
            "id": str(t.id), "posted_date": t.posted_date,
            "amount": t.amount, "description": t.description,
            "category_id": str(t.category_id) if t.category_id else None,
        })
        for t in txns
    ], "count": len(txns)}


async def _run_recommendation(db: AsyncSession, user_id: uuid.UUID, args: dict) -> dict:
    answers = args.get("answers")
    horizon = args.get("horizon_months", 60)

    rp_input = None
    if answers and isinstance(answers, dict):
        rp_input = {
            "answers": answers,
            "horizon_months": horizon,
            "liquidity_need": args.get("liquidity_need", "moderate"),
        }

    run = await recommendation_service.execute_run(
        db, user_id, risk_profile_input=rp_input, horizon_override=horizon,
    )
    out = run.outputs or {}

    compact: dict[str, Any] = {
        "run_id": str(run.id),
        "needs_profile": out.get("needs_profile", False),
        "gates": out.get("gates", []),
        "safety_warnings": out.get("safety_warnings", []),
        "risk": out.get("risk"),
        "monthly_spending_avg": out.get("monthly_spending_avg", 0),
        "emergency_fund_months": out.get("emergency_fund_months", 0),
        "investable_monthly": out.get("investable_monthly", 0),
        "cashflow_positive": out.get("cashflow_positive", True),
    }

    blocked = len(out.get("safety_warnings", [])) > 0

    if not blocked:
        compact["allocation"] = [
            {"ticker": a["ticker"], "pct": a["pct"]} for a in out.get("allocation", [])
        ]
        compact["allocation_rationale"] = out.get("allocation_rationale", [])
        proj = out.get("projection", [])
        if proj:
            compact["projection_start"] = proj[0]
            compact["projection_end"] = proj[-1]
            compact["projection_points"] = len(proj)
    else:
        items = [{"priority": i.priority, "type": i.type, "title": i.title} for i in run.items]
        compact["action_items"] = items

    if out.get("needs_profile"):
        compact["missing_profile_note"] = (
            "No risk profile on file. Ask the user these 5 questions (each 1-5): "
            "market_drop_reaction, investment_experience, income_stability, "
            "loss_tolerance_pct, goal_priority. Also ask for horizon_months."
        )

    return _serialize(compact)


async def _get_latest_recommendation(db: AsyncSession, user_id: uuid.UUID, args: dict) -> dict:
    run = await recommendation_service.get_latest_run(db, user_id)
    if not run:
        return {"error": "No recommendation runs found. Use run_recommendation first."}

    out = run.outputs or {}
    blocked = len(out.get("safety_warnings", [])) > 0

    compact: dict[str, Any] = {
        "run_id": str(run.id),
        "created_at": run.created_at,
        "needs_profile": out.get("needs_profile", False),
        "gates": out.get("gates", []),
        "risk": out.get("risk"),
        "monthly_spending_avg": out.get("monthly_spending_avg", 0),
        "emergency_fund_months": out.get("emergency_fund_months", 0),
        "investable_monthly": out.get("investable_monthly", 0),
        "cashflow_positive": out.get("cashflow_positive", True),
        "safety_warnings": out.get("safety_warnings", []),
    }

    if not blocked:
        compact["allocation"] = [
            {"ticker": a["ticker"], "pct": a["pct"]} for a in out.get("allocation", [])
        ]
        proj = out.get("projection", [])
        if proj:
            compact["projection_end"] = proj[-1]

    items = [{"priority": i.priority, "type": i.type, "title": i.title} for i in run.items]
    compact["action_items"] = items
    return _serialize(compact)


# --- Registry ---------------------------------------------------------------

_TOOL_FUNCTIONS = {
    "get_summary": _get_summary,
    "get_trends": _get_trends,
    "get_budget_vs_actual": _get_budget_vs_actual,
    "list_budgets": _list_budgets,
    "get_budget": _get_budget,
    "list_alerts": _list_alerts,
    "list_transactions": _list_transactions,
    "run_recommendation": _run_recommendation,
    "get_latest_recommendation": _get_latest_recommendation,
}

TOOL_DEFINITIONS = {
    "get_summary": {
        "name": "get_summary",
        "description": "Get spending summary with totals broken down by category and account. Supports optional date range and filters.",
        "parameters": {
            "type": "object",
            "properties": {
                "date_from": {"type": "string", "description": "Start date YYYY-MM-DD"},
                "date_to": {"type": "string", "description": "End date YYYY-MM-DD"},
                "account_ids": {"type": "array", "items": {"type": "string"}, "description": "Filter by account UUIDs"},
                "category_ids": {"type": "array", "items": {"type": "string"}, "description": "Filter by category UUIDs"},
            },
        },
    },
    "get_trends": {
        "name": "get_trends",
        "description": "Get spending trends over time grouped by day, week, or month. Requires date_from and date_to.",
        "parameters": {
            "type": "object",
            "properties": {
                "date_from": {"type": "string", "description": "Start date YYYY-MM-DD"},
                "date_to": {"type": "string", "description": "End date YYYY-MM-DD"},
                "group_by": {"type": "string", "enum": ["day", "week", "month"], "description": "Grouping period"},
            },
            "required": ["date_from", "date_to"],
        },
    },
    "get_budget_vs_actual": {
        "name": "get_budget_vs_actual",
        "description": "Compare actual spending against budget limits per category for a specific budget.",
        "parameters": {
            "type": "object",
            "properties": {
                "budget_id": {"type": "string", "description": "Budget UUID"},
            },
            "required": ["budget_id"],
        },
    },
    "list_budgets": {
        "name": "list_budgets",
        "description": "List the user's budgets with optional period filter.",
        "parameters": {
            "type": "object",
            "properties": {
                "period_from": {"type": "string", "description": "Filter budgets overlapping this start date YYYY-MM-DD"},
                "period_to": {"type": "string", "description": "Filter budgets overlapping this end date YYYY-MM-DD"},
            },
        },
    },
    "get_budget": {
        "name": "get_budget",
        "description": "Get details of a specific budget including items and thresholds.",
        "parameters": {
            "type": "object",
            "properties": {
                "budget_id": {"type": "string", "description": "Budget UUID"},
            },
            "required": ["budget_id"],
        },
    },
    "list_alerts": {
        "name": "list_alerts",
        "description": "List budget alerts (threshold breach notifications). Optionally filter by read status.",
        "parameters": {
            "type": "object",
            "properties": {
                "is_read": {"type": "boolean", "description": "Filter by read status"},
            },
        },
    },
    "list_transactions": {
        "name": "list_transactions",
        "description": "List recent transactions with optional date range and filters. Returns up to 50 rows.",
        "parameters": {
            "type": "object",
            "properties": {
                "date_from": {"type": "string", "description": "Start date YYYY-MM-DD"},
                "date_to": {"type": "string", "description": "End date YYYY-MM-DD"},
                "account_ids": {"type": "array", "items": {"type": "string"}, "description": "Filter by account UUIDs"},
                "category_ids": {"type": "array", "items": {"type": "string"}, "description": "Filter by category UUIDs"},
                "limit": {"type": "integer", "description": "Max results (default 50, max 100)"},
            },
        },
    },
    "run_recommendation": {
        "name": "run_recommendation",
        "description": "Run the investment recommendation engine. Returns safety gates, risk bucket, allocation, and projection. If user has no risk profile, returns needs_profile=true with the 5 questions to ask. If safety gates fail, returns stabilization action items instead of allocation.",
        "parameters": {
            "type": "object",
            "properties": {
                "horizon_months": {"type": "integer", "description": "Investment horizon in months (6-360). Default 60."},
                "answers": {
                    "type": "object",
                    "description": "Risk profile answers (each 1-5): market_drop_reaction, investment_experience, income_stability, loss_tolerance_pct, goal_priority. Omit if unknown.",
                    "properties": {
                        "market_drop_reaction": {"type": "integer"},
                        "investment_experience": {"type": "integer"},
                        "income_stability": {"type": "integer"},
                        "loss_tolerance_pct": {"type": "integer"},
                        "goal_priority": {"type": "integer"},
                    },
                },
                "liquidity_need": {"type": "string", "enum": ["low", "moderate", "high"], "description": "How soon user may need cash"},
            },
        },
    },
    "get_latest_recommendation": {
        "name": "get_latest_recommendation",
        "description": "Get the most recent recommendation run results including gates, risk bucket, allocation, and action items. Returns error if no runs exist.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
}


async def execute_tool(name: str, db: AsyncSession, user_id: uuid.UUID, args: dict) -> dict:
    fn = _TOOL_FUNCTIONS.get(name)
    if not fn:
        return {"error": f"Unknown tool: {name}"}
    try:
        return await fn(db, user_id, args)
    except Exception as exc:
        return {"error": str(exc)[:300]}
