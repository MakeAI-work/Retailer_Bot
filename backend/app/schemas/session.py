from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum

from app.models.session import BotType


class BotTypeEnum(str, Enum):
    INVENTORY = "inventory"
    INVOICE = "invoice"


class SessionBase(BaseModel):
    whatsapp_number: str = Field(..., min_length=10, max_length=20)
    bot_type: BotTypeEnum

    @validator('whatsapp_number')
    def validate_whatsapp_number(cls, v):
        digits_only = ''.join(filter(str.isdigit, v))
        if len(digits_only) < 10:
            raise ValueError('WhatsApp number must have at least 10 digits')
        return digits_only


class SessionCreate(SessionBase):
    user_id: int
    expires_at: Optional[datetime] = None

    @validator('expires_at', pre=True, always=True)
    def set_default_expiry(cls, v):
        if v is None:
            return datetime.utcnow() + timedelta(hours=24)
        return v


class SessionUpdate(BaseModel):
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None


class SessionResponse(SessionBase):
    id: int
    user_id: int
    session_token: str
    is_active: bool
    is_expired: bool
    is_valid: bool
    expires_at: datetime
    created_at: datetime
    last_activity: datetime
    time_until_expiry: timedelta

    class Config:
        from_attributes = True


class SessionLogin(BaseModel):
    whatsapp_number: str
    password: str
    bot_type: BotTypeEnum

    @validator('whatsapp_number')
    def validate_whatsapp_number(cls, v):
        digits_only = ''.join(filter(str.isdigit, v))
        if len(digits_only) < 10:
            raise ValueError('WhatsApp number must have at least 10 digits')
        return digits_only


class SessionToken(BaseModel):
    session_token: str
    bot_type: BotTypeEnum
    expires_at: datetime
    expires_in_seconds: int

    @validator('expires_in_seconds', pre=True, always=True)
    def calculate_expires_in(cls, v, values):
        if 'expires_at' in values:
            delta = values['expires_at'] - datetime.utcnow()
            return int(delta.total_seconds())
        return v


class SessionValidation(BaseModel):
    session_token: str
    whatsapp_number: str
    bot_type: BotTypeEnum
