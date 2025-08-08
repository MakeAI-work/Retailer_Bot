from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class SaleStatus(enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String(100), nullable=False)
    items_sold_json = Column(Text, nullable=False)  # JSON string of items and quantities
    total_amount = Column(Float, nullable=False)
    pdf_path = Column(String(255), nullable=True)  # Path to generated PDF invoice
    status = Column(Enum(SaleStatus), default=SaleStatus.PENDING)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="sales")

    def __repr__(self):
        return f"<Sale(id={self.id}, customer='{self.customer_name}', amount={self.total_amount}, status='{self.status.value}')>"

    @property
    def is_pending(self) -> bool:
        """Check if sale is pending retailer confirmation"""
        return self.status == SaleStatus.PENDING

    @property
    def is_completed(self) -> bool:
        """Check if sale is successfully completed"""
        return self.status == SaleStatus.SUCCESS
