import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models import User, Item, WhatsAppSession
from app.schemas import ItemCreate, ItemUpdate
from app.utils.security import verify_password
from app.whatsapp.message_parser import message_parser, CommandType
from app.whatsapp.whatsapp_client import whatsapp_client

logger = logging.getLogger(__name__)


class InventoryBot:
    def __init__(self):
        self.bot_type = "inventory"

    async def handle_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming message for inventory bot"""
        try:
            phone_number = message_data.get("from")
            message_text = message_data.get("text", "")
            
            if not phone_number or not message_text:
                return {"success": False, "error": "Invalid message data"}
            
            # Parse the command
            parsed_command = message_parser.parse_inventory_command(message_text)
            command_type = parsed_command.get("command")
            
            # Get database session
            db = next(get_db())
            
            try:
                # Check if user has active session (except for login command)
                if command_type != CommandType.LOGIN:
                    session = self._get_active_session(db, phone_number)
                    if not session:
                        await whatsapp_client.send_inventory_response(
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
                
                elif command_type == CommandType.ADD_ITEM:
                    return await self._handle_add_item(db, user, phone_number, parsed_command)
                
                elif command_type == CommandType.UPDATE_STOCK:
                    return await self._handle_update_stock(db, user, phone_number, parsed_command)
                
                elif command_type == CommandType.VIEW_ITEMS:
                    return await self._handle_view_items(db, phone_number)
                
                elif command_type == CommandType.CHECK_STOCK:
                    return await self._handle_check_stock(db, phone_number, parsed_command)
                
                elif command_type == CommandType.LOW_STOCK:
                    return await self._handle_low_stock(db, phone_number)
                
                elif command_type == CommandType.HELP:
                    return await self._handle_help(phone_number)
                
                else:
                    error_msg = parsed_command.get("error", "Unknown command. Type 'help' for available commands.")
                    await whatsapp_client.send_inventory_response(phone_number, f"❌ {error_msg}")
                    return {"success": True, "message": "Error sent to user"}
            
            finally:
                db.close()
        
        except Exception as e:
            logger.error(f"Error handling inventory bot message: {e}")
            try:
                await whatsapp_client.send_inventory_response(
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
            WhatsAppSession.bot_type == "inventory",
            WhatsAppSession.is_active == True
        ).first()

    async def _handle_login(self, db: Session, phone_number: str, parsed_command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle login command"""
        if "error" in parsed_command:
            await whatsapp_client.send_inventory_response(phone_number, f"❌ {parsed_command['error']}")
            return {"success": True, "message": "Login error sent"}
        
        user_id = parsed_command.get("user_id")
        password = parsed_command.get("password")
        
        # Find user by ID or WhatsApp number
        user = db.query(User).filter(
            or_(User.id == user_id, User.whatsapp_number == phone_number)
        ).first()
        
        if not user or not verify_password(password, user.password_hash):
            await whatsapp_client.send_inventory_response(
                phone_number,
                "❌ Invalid credentials. Please check your user ID and password."
            )
            return {"success": True, "message": "Invalid credentials"}
        
        # Deactivate existing sessions
        db.query(WhatsAppSession).filter(
            WhatsAppSession.whatsapp_number == phone_number,
            WhatsAppSession.bot_type == "inventory"
        ).update({"is_active": False})
        
        # Create new session
        from datetime import datetime, timedelta
        session = WhatsAppSession(
            user_id=user.id,
            whatsapp_number=phone_number,
            bot_type="inventory",
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db.add(session)
        db.commit()
        
        await whatsapp_client.send_inventory_response(
            phone_number,
            f"✅ Welcome {user.name}! You are now logged in to the Inventory Bot.\nType 'help' for available commands."
        )
        
        return {"success": True, "message": "Login successful"}

    async def _handle_logout(self, db: Session, phone_number: str, session: WhatsAppSession) -> Dict[str, Any]:
        """Handle logout command"""
        session.is_active = False
        db.commit()
        
        await whatsapp_client.send_inventory_response(
            phone_number,
            "👋 You have been logged out from the Inventory Bot."
        )
        
        return {"success": True, "message": "Logout successful"}

    async def _handle_add_item(self, db: Session, user: User, phone_number: str, parsed_command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle add item command"""
        if "error" in parsed_command:
            await whatsapp_client.send_inventory_response(phone_number, f"❌ {parsed_command['error']}")
            return {"success": True, "message": "Add item error sent"}
        
        item_name = parsed_command.get("item_name")
        quantity = parsed_command.get("quantity")
        price = parsed_command.get("price")
        
        # Check if item already exists
        existing_item = db.query(Item).filter(Item.name.ilike(f"%{item_name}%")).first()
        if existing_item:
            await whatsapp_client.send_inventory_response(
                phone_number,
                f"❌ Item '{item_name}' already exists. Use 'update' command to modify stock."
            )
            return {"success": True, "message": "Item already exists"}
        
        # Create new item
        new_item = Item(
            name=item_name.title(),
            quantity=quantity,
            price=price,
            description=f"Added via WhatsApp by {user.name}"
        )
        db.add(new_item)
        db.commit()
        
        await whatsapp_client.send_inventory_response(
            phone_number,
            f"✅ Item added successfully!\n\n📦 *{new_item.name}*\nStock: {new_item.quantity}\nPrice: ₹{new_item.price:.2f}"
        )
        
        return {"success": True, "message": "Item added successfully"}

    async def _handle_update_stock(self, db: Session, user: User, phone_number: str, parsed_command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle update stock command"""
        if "error" in parsed_command:
            await whatsapp_client.send_inventory_response(phone_number, f"❌ {parsed_command['error']}")
            return {"success": True, "message": "Update stock error sent"}
        
        item_name = parsed_command.get("item_name")
        quantity = parsed_command.get("quantity")
        
        # Find item
        item = db.query(Item).filter(Item.name.ilike(f"%{item_name}%"), Item.is_active == True).first()
        if not item:
            await whatsapp_client.send_inventory_response(
                phone_number,
                f"❌ Item '{item_name}' not found. Use 'view' to see available items."
            )
            return {"success": True, "message": "Item not found"}
        
        # Update stock
        old_quantity = item.quantity
        item.quantity = quantity
        db.commit()
        
        stock_emoji = "✅" if quantity > 10 else "⚠️" if quantity > 0 else "❌"
        await whatsapp_client.send_inventory_response(
            phone_number,
            f"{stock_emoji} Stock updated successfully!\n\n📦 *{item.name}*\nOld Stock: {old_quantity}\nNew Stock: {item.quantity}\nPrice: ₹{item.price:.2f}"
        )
        
        return {"success": True, "message": "Stock updated successfully"}

    async def _handle_view_items(self, db: Session, phone_number: str) -> Dict[str, Any]:
        """Handle view items command"""
        items = db.query(Item).filter(Item.is_active == True).order_by(Item.name).all()
        
        formatted_message = message_parser.format_item_list(items)
        await whatsapp_client.send_inventory_response(phone_number, formatted_message)
        
        return {"success": True, "message": "Items list sent"}

    async def _handle_check_stock(self, db: Session, phone_number: str, parsed_command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle check stock command"""
        if "error" in parsed_command:
            await whatsapp_client.send_inventory_response(phone_number, f"❌ {parsed_command['error']}")
            return {"success": True, "message": "Check stock error sent"}
        
        item_name = parsed_command.get("item_name")
        
        # Find item
        item = db.query(Item).filter(Item.name.ilike(f"%{item_name}%"), Item.is_active == True).first()
        if not item:
            await whatsapp_client.send_inventory_response(
                phone_number,
                f"❌ Item '{item_name}' not found. Use 'view' to see available items."
            )
            return {"success": True, "message": "Item not found"}
        
        stock_emoji = "✅" if item.quantity > 10 else "⚠️" if item.quantity > 0 else "❌"
        status = "Well Stocked" if item.quantity > 10 else "Low Stock" if item.quantity > 0 else "Out of Stock"
        
        await whatsapp_client.send_inventory_response(
            phone_number,
            f"{stock_emoji} *{item.name}*\n\nStock: {item.quantity}\nPrice: ₹{item.price:.2f}\nStatus: {status}"
        )
        
        return {"success": True, "message": "Stock info sent"}

    async def _handle_low_stock(self, db: Session, phone_number: str) -> Dict[str, Any]:
        """Handle low stock command"""
        low_stock_items = db.query(Item).filter(
            Item.is_active == True,
            Item.quantity <= 10,
            Item.quantity > 0
        ).order_by(Item.quantity).all()
        
        formatted_message = message_parser.format_low_stock_alert(low_stock_items)
        await whatsapp_client.send_inventory_response(phone_number, formatted_message)
        
        return {"success": True, "message": "Low stock alert sent"}

    async def _handle_help(self, phone_number: str) -> Dict[str, Any]:
        """Handle help command"""
        help_message = message_parser.generate_help_message("inventory")
        await whatsapp_client.send_inventory_response(phone_number, help_message)
        
        return {"success": True, "message": "Help message sent"}


# Global inventory bot instance
inventory_bot = InventoryBot()
