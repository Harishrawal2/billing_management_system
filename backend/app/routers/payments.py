from typing import List, Optional
from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from prisma import Prisma
from backend.app.db import get_db
from backend.app.schemas.payment import PaymentCreate, PaymentOut
from backend.app.services.billing_service import get_status_on_balance

router = APIRouter(prefix="/api/payments", tags=["Payments"])

def payment_to_out(payment) -> dict:
    inv = payment.invoice if hasattr(payment, "invoice") else None
    client = inv.client if inv and hasattr(inv, "client") else None
    return {
        "id": payment.id,
        "invoice_id": payment.invoice_id,
        "invoice_number": inv.invoice_number if inv else "",
        "client_name": client.name if client else "Unknown",
        "amount": payment.amount,
        "payment_date": payment.payment_date,
        "payment_method": payment.payment_method,
        "reference_number": payment.reference_number,
        "notes": payment.notes,
        "created_at": payment.created_at,
    }

@router.get("", response_model=List[PaymentOut])
async def get_payments(
    invoice_id: Optional[int] = Query(None),
    db: Prisma = Depends(get_db)
):
    where = {}
    if invoice_id:
        where["invoice_id"] = invoice_id
        
    payments = await db.payment.find_many(
        where=where if where else None,
        include={"invoice": {"include": {"client": True}}},
        order={"id": "desc"}
    )
    return [payment_to_out(p) for p in payments]

@router.post("", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
async def record_payment(payment_in: PaymentCreate, db: Prisma = Depends(get_db)):
    invoice = await db.invoice.find_unique(
        where={"id": payment_in.invoice_id},
        include={"client": True}
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.status == "CANCELLED":
        raise HTTPException(status_code=400, detail="Cannot record payment on a cancelled invoice")

    if payment_in.amount <= 0:
        raise HTTPException(status_code=400, detail="Payment amount must be greater than zero")

    if round(payment_in.amount, 2) > round(invoice.balance_due, 2):
        raise HTTPException(
            status_code=400,
            detail=f"Payment amount (${payment_in.amount:.2f}) exceeds balance due (${invoice.balance_due:.2f})"
        )

    # Dates
    if payment_in.payment_date:
        if isinstance(payment_in.payment_date, datetime):
            pay_dt = payment_in.payment_date
        else:
            pay_dt = datetime.combine(payment_in.payment_date, datetime.min.time(), tzinfo=timezone.utc)
    else:
        pay_dt = datetime.now(timezone.utc)

    payment = await db.payment.create(
        data={
            "invoice_id": invoice.id,
            "amount": round(payment_in.amount, 2),
            "payment_date": pay_dt,
            "payment_method": payment_in.payment_method.value,
            "reference_number": payment_in.reference_number,
            "notes": payment_in.notes
        },
        include={"invoice": {"include": {"client": True}}}
    )

    # Update invoice financials
    new_paid = round(invoice.paid_amount + payment.amount, 2)
    new_balance = max(0.0, round(invoice.total_amount - new_paid, 2))
    new_status = get_status_on_balance(
        balance_due=new_balance,
        total_amount=invoice.total_amount,
        paid_amount=new_paid,
        due_date=invoice.due_date,
        current_status=invoice.status
    )

    await db.invoice.update(
        where={"id": invoice.id},
        data={
            "paid_amount": new_paid,
            "balance_due": new_balance,
            "status": new_status
        }
    )

    return payment_to_out(payment)
