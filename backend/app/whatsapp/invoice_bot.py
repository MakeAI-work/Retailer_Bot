import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from datetime import datetime

from app.database import get_db
from app.models import User, Item, Sale, WhatsAppSession, SaleStatus
from app.utils.security import verify_password
from app.whatsapp.message_parser import message_parser, CommandType
from app.whatsapp.whatsapp_client import whatsapp_client

logger = logging.getLogger(__name__)


class InvoiceBot:
    def __init__(self):
        self.bot_type = "invoice"
        # Store pending sales for retailer responses
        self.pending_sales = {}  # phone_number -> sale_id mapping

    async def handle_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming message for invoice bot"""
        try:
            phone_number = message_data.get("from")
            message_text = message_data.get("text", "")
            
            if not phone_number or not message_text:
                return {"success": False, "error": "Invalid message data"}
            
            # Parse the command
            parsed_command = message_parser.parse_invoice_message(message_text)
            command_type = parsed_command.get("command")
            
            # Get database session
            db = next(get_db())
            
            try:
                # Check if user has active session (except for login command)
                if command_type != CommandType.LOGIN:
                    session = self._get_active_session(db, phone_number)
                    if not session:
                        await whatsapp_client.send_invoice_response(
                            phone_number,
                            "🔒 Please login first using: login user_id password"
                        )
                        return {"success": True, "message": "Login required"}
                    
                    user = session.user
                else:
                    session = None
                    user = None
                
                # Handle different command types
                if command_type == CommandType.LOGIN:
                    return await self._handle_login(db, phone_number, parsed_command)
                
                elif command_type == CommandType.LOGOUT:
                    return await self._handle_logout(db, phone_number, session)
                
                elif command_type == CommandType.INVOICE_REQUEST:
                    return await self._handle_invoice_request(db, user, phone_number, parsed_command)
                
                elif command_type == CommandType.RETAILER_SUCCESS:
                    return await self._handle_retailer_success(db, user, phone_number)
                
                elif command_type == CommandType.RETAILER_FAIL:
                    return await self._handle_retailer_fail(db, user, phone_number)
                
                elif command_type == CommandType.HELP:
                    return await self._handle_help(phone_number)
                
                else:
                    error_msg = parsed_command.get("error", "Unknown command. Type 'help' for available commands.")
                    await whatsapp_client.send_invoice_response(phone_number, f"❌ {error_msg}")
                    return {"success": True, "message": "Error sent to user"}
            
            finally:
                db.close()
        
        except Exception as e:
            logger.error(f"Error handling invoice bot message: {e}")
            try:
                await whatsapp_client.send_invoice_response(
                    message_data.get("from", ""),
                    "❌ An error occurred. Please try again later."
                )
            except:
                pass
            return {"success": False, "error": str(e)}

    def _get_active_session(self, db: Session, phone_number: str) -> Optional[WhatsAppSession]:
        """Get active WhatsApp session for phone number"""
        return db.query(WhatsAppSession).filter(
            WhatsAppSession.whatsapp_number == phone_number,
            WhatsAppSession.bot_type == "invoice",
            WhatsAppSession.is_active == True
        ).first()

    async def _handle_login(self, db: Session, phone_number: str, parsed_command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle login command"""
        if "error" in parsed_command:
            await whatsapp_client.send_invoice_response(phone_number, f"❌ {parsed_command['error']}")
            return {"success": True, "message": "Login error sent"}
        
        user_id = parsed_command.get("user_id")
        password = parsed_command.get("password")
        
        # Find user by ID or WhatsApp number
        user = db.query(User).filter(
            or_(User.id == user_id, User.whatsapp_number == phone_number)
        ).first()
        
        if not user or not verify_password(password, user.password_hash):
            await whatsapp_client.send_invoice_response(
                phone_number,
                "❌ Invalid credentials. Please check your user ID and password."
            )
            return {"success": True, "message": "Invalid credentials"}
        
        # Deactivate existing sessions
        db.query(WhatsAppSession).filter(
            WhatsAppSession.whatsapp_number == phone_number,
            WhatsAppSession.bot_type == "invoice"
        ).update({"is_active": False})
        
        # Create new session
        from datetime import datetime, timedelta
        session = WhatsAppSession(
            user_id=user.id,
            whatsapp_number=phone_number,
            bot_type="invoice",
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db.add(session)
        db.commit()
        
        await whatsapp_client.send_invoice_response(
            phone_number,
            f"✅ Welcome {user.name}! You are now logged in to the Invoice Bot.\nType 'help' for available commands."
        )
        
        return {"success": True, "message": "Login successful"}

    async def _handle_logout(self, db: Session, phone_number: str, session: WhatsAppSession) -> Dict[str, Any]:
        """Handle logout command"""
        session.is_active = False
        db.commit()
        
        # Clear any pending sales for this user
        if phone_number in self.pending_sales:
            del self.pending_sales[phone_number]
        
        await whatsapp_client.send_invoice_response(
            phone_number,
            "👋 You have been logged out from the Invoice Bot."
        )
        
        return {"success": True, "message": "Logout successful"}

    async def _handle_invoice_request(self, db: Session, user: User, phone_number: str, parsed_command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle invoice request command"""
        if "error" in parsed_command:
            await whatsapp_client.send_invoice_response(phone_number, f"❌ {parsed_command['error']}")
            return {"success": True, "message": "Invoice request error sent"}
        
        customer_name = parsed_command.get("customer_name")
        item_name = parsed_command.get("item_name")
        quantity = parsed_command.get("quantity")
        
        # Find item
        item = db.query(Item).filter(Item.name.ilike(f"%{item_name}%"), Item.is_active == True).first()
        if not item:
            await whatsapp_client.send_invoice_response(
                phone_number,
                f"❌ Item '{item_name}' not found in inventory."
            )
            return {"success": True, "message": "Item not found"}
        
        # Check stock availability
        if item.quantity < quantity:
            await whatsapp_client.send_invoice_response(
                phone_number,
                f"❌ Insufficient stock for '{item.name}'.\nAvailable: {item.quantity}\nRequested: {quantity}"
            )
            return {"success": True, "message": "Insufficient stock"}
        
        # Calculate total amount
        total_amount = item.price * quantity
        
        # Create sale record
        import json
        items_sold = [{
            "item_id": item.id,
            "item_name": item.name,
            "quantity": quantity,
            "unit_price": float(item.price),
            "total_price": float(total_amount)
        }]
        
        sale = Sale(
            customer_name=customer_name,
            items_sold_json=json.dumps(items_sold),
            total_amount=total_amount,
            status=SaleStatus.PENDING,
            user_id=user.id
        )
        db.add(sale)
        db.commit()
        db.refresh(sale)
        
        # Store pending sale for this user
        self.pending_sales[phone_number] = sale.id
        
        # Generate and send invoice (for now, send text summary - PDF will be in Phase 5)
        invoice_message = f"""🧾 *INVOICE GENERATED*

📋 *Sale ID:* {sale.id}
👤 *Customer:* {customer_name}
📦 *Item:* {item.name}
🔢 *Quantity:* {quantity}
💰 *Unit Price:* ₹{item.price:.2f}
💵 *Total Amount:* ₹{total_amount:.2f}

⏳ *Status:* Pending Confirmation

Please reply with:
• `success` - to confirm sale and update stock
• `fail` - to cancel sale"""
        
        await whatsapp_client.send_invoice_response(phone_number, invoice_message)
        
        return {"success": True, "message": "Invoice generated and sent"}

    async def _handle_retailer_success(self, db: Session, user: User, phone_number: str) -> Dict[str, Any]:
        """Handle retailer success response"""
        # Get pending sale for this user
        sale_id = self.pending_sales.get(phone_number)
        if not sale_id:
            await whatsapp_client.send_invoice_response(
                phone_number,
                "❌ No pending invoice found. Please create an invoice first."
            )
            return {"success": True, "message": "No pending invoice"}
        
        # Get sale record
        sale = db.query(Sale).filter(Sale.id == sale_id, Sale.user_id == user.id).first()
        if not sale or sale.status != SaleStatus.PENDING:
            await whatsapp_client.send_invoice_response(
                phone_number,
                "❌ Invalid or already processed sale."
            )
            return {"success": True, "message": "Invalid sale"}
        
        # Update sale status to success
        sale.status = SaleStatus.SUCCESS
        sale.updated_at = datetime.utcnow()
        
        # Update stock for sold items
        import json
        items_sold = json.loads(sale.items_sold_json)
        
        for item_data in items_sold:
            item = db.query(Item).filter(Item.id == item_data["item_id"]).first()
            if item:
                item.quantity -= item_data["quantity"]
        
        db.commit()
        
        # Clear pending sale
        del self.pending_sales[phone_number]
        
        # Send confirmation
        await whatsapp_client.send_invoice_response(
            phone_number,
            f"✅ *SALE CONFIRMED*\n\n📋 Sale ID: {sale.id}\n👤 Customer: {sale.customer_name}\n💵 Amount: ₹{sale.total_amount:.2f}\n\n📦 Stock has been updated automatically."
        )
        
        return {"success": True, "message": "Sale confirmed and stock updated"}

    async def _handle_retailer_fail(self, db: Session, user: User, phone_number: str) -> Dict[str, Any]:
        """Handle retailer fail response"""
        # Get pending sale for this user
        sale_id = self.pending_sales.get(phone_number)
        if not sale_id:
            await whatsapp_client.send_invoice_response(
                phone_number,
                "❌ No pending invoice found. Please create an invoice first."
            )
            return {"success": True, "message": "No pending invoice"}
        
        # Get sale record
        sale = db.query(Sale).filter(Sale.id == sale_id, Sale.user_id == user.id).first()
        if not sale or sale.status != SaleStatus.PENDING:
            await whatsapp_client.send_invoice_response(
                phone_number,
                "❌ Invalid or already processed sale."
            )
            return {"success": True, "message": "Invalid sale"}
        
        # Update sale status to failed
        sale.status = SaleStatus.FAILED
        sale.updated_at = datetime.utcnow()
        db.commit()
        
        # Clear pending sale
        del self.pending_sales[phone_number]
        
        # Send confirmation
        await whatsapp_client.send_invoice_response(
            phone_number,
            f"❌ *SALE CANCELLED*\n\n📋 Sale ID: {sale.id}\n👤 Customer: {sale.customer_name}\n💵 Amount: ₹{sale.total_amount:.2f}\n\n📦 No stock changes made."
        )
        
        return {"success": True, "message": "Sale cancelled"}

    async def _handle_help(self, phone_number: str) -> Dict[str, Any]:
        """Handle help command"""
        help_message = message_parser.generate_help_message("invoice")
        await whatsapp_client.send_invoice_response(phone_number, help_message)
        
        return {"success": True, "message": "Help message sent"}

    def get_pending_sale_info(self, phone_number: str, db: Session) -> Optional[Sale]:
        """Get pending sale information for a phone number"""
        sale_id = self.pending_sales.get(phone_number)
        if not sale_id:
            return None
        
        return db.query(Sale).filter(Sale.id == sale_id).first()


# Global invoice bot instance
invoice_bot = InvoiceBot()
