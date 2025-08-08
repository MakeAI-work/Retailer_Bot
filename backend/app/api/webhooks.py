from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database import get_db
from app.models import User
from app.config import settings

router = APIRouter()


@router.get("/inventory")
def verify_inventory_webhook(
    hub_mode: str = None,
    hub_verify_token: str = None,
    hub_challenge: str = None
):
    """Verify WhatsApp webhook for inventory bot"""
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN:
        return int(hub_challenge)
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid verification token"
        )


@router.get("/invoice")
def verify_invoice_webhook(
    hub_mode: str = None,
    hub_verify_token: str = None,
    hub_challenge: str = None
):
    """Verify WhatsApp webhook for invoice bot"""
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN:
        return int(hub_challenge)
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid verification token"
        )


@router.post("/inventory")
async def inventory_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle WhatsApp messages for inventory management bot
    
    This endpoint will be implemented in Phase 4.
    Expected commands:
    - "add item_name quantity price" - Add new item
    - "update item_name quantity" - Update stock quantity  
    - "view" - View all items
    - "stock item_name" - Check specific item stock
    """
    body = await request.json()
    
    # TODO: Implement in Phase 4
    # 1. Parse incoming WhatsApp message
    # 2. Validate user session
    # 3. Process inventory commands
    # 4. Send response via WhatsApp
    
    return {"status": "received", "message": "Inventory webhook - Implementation pending Phase 4"}


@router.post("/invoice")
async def invoice_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle WhatsApp messages for invoice generation bot
    
    This endpoint will be implemented in Phase 4.
    Expected format: "customer_name: item_name: quantity"
    Example: "raghav: natraj pencils: 2"
    
    Bot workflow:
    1. Parse message format
    2. Create sale record
    3. Generate PDF invoice
    4. Send PDF to retailer
    5. Wait for "success" or "fail" response
    6. Update stock accordingly
    """
    body = await request.json()
    
    # TODO: Implement in Phase 4
    # 1. Parse incoming WhatsApp message
    # 2. Validate message format (customer_name: item_name: quantity)
    # 3. Create sale record using /sales/from-whatsapp endpoint
    # 4. Generate PDF invoice (Phase 5)
    # 5. Send PDF via WhatsApp
    # 6. Handle retailer response (success/fail)
    # 7. Update sale status and stock
    
    return {"status": "received", "message": "Invoice webhook - Implementation pending Phase 4"}


@router.post("/test")
def test_webhook(payload: Dict[Any, Any]):
    """Test endpoint for webhook development and debugging"""
    return {
        "status": "success",
        "received_payload": payload,
        "message": "Test webhook received successfully"
    }
