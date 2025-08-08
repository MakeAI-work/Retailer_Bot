#!/usr/bin/env python3
"""
Test script for PDF invoice generation functionality.
This script tests the PDF generator without requiring WhatsApp integration.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set up environment
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("INVOICE_STORAGE_PATH", "./storage/invoices")

from app.database import get_db, engine
from app.models import Base, User, Item, Sale, SaleStatus
from app.whatsapp.pdf_generator import pdf_generator
from app.utils.security import get_password_hash


def setup_test_database():
    """Create test database and sample data"""
    print("🔧 Setting up test database...")
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = next(get_db())
    
    try:
        # Create test user
        test_user = User(
            name="Test Retailer",
            whatsapp_number="+1234567890",
            password_hash=get_password_hash("testpassword")
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        # Create test items
        test_items = [
            Item(name="Natraj Pencils", quantity=100, price=5.0, description="HB pencils"),
            Item(name="Parker Pen", quantity=50, price=25.0, description="Blue ink pen"),
            Item(name="A4 Paper", quantity=200, price=2.5, description="White paper pack")
        ]
        
        for item in test_items:
            db.add(item)
        
        db.commit()
        
        # Create test sale
        items_sold = [
            {
                "item_id": 1,
                "item_name": "Natraj Pencils",
                "quantity": 10,
                "unit_price": 5.0,
                "total_price": 50.0
            },
            {
                "item_id": 2,
                "item_name": "Parker Pen",
                "quantity": 2,
                "unit_price": 25.0,
                "total_price": 50.0
            }
        ]
        
        test_sale = Sale(
            customer_name="Raghav Kumar",
            items_sold_json=json.dumps(items_sold),
            total_amount=100.0,
            status=SaleStatus.PENDING,
            user_id=test_user.id
        )
        db.add(test_sale)
        db.commit()
        db.refresh(test_sale)
        
        print("✅ Test database setup complete")
        return test_user, test_sale, items_sold
        
    except Exception as e:
        print(f"❌ Error setting up test database: {e}")
        return None, None, None
    finally:
        db.close()


def test_pdf_generation():
    """Test PDF invoice generation"""
    print("\n📄 Testing PDF invoice generation...")
    
    # Setup test data
    user, sale, items_sold = setup_test_database()
    if not user or not sale:
        print("❌ Failed to setup test data")
        return False
    
    try:
        # Generate PDF
        print(f"🔄 Generating PDF for Sale ID: {sale.id}")
        pdf_path = pdf_generator.generate_invoice_pdf(sale, user, items_sold)
        
        # Verify PDF was created
        if os.path.exists(pdf_path):
            file_size = os.path.getsize(pdf_path)
            print(f"✅ PDF generated successfully!")
            print(f"   📁 Path: {pdf_path}")
            print(f"   📊 Size: {file_size} bytes ({file_size/1024:.2f} KB)")
            
            # Get PDF info
            pdf_info = pdf_generator.get_invoice_info(pdf_path)
            print(f"   📋 Info: {pdf_info}")
            
            return True
        else:
            print("❌ PDF file was not created")
            return False
            
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multiple_invoices():
    """Test generating multiple invoices"""
    print("\n📄 Testing multiple invoice generation...")
    
    db = next(get_db())
    
    try:
        # Get test user and create multiple sales
        user = db.query(User).first()
        if not user:
            print("❌ No test user found")
            return False
        
        test_customers = [
            ("John Doe", "Natraj Pencils", 5, 25.0),
            ("Jane Smith", "Parker Pen", 1, 25.0),
            ("Bob Johnson", "A4 Paper", 10, 25.0)
        ]
        
        generated_pdfs = []
        
        for customer_name, item_name, quantity, total in test_customers:
            # Create sale
            items_sold = [{
                "item_id": 1,
                "item_name": item_name,
                "quantity": quantity,
                "unit_price": total / quantity,
                "total_price": total
            }]
            
            sale = Sale(
                customer_name=customer_name,
                items_sold_json=json.dumps(items_sold),
                total_amount=total,
                status=SaleStatus.PENDING,
                user_id=user.id
            )
            db.add(sale)
            db.commit()
            db.refresh(sale)
            
            # Generate PDF
            try:
                pdf_path = pdf_generator.generate_invoice_pdf(sale, user, items_sold)
                generated_pdfs.append((customer_name, pdf_path))
                print(f"✅ Generated PDF for {customer_name}")
            except Exception as e:
                print(f"❌ Failed to generate PDF for {customer_name}: {e}")
        
        print(f"\n📊 Generated {len(generated_pdfs)} PDFs:")
        for customer, path in generated_pdfs:
            size = os.path.getsize(path) if os.path.exists(path) else 0
            print(f"   • {customer}: {size/1024:.2f} KB")
        
        return len(generated_pdfs) > 0
        
    except Exception as e:
        print(f"❌ Error in multiple invoice test: {e}")
        return False
    finally:
        db.close()


def test_pdf_cleanup():
    """Test PDF cleanup functionality"""
    print("\n🧹 Testing PDF cleanup...")
    
    try:
        # List current PDFs
        storage_path = Path(pdf_generator.storage_path)
        pdf_files = list(storage_path.glob("*.pdf"))
        print(f"📁 Found {len(pdf_files)} PDF files before cleanup")
        
        # Test cleanup (0 days = clean all)
        pdf_generator.cleanup_old_invoices(days_old=0)
        
        # Check remaining files
        remaining_files = list(storage_path.glob("*.pdf"))
        print(f"📁 Found {len(remaining_files)} PDF files after cleanup")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in cleanup test: {e}")
        return False


def main():
    """Run all PDF generation tests"""
    print("🚀 Starting PDF Invoice Generation Tests")
    print("=" * 50)
    
    # Ensure storage directory exists
    storage_path = Path("./storage/invoices")
    storage_path.mkdir(parents=True, exist_ok=True)
    
    tests = [
        ("Basic PDF Generation", test_pdf_generation),
        ("Multiple Invoices", test_multiple_invoices),
        ("PDF Cleanup", test_pdf_cleanup)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        print("-" * 30)
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<30} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! PDF generation is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    # Show generated files
    storage_path = Path("./storage/invoices")
    if storage_path.exists():
        pdf_files = list(storage_path.glob("*.pdf"))
        if pdf_files:
            print(f"\n📁 Generated PDF files ({len(pdf_files)}):")
            for pdf_file in pdf_files:
                size = pdf_file.stat().st_size
                print(f"   • {pdf_file.name} ({size/1024:.2f} KB)")


if __name__ == "__main__":
    main()
