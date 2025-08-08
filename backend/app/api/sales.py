from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
import json

from app.database import get_db
from app.models import Sale, Item, User, SaleStatus
from app.schemas import (
    SaleCreate, SaleUpdate, SaleResponse, SaleStatusUpdate,
    InvoiceRequest, SaleSearch, SaleStatusEnum, SaleItemData
)
from app.api.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=List[SaleResponse])
def get_sales_history(
    skip: int = Query(0, ge=0, description="Number of sales to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of sales to return"),
    status_filter: Optional[SaleStatusEnum] = Query(None, description="Filter by sale status"),
    customer_name: Optional[str] = Query(None, description="Filter by customer name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get sales history with optional filtering"""
    query = db.query(Sale).filter(Sale.user_id == current_user.id)
    
    # Apply filters
    if status_filter:
        query = query.filter(Sale.status == SaleStatus(status_filter.value))
    
    if customer_name:
        query = query.filter(Sale.customer_name.ilike(f"%{customer_name}%"))
    
    # Order by most recent first
    sales = query.order_by(desc(Sale.created_at)).offset(skip).limit(limit).all()
    
    # Convert items_sold_json to list for response
    for sale in sales:
        if isinstance(sale.items_sold_json, str):
            sale.items_sold = json.loads(sale.items_sold_json)
        else:
            sale.items_sold = sale.items_sold_json
    
    return sales


@router.get("/{sale_id}", response_model=SaleResponse)
def get_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific sale by ID"""
    sale = db.query(Sale).filter(
        Sale.id == sale_id,
        Sale.user_id == current_user.id
    ).first()
    
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sale not found"
        )
    
    # Convert items_sold_json to list for response
    if isinstance(sale.items_sold_json, str):
        sale.items_sold = json.loads(sale.items_sold_json)
    else:
        sale.items_sold = sale.items_sold_json
    
    return sale


@router.post("/", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
def create_sale(
    sale_data: SaleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new sale"""
    # Validate items exist and have sufficient stock
    total_calculated = 0
    validated_items = []
    
    for item_data in sale_data.items_sold:
        # Find item in database
        item = db.query(Item).filter(
            Item.name.ilike(item_data.item_name),
            Item.is_active == True
        ).first()
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item '{item_data.item_name}' not found"
            )
        
        # Check stock availability
        if item.quantity < item_data.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for '{item_data.item_name}'. Available: {item.quantity}, Requested: {item_data.quantity}"
            )
        
        # Calculate item total
        item_total = item.price * item_data.quantity
        total_calculated += item_total
        
        # Add validated item data
        validated_items.append({
            "item_name": item.name,
            "quantity": item_data.quantity,
            "unit_price": item.price,
            "total_price": item_total
        })
    
    # Verify total amount matches
    if abs(total_calculated - sale_data.total_amount) > 0.01:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Total amount mismatch. Calculated: {total_calculated}, Provided: {sale_data.total_amount}"
        )
    
    # Create sale record
    db_sale = Sale(
        customer_name=sale_data.customer_name,
        items_sold_json=json.dumps(validated_items),
        total_amount=sale_data.total_amount,
        user_id=current_user.id,
        status=SaleStatus.PENDING
    )
    
    db.add(db_sale)
    db.commit()
    db.refresh(db_sale)
    
    # Add items_sold for response
    db_sale.items_sold = validated_items
    
    return db_sale


@router.post("/from-whatsapp", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
def create_sale_from_whatsapp(
    invoice_request: InvoiceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a sale from WhatsApp invoice request (customer_name: item_name: quantity)"""
    # Find the item
    item = db.query(Item).filter(
        Item.name.ilike(invoice_request.item_name),
        Item.is_active == True
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item '{invoice_request.item_name}' not found"
        )
    
    # Check stock availability
    if item.quantity < invoice_request.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient stock for '{invoice_request.item_name}'. Available: {item.quantity}, Requested: {invoice_request.quantity}"
        )
    
    # Calculate total
    total_amount = item.price * invoice_request.quantity
    
    # Create item data
    item_data = {
        "item_name": item.name,
        "quantity": invoice_request.quantity,
        "unit_price": item.price,
        "total_price": total_amount
    }
    
    # Create sale record
    db_sale = Sale(
        customer_name=invoice_request.customer_name,
        items_sold_json=json.dumps([item_data]),
        total_amount=total_amount,
        user_id=current_user.id,
        status=SaleStatus.PENDING
    )
    
    db.add(db_sale)
    db.commit()
    db.refresh(db_sale)
    
    # Add items_sold for response
    db_sale.items_sold = [item_data]
    
    return db_sale


@router.put("/{sale_id}/status", response_model=SaleResponse)
def update_sale_status(
    sale_id: int,
    status_update: SaleStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update sale status (used when retailer responds with success/fail)"""
    sale = db.query(Sale).filter(
        Sale.id == sale_id,
        Sale.user_id == current_user.id
    ).first()
    
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sale not found"
        )
    
    old_status = sale.status
    new_status = SaleStatus(status_update.status.value)
    
    # Update sale status
    sale.status = new_status
    
    # If status changed from PENDING to SUCCESS, decrease stock
    if old_status == SaleStatus.PENDING and new_status == SaleStatus.SUCCESS:
        # Parse items and decrease stock
        items_sold = json.loads(sale.items_sold_json) if isinstance(sale.items_sold_json, str) else sale.items_sold_json
        
        for item_data in items_sold:
            item = db.query(Item).filter(
                Item.name.ilike(item_data["item_name"]),
                Item.is_active == True
            ).first()
            
            if item:
                # Decrease stock
                item.quantity -= item_data["quantity"]
                if item.quantity < 0:
                    item.quantity = 0  # Prevent negative stock
    
    db.commit()
    db.refresh(sale)
    
    # Add items_sold for response
    if isinstance(sale.items_sold_json, str):
        sale.items_sold = json.loads(sale.items_sold_json)
    else:
        sale.items_sold = sale.items_sold_json
    
    return sale


@router.get("/pending/", response_model=List[SaleResponse])
def get_pending_sales(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all pending sales awaiting retailer confirmation"""
    sales = db.query(Sale).filter(
        Sale.user_id == current_user.id,
        Sale.status == SaleStatus.PENDING
    ).order_by(desc(Sale.created_at)).all()
    
    # Convert items_sold_json to list for response
    for sale in sales:
        if isinstance(sale.items_sold_json, str):
            sale.items_sold = json.loads(sale.items_sold_json)
        else:
            sale.items_sold = sale.items_sold_json
    
    return sales


@router.get("/stats/", response_model=dict)
def get_sales_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get sales statistics"""
    # Count sales by status
    total_sales = db.query(Sale).filter(Sale.user_id == current_user.id).count()
    pending_sales = db.query(Sale).filter(
        Sale.user_id == current_user.id,
        Sale.status == SaleStatus.PENDING
    ).count()
    successful_sales = db.query(Sale).filter(
        Sale.user_id == current_user.id,
        Sale.status == SaleStatus.SUCCESS
    ).count()
    failed_sales = db.query(Sale).filter(
        Sale.user_id == current_user.id,
        Sale.status == SaleStatus.FAILED
    ).count()
    
    # Calculate total revenue from successful sales
    successful_sales_records = db.query(Sale).filter(
        Sale.user_id == current_user.id,
        Sale.status == SaleStatus.SUCCESS
    ).all()
    
    total_revenue = sum(sale.total_amount for sale in successful_sales_records)
    
    return {
        "total_sales": total_sales,
        "pending_sales": pending_sales,
        "successful_sales": successful_sales,
        "failed_sales": failed_sales,
        "total_revenue": total_revenue,
        "success_rate": (successful_sales / total_sales * 100) if total_sales > 0 else 0
    }
