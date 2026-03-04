import io
from datetime import datetime
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer


def _fmt(val) -> str:
    if isinstance(val, Decimal):
        return f"${float(val):,.2f}"
    if val is None:
        return "-"
    return str(val)


def _build_table(headers: list[str], rows: list[list[str]]) -> Table:
    data = [headers] + rows
    t = Table(data, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d4d4d4")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def _make_doc(report_type: str, from_date: str, to_date: str, elements: list) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, topMargin=0.5 * inch, bottomMargin=0.5 * inch)
    styles = getSampleStyleSheet()

    story = [
        Paragraph(f"BudgetFlow Report: {report_type.replace('_', ' ').title()}", styles["Title"]),
        Paragraph(f"Period: {from_date} to {to_date}", styles["Normal"]),
        Spacer(1, 12),
    ]
    story.extend(elements)
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", styles["Italic"]))

    doc.build(story)
    return buf.getvalue()


def render_monthly_summary(data: dict, from_date: str, to_date: str) -> bytes:
    styles = getSampleStyleSheet()
    elements = [
        Paragraph(f"Total Spending: {_fmt(data['total_spending'])}", styles["Heading2"]),
        Spacer(1, 8),
    ]
    if data.get("by_category"):
        elements.append(Paragraph("By Category", styles["Heading3"]))
        rows = [[r["category_id"] or "Uncategorized", _fmt(r["total"])] for r in data["by_category"]]
        elements.append(_build_table(["Category", "Amount"], rows))
        elements.append(Spacer(1, 8))
    if data.get("by_account"):
        elements.append(Paragraph("By Account", styles["Heading3"]))
        rows = [[r["account_id"], _fmt(r["total"])] for r in data["by_account"]]
        elements.append(_build_table(["Account", "Amount"], rows))
    return _make_doc("monthly_summary", from_date, to_date, elements)


def render_category_breakdown(rows: list, from_date: str, to_date: str) -> bytes:
    styles = getSampleStyleSheet()
    elements = [Paragraph("Spending by Category", styles["Heading3"])]
    table_rows = [[r["category_id"] or "Uncategorized", _fmt(r["total"])] for r in rows]
    elements.append(_build_table(["Category", "Amount"], table_rows))
    return _make_doc("category_breakdown", from_date, to_date, elements)


def render_budget_vs_actual(rows: list, from_date: str, to_date: str) -> bytes:
    styles = getSampleStyleSheet()
    elements = [Paragraph("Budget vs Actual", styles["Heading3"])]
    table_rows = [
        [r["category_id"], _fmt(r["limit_amount"]), _fmt(r["spent_amount"]), f"{float(r['percent']) * 100:.0f}%"]
        for r in rows
    ]
    elements.append(_build_table(["Category", "Limit", "Spent", "Used %"], table_rows))
    return _make_doc("budget_vs_actual", from_date, to_date, elements)


def render_transactions(transactions: list, from_date: str, to_date: str) -> bytes:
    styles = getSampleStyleSheet()
    capped = transactions[:200]
    elements = [Paragraph(f"Transactions ({len(capped)} of {len(transactions)})", styles["Heading3"])]
    table_rows = [
        [t["posted_date"], t["description"][:60], _fmt(t["amount"]), t["currency"]]
        for t in capped
    ]
    elements.append(_build_table(["Date", "Description", "Amount", "Currency"], table_rows))
    return _make_doc("transactions", from_date, to_date, elements)
