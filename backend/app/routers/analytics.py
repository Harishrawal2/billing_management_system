from datetime import date, datetime, timedelta, timezone
from typing import Dict, List
from collections import defaultdict
from fastapi import APIRouter, Depends
from prisma import Prisma

from backend.app.db import get_db
from backend.app.schemas.analytics import DashboardSummary, MonthlyData
from backend.app.routers.invoices import invoice_to_summary
from backend.app.routers.payments import payment_to_out

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(db: Prisma = Depends(get_db)):
    today_dt = datetime.now(timezone.utc)

    # 1. Total revenue
    all_payments = await db.payment.find_many(order={"id": "desc"})
    total_revenue = round(sum(p.amount for p in all_payments), 2)

    # 2. Invoices
    active_invoices = await db.invoice.find_many(
        where={"status": {"not": "CANCELLED"}},
        include={"client": True}
    )
    total_invoiced = round(sum(inv.total_amount for inv in active_invoices), 2)
    outstanding_receivables = round(sum(inv.balance_due for inv in active_invoices), 2)

    # Overdue
    overdue_amount = round(
        sum(inv.balance_due for inv in active_invoices if inv.due_date < today_dt and inv.balance_due > 0),
        2
    )

    total_clients = await db.client.count()
    total_invoices = len(active_invoices)

    # Status breakdown
    status_counts = defaultdict(int)
    for inv in active_invoices:
        status_counts[inv.status] += 1

    for st in ["DRAFT", "SENT", "PARTIAL", "PAID", "OVERDUE"]:
        if st not in status_counts:
            status_counts[st] = 0

    # Monthly Trend (Past 6 calendar months)
    monthly_map = {}
    for i in range(5, -1, -1):
        m_date = today_dt.replace(day=1) - timedelta(days=i * 28)
        m_key = m_date.strftime("%b %Y")
        monthly_map[m_key] = {"billed": 0.0, "received": 0.0}

    for inv in active_invoices:
        m_key = inv.issue_date.strftime("%b %Y")
        if m_key in monthly_map:
            monthly_map[m_key]["billed"] += inv.total_amount

    for pay in all_payments:
        m_key = pay.payment_date.strftime("%b %Y")
        if m_key in monthly_map:
            monthly_map[m_key]["received"] += pay.amount

    monthly_trend = [
        MonthlyData(
            month=k,
            billed=round(v["billed"], 2),
            received=round(v["received"], 2)
        )
        for k, v in monthly_map.items()
    ]

    # Recent invoices
    recent_invoices_db = await db.invoice.find_many(
        include={"client": True},
        order={"id": "desc"},
        take=5
    )
    recent_invoices = [invoice_to_summary(inv) for inv in recent_invoices_db]

    # Recent payments
    recent_payments_db = await db.payment.find_many(
        include={"invoice": {"include": {"client": True}}},
        order={"id": "desc"},
        take=5
    )
    recent_payments = [payment_to_out(p) for p in recent_payments_db]

    return DashboardSummary(
        total_revenue=total_revenue,
        total_invoiced=total_invoiced,
        outstanding_receivables=outstanding_receivables,
        overdue_amount=overdue_amount,
        total_clients=total_clients,
        total_invoices=total_invoices,
        invoices_by_status=dict(status_counts),
        monthly_trend=monthly_trend,
        recent_invoices=recent_invoices,
        recent_payments=recent_payments,
    )
