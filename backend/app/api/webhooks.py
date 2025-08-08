from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse
import logging
from typing import Dict, Any

from app.config import settings
from app.whatsapp import whatsapp_client, inventory_bot, invoice_bot

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["webhooks"])


def verify_webhook_signature(payload: str, signature: str) -> bool:
    """Verify WhatsApp webhook signature"""
    import hmac
    import hashlib
    
    if not signature.startswith("sha256="):
        return False
    
    expected_signature = hmac.new(
        settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    received_signature = signature[7:]  # Remove 'sha256=' prefix
    return hmac.compare_digest(expected_signature, received_signature)


@router.get("/inventory")
async def verify_inventory_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_challenge: str = Query(alias="hub.challenge"), 
    hub_verify_token: str = Query(alias="hub.verify_token")
):
    """Verify inventory bot webhook endpoint"""
    logger.info(f"Inventory webhook verification - Mode: {hub_mode}, Token: {hub_verify_token}")
    
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN:
        logger.info("Inventory webhook verified successfully")
        return PlainTextResponse(hub_challenge)
    
    logger.warning("Inventory webhook verification failed")
    raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/inventory")
async def handle_inventory_webhook(request: Request):
    """Handle incoming messages for inventory bot"""
    try:
        # Get request body and headers
        body = await request.body()
        signature = request.headers.get("X-Hub-Signature-256", "")
        
        # Verify signature (optional - enable in production)
        # if not verify_webhook_signature(body.decode(), signature):
        #     raise HTTPException(status_code=403, detail="Invalid signature")
        
        # Parse JSON payload
        import json
        payload = json.loads(body.decode())
        
        logger.info(f"Inventory webhook received: {payload}")
        
        # Parse message data
        message_data = whatsapp_client.parse_webhook_payload(payload)
        
        if not message_data:
            logger.info("No valid message data found in payload")
            return {"status": "ok", "message": "No message to process"}
        
        # Only process text messages
        if message_data.get("type") != "text":
            logger.info(f"Ignoring non-text message type: {message_data.get('type')}")
            return {"status": "ok", "message": "Non-text message ignored"}
        
        # Handle message with inventory bot
        result = await inventory_bot.handle_message(message_data)
        
        logger.info(f"Inventory bot result: {result}")
        return {"status": "ok", "result": result}
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in inventory webhook: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    except Exception as e:
        logger.error(f"Error processing inventory webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/invoice")
async def verify_invoice_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_challenge: str = Query(alias="hub.challenge"),
    hub_verify_token: str = Query(alias="hub.verify_token")
):
    """Verify invoice bot webhook endpoint"""
    logger.info(f"Invoice webhook verification - Mode: {hub_mode}, Token: {hub_verify_token}")
    
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN:
        logger.info("Invoice webhook verified successfully")
        return PlainTextResponse(hub_challenge)
    
    logger.warning("Invoice webhook verification failed")
    raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/invoice")
async def handle_invoice_webhook(request: Request):
    """Handle incoming messages for invoice bot"""
    try:
        # Get request body and headers
        body = await request.body()
        signature = request.headers.get("X-Hub-Signature-256", "")
        
        # Verify signature (optional - enable in production)
        # if not verify_webhook_signature(body.decode(), signature):
        #     raise HTTPException(status_code=403, detail="Invalid signature")
        
        # Parse JSON payload
        import json
        payload = json.loads(body.decode())
        
        logger.info(f"Invoice webhook received: {payload}")
        
        # Parse message data
        message_data = whatsapp_client.parse_webhook_payload(payload)
        
        if not message_data:
            logger.info("No valid message data found in payload")
            return {"status": "ok", "message": "No message to process"}
        
        # Only process text messages
        if message_data.get("type") != "text":
            logger.info(f"Ignoring non-text message type: {message_data.get('type')}")
            return {"status": "ok", "message": "Non-text message ignored"}
        
        # Handle message with invoice bot
        result = await invoice_bot.handle_message(message_data)
        
        logger.info(f"Invoice bot result: {result}")
        return {"status": "ok", "result": result}
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in invoice webhook: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    except Exception as e:
        logger.error(f"Error processing invoice webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/test")
async def test_webhook():
    """Test webhook endpoint for development"""
    return {
        "status": "ok",
        "message": "Webhook endpoints are working",
        "bots": {
            "inventory": "Ready",
            "invoice": "Ready"
        }
    }
