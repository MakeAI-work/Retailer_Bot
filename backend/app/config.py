from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "WhatsApp Retailer Bots"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL: str = "postgresql://username:password@localhost:5432/whatsapp_retailer_db"
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "whatsapp_retailer_db"
    DATABASE_USER: str = "postgres"
    DATABASE_PASSWORD: str = "password"
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-here-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # WhatsApp API
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID_INVENTORY: str = ""
    WHATSAPP_PHONE_NUMBER_ID_INVOICE: str = ""
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: str = ""
    WHATSAPP_API_VERSION: str = "v18.0"
    WHATSAPP_API_BASE_URL: str = "https://graph.facebook.com"
    
    # File Storage
    INVOICE_STORAGE_PATH: str = "./storage/invoices"
    MAX_FILE_SIZE_MB: int = 10
    
    # Session Management
    SESSION_EXPIRE_HOURS: int = 24
    CLEANUP_EXPIRED_SESSIONS_HOURS: int = 1
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create storage directory if it doesn't exist
        os.makedirs(self.INVOICE_STORAGE_PATH, exist_ok=True)
    
    @property
    def database_url(self) -> str:
        """Construct database URL from components if DATABASE_URL is not set properly"""
        if self.DATABASE_URL and self.DATABASE_URL != "postgresql://username:password@localhost:5432/whatsapp_retailer_db":
            return self.DATABASE_URL
        return f"postgresql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"


settings = Settings()
