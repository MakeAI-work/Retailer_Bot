import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from app.config import settings
from app.models import Sale, Item, User

logger = logging.getLogger(__name__)


class PDFInvoiceGenerator:
    def __init__(self):
        self.storage_path = Path(settings.INVOICE_STORAGE_PATH)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Invoice styling
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()

    def setup_custom_styles(self):
        """Setup custom styles for the invoice"""
        # Company header style
        self.styles.add(ParagraphStyle(
            name='CompanyHeader',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.darkblue,
            alignment=TA_CENTER,
            spaceAfter=6
        ))
        
        # Invoice title style
        self.styles.add(ParagraphStyle(
            name='InvoiceTitle',
            parent=self.styles['Heading2'],
            fontSize=18,
            textColor=colors.darkred,
            alignment=TA_CENTER,
            spaceAfter=12
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.darkblue,
            alignment=TA_LEFT,
            spaceAfter=6
        ))
        
        # Invoice info style
        self.styles.add(ParagraphStyle(
            name='InvoiceInfo',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_RIGHT,
            spaceAfter=3
        ))
        
        # Customer info style
        self.styles.add(ParagraphStyle(
            name='CustomerInfo',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_LEFT,
            spaceAfter=3
        ))
        
        # Total style
        self.styles.add(ParagraphStyle(
            name='Total',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=colors.darkred,
            alignment=TA_RIGHT,
            fontName='Helvetica-Bold'
        ))

    def generate_invoice_pdf(
        self, 
        sale: Sale, 
        user: User,
        items_data: list
    ) -> str:
        """Generate PDF invoice and return file path"""
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"invoice_{sale.id}_{timestamp}.pdf"
            file_path = self.storage_path / filename
            
            # Create PDF document
            doc = SimpleDocTemplate(
                str(file_path),
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build invoice content
            story = []
            
            # Company header
            story.append(Paragraph("RETAILER INVOICE", self.styles['CompanyHeader']))
            story.append(Spacer(1, 12))
            
            # Invoice info section
            invoice_info = [
                [
                    Paragraph("<b>Invoice Details</b>", self.styles['SectionHeader']),
                    ""
                ],
                [
                    Paragraph("Invoice ID:", self.styles['CustomerInfo']),
                    Paragraph(f"<b>INV-{sale.id:06d}</b>", self.styles['InvoiceInfo'])
                ],
                [
                    Paragraph("Date:", self.styles['CustomerInfo']),
                    Paragraph(f"<b>{sale.created_at.strftime('%d %B %Y')}</b>", self.styles['InvoiceInfo'])
                ],
                [
                    Paragraph("Time:", self.styles['CustomerInfo']),
                    Paragraph(f"<b>{sale.created_at.strftime('%I:%M %p')}</b>", self.styles['InvoiceInfo'])
                ],
                [
                    Paragraph("Status:", self.styles['CustomerInfo']),
                    Paragraph(f"<b>{sale.status.value.title()}</b>", self.styles['InvoiceInfo'])
                ]
            ]
            
            invoice_table = Table(invoice_info, colWidths=[2*inch, 2*inch])
            invoice_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('SPAN', (0, 0), (1, 0)),
                ('BACKGROUND', (0, 0), (1, 0), colors.lightblue),
                ('GRID', (0, 1), (-1, -1), 1, colors.lightgrey),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
            ]))
            
            story.append(invoice_table)
            story.append(Spacer(1, 20))
            
            # Customer and retailer info
            info_data = [
                [
                    Paragraph("<b>Bill To:</b>", self.styles['SectionHeader']),
                    Paragraph("<b>Retailer:</b>", self.styles['SectionHeader'])
                ],
                [
                    Paragraph(f"<b>{sale.customer_name}</b>", self.styles['CustomerInfo']),
                    Paragraph(f"<b>{user.name}</b>", self.styles['CustomerInfo'])
                ],
                [
                    Paragraph("Customer", self.styles['CustomerInfo']),
                    Paragraph(f"Phone: {user.whatsapp_number}", self.styles['CustomerInfo'])
                ]
            ]
            
            info_table = Table(info_data, colWidths=[3*inch, 3*inch])
            info_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
            ]))
            
            story.append(info_table)
            story.append(Spacer(1, 20))
            
            # Items table
            story.append(Paragraph("Items", self.styles['SectionHeader']))
            
            # Table headers
            items_data_table = [
                ['Item Name', 'Unit Price', 'Quantity', 'Total Price']
            ]
            
            # Parse items from sale
            items_sold = json.loads(sale.items_sold_json)
            subtotal = 0
            
            for item in items_sold:
                items_data_table.append([
                    item['item_name'],
                    f"₹{item['unit_price']:.2f}",
                    str(item['quantity']),
                    f"₹{item['total_price']:.2f}"
                ])
                subtotal += item['total_price']
            
            # Create items table
            items_table = Table(items_data_table, colWidths=[2.5*inch, 1.2*inch, 1*inch, 1.3*inch])
            items_table.setStyle(TableStyle([
                # Header row
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                
                # Data rows
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),  # Right align prices
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),    # Left align item names
                
                # Grid
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(items_table)
            story.append(Spacer(1, 20))
            
            # Total section
            total_data = [
                ['', '', 'Subtotal:', f"₹{subtotal:.2f}"],
                ['', '', 'Tax (0%):', '₹0.00'],
                ['', '', 'Total Amount:', f"₹{sale.total_amount:.2f}"]
            ]
            
            total_table = Table(total_data, colWidths=[2.5*inch, 1.2*inch, 1*inch, 1.3*inch])
            total_table.setStyle(TableStyle([
                ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (2, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (2, 0), (-1, -1), 11),
                ('BACKGROUND', (2, -1), (-1, -1), colors.darkred),
                ('TEXTCOLOR', (2, -1), (-1, -1), colors.white),
                ('FONTSIZE', (2, -1), (-1, -1), 12),
                ('GRID', (2, 0), (-1, -1), 1, colors.black),
            ]))
            
            story.append(total_table)
            story.append(Spacer(1, 30))
            
            # Footer
            story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
            story.append(Spacer(1, 12))
            
            footer_text = """
            <b>Payment Instructions:</b><br/>
            Please confirm this invoice by replying with 'success' to complete the transaction.<br/>
            Reply with 'fail' to cancel this invoice.<br/><br/>
            <b>Thank you for your business!</b><br/>
            Generated via WhatsApp Retailer Bot System
            """
            
            story.append(Paragraph(footer_text, self.styles['Normal']))
            
            # Build PDF
            doc.build(story)
            
            # Update sale with PDF path
            sale.pdf_path = str(file_path)
            
            logger.info(f"Invoice PDF generated successfully: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Error generating invoice PDF: {e}")
            raise Exception(f"PDF generation failed: {e}")

    def generate_invoice_filename(self, sale_id: int) -> str:
        """Generate a unique filename for the invoice"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"invoice_{sale_id}_{timestamp}.pdf"

    def cleanup_old_invoices(self, days_old: int = 30):
        """Clean up invoice files older than specified days"""
        try:
            cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            
            for file_path in self.storage_path.glob("*.pdf"):
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    logger.info(f"Cleaned up old invoice: {file_path}")
                    
        except Exception as e:
            logger.error(f"Error cleaning up old invoices: {e}")

    def get_invoice_info(self, file_path: str) -> Dict[str, Any]:
        """Get invoice file information"""
        try:
            path = Path(file_path)
            if not path.exists():
                return {"exists": False}
            
            stat = path.stat()
            return {
                "exists": True,
                "filename": path.name,
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created_at": datetime.fromtimestamp(stat.st_ctime),
                "modified_at": datetime.fromtimestamp(stat.st_mtime)
            }
        except Exception as e:
            logger.error(f"Error getting invoice info: {e}")
            return {"exists": False, "error": str(e)}


# Global PDF generator instance
pdf_generator = PDFInvoiceGenerator()
