from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ClientBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None

class ClientCreate(ClientBase):
    pass

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None

class ClientOut(ClientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    total_invoiced: Optional[float] = 0.0
    total_paid: Optional[float] = 0.0
    balance_due: Optional[float] = 0.0
    invoice_count: Optional[int] = 0
