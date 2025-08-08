# WhatsApp package

"""
WhatsApp integration package for the retailer bots system.

This package contains:
- WhatsApp Cloud API client for sending messages and documents
- Message parser for handling bot commands and invoice format
- Inventory bot for stock management
- Invoice bot for invoice generation and retailer responses
"""

from .whatsapp_client import whatsapp_client, WhatsAppClient
from .message_parser import message_parser, MessageParser, CommandType
from .inventory_bot import inventory_bot, InventoryBot
from .invoice_bot import invoice_bot, InvoiceBot

__all__ = [
    "whatsapp_client",
    "WhatsAppClient",
    "message_parser", 
    "MessageParser",
    "CommandType",
    "inventory_bot",
    "InventoryBot",
    "invoice_bot",
    "InvoiceBot"
]
