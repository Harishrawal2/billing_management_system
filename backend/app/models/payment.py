import enum
from datetime import datetime, date, timezone
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Date, ForeignKey, Enum
from sqlalchemy.orm import relationship
from backend.app.database import Base

class PaymentMethod(str, enum.Enum):
    CASH = "CASH"
    BANK_TRANSFER = "BANK_TRANSFER"
    CARD = "CARD"
    UPI = "UPI"
    CHEQUE = "CHEQUE"
    OTHER = "OTHER"

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_date = Column(Date, default=date.today, nullable=False)
    payment_method = Column(String(50), default=PaymentMethod.BANK_TRANSFER.value, nullable=False)
    reference_number = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    invoice = relationship("Invoice", back_populates="payments")
