from typing import List, Dict, Optional
from pydantic import BaseModel
from backend.app.schemas.invoice import InvoiceSummary
from backend.app.schemas.payment import PaymentOut

class MonthlyData(BaseModel):
    month: str
    billed: float
    received: float

class DashboardSummary(BaseModel):
    total_revenue: float
    total_invoiced: float
    outstanding_receivables: float
    overdue_amount: float
    total_clients: int
    total_invoices: int
    invoices_by_status: Dict[str, int]
    monthly_trend: List[MonthlyData]
    recent_invoices: List[InvoiceSummary]
    recent_payments: List[PaymentOut]
