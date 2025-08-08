from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func

from app.database import Base


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=0)
    price = Column(Float, nullable=False)
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Item(id={self.id}, name='{self.name}', quantity={self.quantity}, price={self.price})>"

    @property
    def is_low_stock(self) -> bool:
        """Check if item is low on stock (less than 10 units)"""
        return self.quantity < 10

    @property
    def is_out_of_stock(self) -> bool:
        """Check if item is out of stock"""
        return self.quantity <= 0
