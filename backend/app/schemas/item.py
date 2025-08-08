from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional


class ItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    quantity: int = Field(..., ge=0)
    price: float = Field(..., gt=0)
    description: Optional[str] = Field(None, max_length=255)

    @validator('price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Price must be greater than 0')
        return round(v, 2)


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    quantity: Optional[int] = Field(None, ge=0)
    price: Optional[float] = Field(None, gt=0)
    description: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None

    @validator('price')
    def validate_price(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Price must be greater than 0')
        return round(v, 2) if v is not None else v


class ItemResponse(ItemBase):
    id: int
    is_active: bool
    is_low_stock: bool
    is_out_of_stock: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ItemStockUpdate(BaseModel):
    quantity: int = Field(..., ge=0)
    operation: str = Field(..., regex="^(set|add|subtract)$")

    @validator('operation')
    def validate_operation(cls, v):
        if v not in ['set', 'add', 'subtract']:
            raise ValueError('Operation must be one of: set, add, subtract')
        return v


class ItemSearch(BaseModel):
    name: Optional[str] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    low_stock_only: Optional[bool] = False
    out_of_stock_only: Optional[bool] = False
