from datetime import date, datetime
from typing import List, Tuple, Any
from prisma import Prisma
from prisma.enums import InvoiceStatus, DiscountType
from backend.app.schemas.invoice import InvoiceItemCreate
from backend.app.config import settings

async def generate_invoice_number(db: Prisma) -> str:
    """Generate sequential invoice number: e.g., INV-2026-0001"""
    current_year = date.today().year
    prefix = f"{settings.INVOICE_PREFIX}-{current_year}-"
    
    last_inv = await db.invoice.find_first(
        where={"invoice_number": {"startswith": prefix}},
        order={"id": "desc"}
    )
    
    if last_inv:
        try:
            last_seq = int(last_inv.invoice_number.split("-")[-1])
            new_seq = last_seq + 1
        except (ValueError, IndexError):
            new_seq = (await db.invoice.count()) + 1
    else:
        new_seq = 1
        
    return f"{prefix}{new_seq:04d}"

def calculate_item_totals(item: InvoiceItemCreate) -> Tuple[float, float, float]:
    """
    Returns: (raw_subtotal, tax_amount, line_total)
    """
    raw_subtotal = round(item.quantity * item.unit_price, 2)
    discount_amount = round(raw_subtotal * (item.discount / 100.0), 2)
    taxable_amount = max(0.0, raw_subtotal - discount_amount)
    tax_amount = round(taxable_amount * (item.tax_rate / 100.0), 2)
    line_total = round(taxable_amount + tax_amount, 2)
    return raw_subtotal, tax_amount, line_total

def calculate_invoice_totals(
    items_data: List[InvoiceItemCreate],
    discount_type: Any,
    discount_value: float,
    current_paid: float = 0.0
) -> dict:
    """
    Computes all invoice totals accurately.
    """
    subtotal = 0.0
    total_item_taxes = 0.0
    
    for item in items_data:
        raw_sub, item_tax, line_tot = calculate_item_totals(item)
        subtotal += raw_sub
        total_item_taxes += item_tax

    subtotal = round(subtotal, 2)
    
    # Overall invoice discount
    disc_type_str = str(discount_type).upper()
    if "PERCENTAGE" in disc_type_str:
        discount_amount = round(subtotal * (discount_value / 100.0), 2)
    else:
        discount_amount = min(round(discount_value, 2), subtotal)
        
    discount_amount = max(0.0, discount_amount)
    tax_amount = round(total_item_taxes, 2)
    total_amount = max(0.0, round(subtotal - discount_amount + tax_amount, 2))
    paid_amount = round(current_paid, 2)
    balance_due = max(0.0, round(total_amount - paid_amount, 2))

    return {
        "subtotal": subtotal,
        "discount_amount": discount_amount,
        "tax_amount": tax_amount,
        "total_amount": total_amount,
        "paid_amount": paid_amount,
        "balance_due": balance_due,
    }

def get_status_on_balance(balance_due: float, total_amount: float, paid_amount: float, due_date: Any, current_status: str) -> str:
    """
    Determines status based on balance and due date.
    """
    today_dt = date.today()
    if isinstance(due_date, datetime):
        due_d = due_date.date()
    elif isinstance(due_date, date):
        due_d = due_date
    else:
        due_d = today_dt

    if balance_due <= 0.001 and total_amount > 0:
        return "PAID"
    elif paid_amount > 0:
        return "PARTIAL"
    elif due_d < today_dt and current_status not in ("PAID", "CANCELLED"):
        return "OVERDUE"
    return current_status
