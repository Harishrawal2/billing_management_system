from typing import List, Optional
from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from prisma import Prisma

from backend.app.db import get_db
from backend.app.config import settings
from backend.app.schemas.invoice import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceDetail,
    InvoiceSummary,
    InvoiceStatusUpdate,
)
from backend.app.services.billing_service import (
    generate_invoice_number,
    calculate_item_totals,
    calculate_invoice_totals,
    get_status_on_balance
)

router = APIRouter(tags=["Invoices"])
templates = Jinja2Templates(directory="frontend/templates")

def invoice_to_summary(inv) -> dict:
    return {
        "id": inv.id,
        "invoice_number": inv.invoice_number,
        "client_id": inv.client_id,
        "client_name": inv.client.name if inv.client else "Unknown",
        "client_company": inv.client.company if inv.client else "",
        "status": inv.status,
        "issue_date": inv.issue_date,
        "due_date": inv.due_date,
        "total_amount": inv.total_amount,
        "paid_amount": inv.paid_amount,
        "balance_due": inv.balance_due,
        "created_at": inv.created_at,
    }

@router.get("/api/invoices", response_model=List[InvoiceSummary])
async def get_invoices(
    status: Optional[str] = Query(None),
    client_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None, description="Search by invoice number or client name"),
    db: Prisma = Depends(get_db)
):
    where = {}
    if status:
        where["status"] = status.upper()
    if client_id:
        where["client_id"] = client_id

    if search:
        where["OR"] = [
            {"invoice_number": {"contains": search, "mode": "insensitive"}},
            {"client": {"name": {"contains": search, "mode": "insensitive"}}},
            {"client": {"company": {"contains": search, "mode": "insensitive"}}},
        ]

    invoices = await db.invoice.find_many(
        where=where if where else None,
        include={"client": True},
        order={"id": "desc"}
    )
    return [invoice_to_summary(inv) for inv in invoices]

@router.post("/api/invoices", response_model=InvoiceDetail, status_code=status.HTTP_201_CREATED)
async def create_invoice(invoice_in: InvoiceCreate, db: Prisma = Depends(get_db)):
    client = await db.client.find_unique(where={"id": invoice_in.client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if not invoice_in.items:
        raise HTTPException(status_code=400, detail="Invoice must contain at least one line item")

    invoice_number = await generate_invoice_number(db)
    
    # Dates to datetime for Prisma PostgreSQL
    issue_date = invoice_in.issue_date or date.today()
    issue_dt = datetime.combine(issue_date, datetime.min.time(), tzinfo=timezone.utc)
    due_dt = datetime.combine(invoice_in.due_date, datetime.min.time(), tzinfo=timezone.utc)

    # Calculate totals
    totals = calculate_invoice_totals(
        items_data=invoice_in.items,
        discount_type=invoice_in.discount_type,
        discount_value=invoice_in.discount_value,
        current_paid=0.0
    )

    items_create = []
    for item in invoice_in.items:
        _, _, line_tot = calculate_item_totals(item)
        items_create.append({
            "product_id": item.product_id,
            "description": item.description,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "tax_rate": item.tax_rate,
            "discount": item.discount,
            "line_total": line_tot
        })

    new_invoice = await db.invoice.create(
        data={
            "invoice_number": invoice_number,
            "client_id": client.id,
            "status": "SENT",
            "issue_date": issue_dt,
            "due_date": due_dt,
            "subtotal": totals["subtotal"],
            "discount_type": invoice_in.discount_type.value,
            "discount_value": invoice_in.discount_value,
            "discount_amount": totals["discount_amount"],
            "tax_amount": totals["tax_amount"],
            "total_amount": totals["total_amount"],
            "paid_amount": 0.0,
            "balance_due": totals["balance_due"],
            "notes": invoice_in.notes,
            "payment_terms": invoice_in.payment_terms,
            "items": {
                "create": items_create
            }
        },
        include={"client": True, "items": True, "payments": True}
    )

    return new_invoice

@router.get("/api/invoices/{invoice_id}", response_model=InvoiceDetail)
async def get_invoice(invoice_id: int, db: Prisma = Depends(get_db)):
    invoice = await db.invoice.find_unique(
        where={"id": invoice_id},
        include={"client": True, "items": True, "payments": True}
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@router.patch("/api/invoices/{invoice_id}/status", response_model=InvoiceDetail)
async def update_invoice_status(invoice_id: int, status_in: InvoiceStatusUpdate, db: Prisma = Depends(get_db)):
    invoice = await db.invoice.find_unique(where={"id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    updated = await db.invoice.update(
        where={"id": invoice_id},
        data={"status": status_in.status.value},
        include={"client": True, "items": True, "payments": True}
    )
    return updated

@router.delete("/api/invoices/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(invoice_id: int, db: Prisma = Depends(get_db)):
    invoice = await db.invoice.find_unique(where={"id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    await db.invoice.delete(where={"id": invoice_id})
    return None

@router.get("/invoices/{invoice_id}/print", response_class=HTMLResponse)
async def print_invoice(
    request: Request,
    invoice_id: int,
    currency: Optional[str] = Query(None),
    db: Prisma = Depends(get_db)
):
    invoice = await db.invoice.find_unique(
        where={"id": invoice_id},
        include={"client": True, "items": True, "payments": True}
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    display_currency = currency if currency else settings.DEFAULT_CURRENCY
    return templates.TemplateResponse(
        request=request,
        name="invoice_view.html",
        context={
            "invoice": invoice,
            "settings": settings,
            "currency": display_currency
        }
    )
