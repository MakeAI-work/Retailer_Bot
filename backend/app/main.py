from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.config import settings
from app.database import engine, Base
from app.api import auth, items, sales, webhooks


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting WhatsApp Retailer Bots API...")
    # Create database tables
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown
    print("Shutting down WhatsApp Retailer Bots API...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="WhatsApp Inventory & Invoice Bots API",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(items.router, prefix="/api/items", tags=["inventory"])
app.include_router(sales.router, prefix="/api/sales", tags=["sales"])
app.include_router(webhooks.router, prefix="/webhook", tags=["whatsapp"])


@app.get("/")
async def root():
    return {
        "message": "WhatsApp Retailer Bots API",
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
