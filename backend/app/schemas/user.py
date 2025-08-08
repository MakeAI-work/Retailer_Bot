from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    whatsapp_number: str = Field(..., min_length=10, max_length=20)

    @validator('whatsapp_number')
    def validate_whatsapp_number(cls, v):
        # Remove any non-digit characters
        digits_only = ''.join(filter(str.isdigit, v))
        if len(digits_only) < 10:
            raise ValueError('WhatsApp number must have at least 10 digits')
        return digits_only


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    whatsapp_number: Optional[str] = Field(None, min_length=10, max_length=20)
    is_active: Optional[bool] = None

    @validator('whatsapp_number')
    def validate_whatsapp_number(cls, v):
        if v is not None:
            digits_only = ''.join(filter(str.isdigit, v))
            if len(digits_only) < 10:
                raise ValueError('WhatsApp number must have at least 10 digits')
            return digits_only
        return v


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    whatsapp_number: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    user_id: Optional[int] = None
