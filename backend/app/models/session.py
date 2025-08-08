from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from datetime import datetime, timedelta

from app.database import Base


class BotType(enum.Enum):
    INVENTORY = "inventory"
    INVOICE = "invoice"


class WhatsAppSession(Base):
    __tablename__ = "whatsapp_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    whatsapp_number = Column(String(20), nullable=False)
    session_token = Column(String(255), unique=True, index=True, nullable=False)
    bot_type = Column(Enum(BotType), nullable=False)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="sessions")

    def __repr__(self):
        return f"<WhatsAppSession(id={self.id}, user_id={self.user_id}, bot_type='{self.bot_type.value}', active={self.is_active})>"

    @property
    def is_expired(self) -> bool:
        """Check if session has expired"""
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if session is valid (active and not expired)"""
        return self.is_active and not self.is_expired

    @property
    def time_until_expiry(self) -> timedelta:
        """Get time remaining until session expires"""
        return self.expires_at - datetime.utcnow()

    def extend_session(self, hours: int = 24):
        """Extend session expiry time"""
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
        self.last_activity = datetime.utcnow()

    def deactivate(self):
        """Deactivate the session"""
        self.is_active = False
