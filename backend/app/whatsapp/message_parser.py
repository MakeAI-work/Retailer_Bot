import re
import logging
from typing import Optional, Dict, Any, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class CommandType(Enum):
    # Inventory bot commands
    ADD_ITEM = "add"
    UPDATE_STOCK = "update"
    VIEW_ITEMS = "view"
    CHECK_STOCK = "stock"
    LOW_STOCK = "lowstock"
    HELP = "help"
    
    # Invoice bot commands
    INVOICE_REQUEST = "invoice"
    RETAILER_SUCCESS = "success"
    RETAILER_FAIL = "fail"
    
    # Session commands
    LOGIN = "login"
    LOGOUT = "logout"
    
    # Unknown
    UNKNOWN = "unknown"


class MessageParser:
    def __init__(self):
        self.inventory_commands = {
            "add": CommandType.ADD_ITEM,
            "update": CommandType.UPDATE_STOCK,
            "view": CommandType.VIEW_ITEMS,
            "stock": CommandType.CHECK_STOCK,
            "lowstock": CommandType.LOW_STOCK,
            "help": CommandType.HELP,
            "login": CommandType.LOGIN,
            "logout": CommandType.LOGOUT
        }
        
        self.invoice_responses = {
            "success": CommandType.RETAILER_SUCCESS,
            "fail": CommandType.RETAILER_FAIL,
            "failed": CommandType.RETAILER_FAIL
        }

    def parse_inventory_command(self, message: str) -> Dict[str, Any]:
        """Parse inventory bot commands
        
        Expected formats:
        - "add item_name quantity price" - Add new item
        - "update item_name quantity" - Update stock quantity
        - "view" - View all items
        - "stock item_name" - Check specific item stock
        - "lowstock" - View low stock items
        - "help" - Show help message
        - "login user_id password" - Login to bot
        """
        message = message.strip().lower()
        parts = message.split()
        
        if not parts:
            return {"command": CommandType.UNKNOWN, "error": "Empty message"}
        
        command_word = parts[0]
        command_type = self.inventory_commands.get(command_word, CommandType.UNKNOWN)
        
        result = {"command": command_type, "raw_message": message}
        
        try:
            if command_type == CommandType.ADD_ITEM:
                # Format: "add item_name quantity price"
                if len(parts) < 4:
                    result["error"] = "Invalid format. Use: add item_name quantity price"
                    return result
                
                item_name = " ".join(parts[1:-2])  # Everything except last 2 parts
                quantity = int(parts[-2])
                price = float(parts[-1])
                
                result.update({
                    "item_name": item_name,
                    "quantity": quantity,
                    "price": price
                })
            
            elif command_type == CommandType.UPDATE_STOCK:
                # Format: "update item_name quantity"
                if len(parts) < 3:
                    result["error"] = "Invalid format. Use: update item_name quantity"
                    return result
                
                item_name = " ".join(parts[1:-1])  # Everything except last part
                quantity = int(parts[-1])
                
                result.update({
                    "item_name": item_name,
                    "quantity": quantity
                })
            
            elif command_type == CommandType.CHECK_STOCK:
                # Format: "stock item_name"
                if len(parts) < 2:
                    result["error"] = "Invalid format. Use: stock item_name"
                    return result
                
                item_name = " ".join(parts[1:])
                result["item_name"] = item_name
            
            elif command_type == CommandType.LOGIN:
                # Format: "login user_id password"
                if len(parts) != 3:
                    result["error"] = "Invalid format. Use: login user_id password"
                    return result
                
                result.update({
                    "user_id": parts[1],
                    "password": parts[2]
                })
            
            elif command_type in [CommandType.VIEW_ITEMS, CommandType.LOW_STOCK, CommandType.HELP, CommandType.LOGOUT]:
                # These commands don't need additional parameters
                pass
            
            else:
                result["error"] = "Unknown command. Type 'help' for available commands."
        
        except (ValueError, IndexError) as e:
            result["error"] = f"Invalid command format: {str(e)}"
        
        return result

    def parse_invoice_message(self, message: str) -> Dict[str, Any]:
        """Parse invoice bot messages
        
        Expected formats:
        - "customer_name: item_name: quantity" - Invoice request
        - "success" - Retailer confirmation
        - "fail" or "failed" - Retailer rejection
        - "login user_id password" - Login to bot
        """
        message = message.strip()
        message_lower = message.lower()
        
        result = {"raw_message": message}
        
        # Check for retailer responses first
        if message_lower in self.invoice_responses:
            result["command"] = self.invoice_responses[message_lower]
            return result
        
        # Check for login command
        if message_lower.startswith("login "):
            parts = message.split()
            if len(parts) == 3:
                result.update({
                    "command": CommandType.LOGIN,
                    "user_id": parts[1],
                    "password": parts[2]
                })
            else:
                result.update({
                    "command": CommandType.UNKNOWN,
                    "error": "Invalid format. Use: login user_id password"
                })
            return result
        
        # Check for logout command
        if message_lower == "logout":
            result["command"] = CommandType.LOGOUT
            return result
        
        # Check for help command
        if message_lower == "help":
            result["command"] = CommandType.HELP
            return result
        
        # Parse invoice request format: "customer_name: item_name: quantity"
        if ":" in message:
            parts = [part.strip() for part in message.split(":")]
            
            if len(parts) == 3:
                customer_name, item_name, quantity_str = parts
                
                try:
                    quantity = int(quantity_str)
                    if quantity <= 0:
                        raise ValueError("Quantity must be positive")
                    
                    result.update({
                        "command": CommandType.INVOICE_REQUEST,
                        "customer_name": customer_name.title(),  # Capitalize properly
                        "item_name": item_name.title(),
                        "quantity": quantity
                    })
                except ValueError as e:
                    result.update({
                        "command": CommandType.UNKNOWN,
                        "error": f"Invalid quantity: {str(e)}"
                    })
            else:
                result.update({
                    "command": CommandType.UNKNOWN,
                    "error": "Invalid format. Use: customer_name: item_name: quantity"
                })
        else:
            result.update({
                "command": CommandType.UNKNOWN,
                "error": "Invalid format. Use: customer_name: item_name: quantity"
            })
        
        return result

    def generate_help_message(self, bot_type: str) -> str:
        """Generate help message for the specified bot"""
        if bot_type == "inventory":
            return """📦 *Inventory Bot Commands:*

*Stock Management:*
• `add item_name quantity price` - Add new item
• `update item_name quantity` - Update stock quantity
• `stock item_name` - Check specific item stock
• `view` - View all items
• `lowstock` - View low stock items

*Session:*
• `login user_id password` - Login to bot
• `logout` - Logout from bot

*Example:*
`add Natraj Pencils 100 5.0`
`update Natraj Pencils 50`
`stock Natraj Pencils`"""
        
        elif bot_type == "invoice":
            return """🧾 *Invoice Bot Commands:*

*Create Invoice:*
• `customer_name: item_name: quantity` - Generate invoice

*Retailer Response:*
• `success` - Confirm sale (stock will be deducted)
• `fail` - Reject sale (no stock change)

*Session:*
• `login user_id password` - Login to bot
• `logout` - Logout from bot

*Example:*
`Raghav: Natraj Pencils: 2`
Then respond with `success` or `fail`"""
        
        return "Help not available for this bot type."

    def validate_phone_number(self, phone_number: str) -> bool:
        """Validate phone number format"""
        # Remove any non-digit characters
        digits_only = re.sub(r'\D', '', phone_number)
        # Check if it's a valid length (10-15 digits)
        return 10 <= len(digits_only) <= 15

    def format_item_list(self, items: list) -> str:
        """Format item list for WhatsApp message"""
        if not items:
            return "No items found."
        
        message = "📦 *Current Inventory:*\n\n"
        for item in items:
            stock_emoji = "✅" if item.quantity > 10 else "⚠️" if item.quantity > 0 else "❌"
            message += f"{stock_emoji} *{item.name}*\n"
            message += f"   Stock: {item.quantity}\n"
            message += f"   Price: ₹{item.price:.2f}\n\n"
        
        return message

    def format_low_stock_alert(self, items: list) -> str:
        """Format low stock alert message"""
        if not items:
            return "✅ All items are well stocked!"
        
        message = "⚠️ *Low Stock Alert:*\n\n"
        for item in items:
            message += f"• *{item.name}*: {item.quantity} left\n"
        
        return message


# Global message parser instance
message_parser = MessageParser()
