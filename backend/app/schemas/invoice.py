import enum
from datetime import date, datetime
from typing import List, Optional, Union
from pydantic import BaseModel, ConfigDict
from backend.app.schemas.client import ClientOut

class InvoiceStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    PARTIAL = "PARTIAL"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"

class DiscountType(str, enum.Enum):
    PERCENTAGE = "PERCENTAGE"
    FIXED = "FIXED"

class InvoiceItemBase(BaseModel):
    product_id: Optional[int] = None
    description: str
    quantity: float = 1.0
    unit_price: float = 0.0
    tax_rate: float = 0.0  # %
    discount: float = 0.0  # %

class InvoiceItemCreate(InvoiceItemBase):
    pass

class InvoiceItemOut(InvoiceItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_id: int
    line_total: float

class InvoiceBase(BaseModel):
    client_id: int
    issue_date: Optional[Union[date, datetime]] = None
    due_date: Union[date, datetime]
    discount_type: DiscountType = DiscountType.PERCENTAGE
    discount_value: float = 0.0
    notes: Optional[str] = None
    payment_terms: str = "Net 30"

class InvoiceCreate(InvoiceBase):
    items: List[InvoiceItemCreate]

class InvoiceUpdate(BaseModel):
    client_id: Optional[int] = None
    issue_date: Optional[Union[date, datetime]] = None
    due_date: Optional[Union[date, datetime]] = None
    discount_type: Optional[DiscountType] = None
    discount_value: Optional[float] = None
    notes: Optional[str] = None
    payment_terms: Optional[str] = None
    items: Optional[List[InvoiceItemCreate]] = None

class InvoiceStatusUpdate(BaseModel):
    status: InvoiceStatus

class InvoiceSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_number: str
    client_id: int
    client_name: Optional[str] = None
    client_company: Optional[str] = None
    status: str
    issue_date: Union[date, datetime]
    due_date: Union[date, datetime]
    total_amount: float
    paid_amount: float
    balance_due: float
    created_at: datetime

class PaymentBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: float
    payment_date: Union[date, datetime]
    payment_method: str
    reference_number: Optional[str] = None

class InvoiceDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_number: str
    client_id: int
    client: ClientOut
    status: str
    issue_date: Union[date, datetime]
    due_date: Union[date, datetime]
    subtotal: float
    discount_type: str
    discount_value: float
    discount_amount: float
    tax_amount: float
    total_amount: float
    paid_amount: float
    balance_due: float
    notes: Optional[str] = None
    payment_terms: str
    created_at: datetime
    updated_at: datetime
    items: List[InvoiceItemOut]
    payments: List[PaymentBrief] = []
