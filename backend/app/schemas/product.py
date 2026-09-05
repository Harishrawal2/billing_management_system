from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ProductBase(BaseModel):
    name: str
    sku: Optional[str] = None
    description: Optional[str] = None
    unit_price: float = 0.0
    tax_rate: float = 0.0
    unit: str = "item"
    is_active: bool = True

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    description: Optional[str] = None
    unit_price: Optional[float] = None
    tax_rate: Optional[float] = None
    unit: Optional[str] = None
    is_active: Optional[bool] = None

class ProductOut(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
