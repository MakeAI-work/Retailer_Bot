from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from app.models.sale import SaleStatus


class SaleStatusEnum(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SaleItemData(BaseModel):
    item_name: str
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., gt=0)
    total_price: float = Field(..., gt=0)


class SaleBase(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=100)
    total_amount: float = Field(..., gt=0)

    @validator('total_amount')
    def validate_total_amount(cls, v):
        if v <= 0:
            raise ValueError('Total amount must be greater than 0')
        return round(v, 2)


class SaleCreate(SaleBase):
    items_sold: List[SaleItemData] = Field(..., min_items=1)

    @validator('items_sold')
    def validate_items_sold(cls, v):
        if not v:
            raise ValueError('At least one item must be sold')
        return v


class SaleUpdate(BaseModel):
    status: Optional[SaleStatusEnum] = None
    pdf_path: Optional[str] = None


class SaleResponse(SaleBase):
    id: int
    items_sold: List[SaleItemData]
    pdf_path: Optional[str]
    status: SaleStatusEnum
    user_id: int
    is_pending: bool
    is_completed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @validator('items_sold', pre=True)
    def parse_items_sold_json(cls, v):
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v


class SaleStatusUpdate(BaseModel):
    status: SaleStatusEnum


class InvoiceRequest(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=100)
    item_name: str = Field(..., min_length=1, max_length=100)
    quantity: int = Field(..., gt=0)

    @validator('customer_name', 'item_name')
    def validate_names(cls, v):
        return v.strip().title()


class SaleSearch(BaseModel):
    customer_name: Optional[str] = None
    status: Optional[SaleStatusEnum] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_amount: Optional[float] = Field(None, ge=0)
    max_amount: Optional[float] = Field(None, ge=0)
