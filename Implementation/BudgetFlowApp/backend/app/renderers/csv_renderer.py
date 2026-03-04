import csv
import io
from decimal import Decimal


def _fmt(val) -> str:
    if isinstance(val, Decimal):
        return str(float(val))
    if val is None:
        return ""
    return str(val)


def render_monthly_summary(data: dict) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Metric", "Value"])
    w.writerow(["Total Spending", _fmt(data["total_spending"])])
    w.writerow([])
    w.writerow(["Category ID", "Amount"])
    for row in data.get("by_category", []):
        w.writerow([row["category_id"] or "Uncategorized", _fmt(row["total"])])
    w.writerow([])
    w.writerow(["Account ID", "Amount"])
    for row in data.get("by_account", []):
        w.writerow([row["account_id"], _fmt(row["total"])])
    return buf.getvalue().encode("utf-8")


def render_category_breakdown(rows: list) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Category ID", "Amount"])
    for row in rows:
        w.writerow([row["category_id"] or "Uncategorized", _fmt(row["total"])])
    return buf.getvalue().encode("utf-8")


def render_budget_vs_actual(rows: list) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Category ID", "Limit", "Spent", "Percent"])
    for row in rows:
        w.writerow([row["category_id"], _fmt(row["limit_amount"]), _fmt(row["spent_amount"]), _fmt(row["percent"])])
    return buf.getvalue().encode("utf-8")


def render_transactions(transactions: list) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Date", "Description", "Amount", "Currency", "Category ID", "Account ID"])
    for t in transactions:
        w.writerow([t["posted_date"], t["description"], _fmt(t["amount"]), t["currency"], t.get("category_id", ""), t["account_id"]])
    return buf.getvalue().encode("utf-8")
