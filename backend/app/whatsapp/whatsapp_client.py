import httpx
import json
import logging
from typing import Optional, Dict, Any
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


class WhatsAppClient:
    def __init__(self):
        self.base_url = f"{settings.WHATSAPP_API_BASE_URL}/{settings.WHATSAPP_API_VERSION}"
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    async def send_text_message(
        self, 
        phone_number_id: str, 
        to: str, 
        message: str
    ) -> Dict[Any, Any]:
        """Send a text message via WhatsApp"""
        url = f"{self.base_url}/{phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {
                "body": message
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url, 
                    headers=self.headers, 
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            raise Exception(f"WhatsApp API error: {e}")

    async def send_document(
        self, 
        phone_number_id: str, 
        to: str, 
        document_path: str,
        filename: Optional[str] = None,
        caption: Optional[str] = None
    ) -> Dict[Any, Any]:
        """Send a document via WhatsApp"""
        # First upload the document
        media_id = await self._upload_media(phone_number_id, document_path)
        
        if not media_id:
            raise Exception("Failed to upload document to WhatsApp")
        
        # Then send the document message
        url = f"{self.base_url}/{phone_number_id}/messages"
        
        document_payload = {
            "id": media_id
        }
        
        if filename:
            document_payload["filename"] = filename
        if caption:
            document_payload["caption"] = caption
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "document",
            "document": document_payload
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url, 
                    headers=self.headers, 
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to send WhatsApp document: {e}")
            raise Exception(f"WhatsApp API error: {e}")

    async def _upload_media(self, phone_number_id: str, file_path: str) -> Optional[str]:
        """Upload media file to WhatsApp and return media ID"""
        url = f"{self.base_url}/{phone_number_id}/media"
        
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            logger.error(f"File not found: {file_path}")
            return None
        
        # Determine MIME type based on file extension
        mime_type = self._get_mime_type(file_path_obj.suffix.lower())
        
        files = {
            "file": (file_path_obj.name, open(file_path, "rb"), mime_type),
            "messaging_product": (None, "whatsapp"),
            "type": (None, mime_type)
        }
        
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url, 
                    headers=headers, 
                    files=files,
                    timeout=60.0
                )
                response.raise_for_status()
                result = response.json()
                return result.get("id")
        except httpx.HTTPError as e:
            logger.error(f"Failed to upload media to WhatsApp: {e}")
            return None
        finally:
            # Close the file
            if "file" in files:
                files["file"][1].close()

    def _get_mime_type(self, extension: str) -> str:
        """Get MIME type based on file extension"""
        mime_types = {
            ".pdf": "application/pdf",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".txt": "text/plain"
        }
        return mime_types.get(extension, "application/octet-stream")

    async def send_inventory_response(self, to: str, message: str) -> Dict[Any, Any]:
        """Send response from inventory bot"""
        return await self.send_text_message(
            settings.WHATSAPP_PHONE_NUMBER_ID_INVENTORY, 
            to, 
            message
        )

    async def send_invoice_response(self, to: str, message: str) -> Dict[Any, Any]:
        """Send response from invoice bot"""
        return await self.send_text_message(
            settings.WHATSAPP_PHONE_NUMBER_ID_INVOICE, 
            to, 
            message
        )

    async def send_invoice_pdf(
        self, 
        to: str, 
        pdf_path: str, 
        filename: str,
        caption: str = "Your invoice is ready!"
    ) -> Dict[Any, Any]:
        """Send invoice PDF from invoice bot"""
        return await self.send_document(
            settings.WHATSAPP_PHONE_NUMBER_ID_INVOICE,
            to,
            pdf_path,
            filename,
            caption
        )

    def parse_webhook_payload(self, payload: Dict[Any, Any]) -> Optional[Dict[str, Any]]:
        """Parse incoming WhatsApp webhook payload"""
        try:
            if "entry" not in payload:
                return None
            
            entry = payload["entry"][0]
            if "changes" not in entry:
                return None
            
            change = entry["changes"][0]
            if change.get("field") != "messages":
                return None
            
            value = change.get("value", {})
            messages = value.get("messages", [])
            
            if not messages:
                return None
            
            message = messages[0]
            
            # Extract message details
            return {
                "message_id": message.get("id"),
                "from": message.get("from"),
                "timestamp": message.get("timestamp"),
                "type": message.get("type"),
                "text": message.get("text", {}).get("body", "") if message.get("type") == "text" else "",
                "contact": value.get("contacts", [{}])[0] if value.get("contacts") else {}
            }
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Failed to parse WhatsApp webhook payload: {e}")
            return None


# Global WhatsApp client instance
whatsapp_client = WhatsAppClient()
