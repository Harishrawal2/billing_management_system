import enum
from datetime import date, datetime
from typing import Optional, Union
from pydantic import BaseModel, ConfigDict

class PaymentMethod(str, enum.Enum):
    CASH = "CASH"
    BANK_TRANSFER = "BANK_TRANSFER"
    CARD = "CARD"
    UPI = "UPI"
    CHEQUE = "CHEQUE"
    OTHER = "OTHER"

class PaymentCreate(BaseModel):
    invoice_id: int
    amount: float
    payment_date: Optional[Union[date, datetime]] = None
    payment_method: PaymentMethod = PaymentMethod.BANK_TRANSFER
    reference_number: Optional[str] = None
    notes: Optional[str] = None

class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_id: int
    invoice_number: Optional[str] = None
    client_name: Optional[str] = None
    amount: float
    payment_date: Union[date, datetime]
    payment_method: str
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
