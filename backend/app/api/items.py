from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models import Item, User
from app.schemas import (
    ItemCreate, ItemUpdate, ItemResponse, ItemStockUpdate, ItemSearch
)
from app.api.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=List[ItemResponse])
def get_all_items(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    search: Optional[str] = Query(None, description="Search by item name"),
    low_stock_only: bool = Query(False, description="Show only low stock items"),
    out_of_stock_only: bool = Query(False, description="Show only out of stock items"),
    active_only: bool = Query(True, description="Show only active items"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all items with optional filtering"""
    query = db.query(Item)
    
    # Apply filters
    if active_only:
        query = query.filter(Item.is_active == True)
    
    if search:
        query = query.filter(
            or_(
                Item.name.ilike(f"%{search}%"),
                Item.description.ilike(f"%{search}%")
            )
        )
    
    if out_of_stock_only:
        query = query.filter(Item.quantity <= 0)
    elif low_stock_only:
        query = query.filter(Item.quantity < 10, Item.quantity > 0)
    
    items = query.offset(skip).limit(limit).all()
    return items


@router.get("/{item_id}", response_model=ItemResponse)
def get_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific item by ID"""
    item = db.query(Item).filter(Item.id == item_id).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    return item


@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    item_data: ItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new item"""
    # Check if item with same name already exists
    existing_item = db.query(Item).filter(Item.name == item_data.name).first()
    if existing_item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item with this name already exists"
        )
    
    # Create new item
    db_item = Item(
        name=item_data.name,
        quantity=item_data.quantity,
        price=item_data.price,
        description=item_data.description
    )
    
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    return db_item


@router.put("/{item_id}", response_model=ItemResponse)
def update_item(
    item_id: int,
    item_data: ItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing item"""
    item = db.query(Item).filter(Item.id == item_id).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    # Check if name is being changed and already exists
    if item_data.name and item_data.name != item.name:
        existing_item = db.query(Item).filter(
            Item.name == item_data.name,
            Item.id != item_id
        ).first()
        if existing_item:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Item with this name already exists"
            )
    
    # Update item fields
    update_data = item_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)
    
    db.commit()
    db.refresh(item)
    
    return item


@router.patch("/{item_id}/stock", response_model=ItemResponse)
def update_item_stock(
    item_id: int,
    stock_update: ItemStockUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update item stock quantity with different operations"""
    item = db.query(Item).filter(Item.id == item_id).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    # Apply stock operation
    if stock_update.operation == "set":
        item.quantity = stock_update.quantity
    elif stock_update.operation == "add":
        item.quantity += stock_update.quantity
    elif stock_update.operation == "subtract":
        new_quantity = item.quantity - stock_update.quantity
        if new_quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot subtract more than available quantity"
            )
        item.quantity = new_quantity
    
    db.commit()
    db.refresh(item)
    
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an item (soft delete by setting is_active to False)"""
    item = db.query(Item).filter(Item.id == item_id).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    # Soft delete - set is_active to False
    item.is_active = False
    db.commit()
    
    return None


@router.get("/search/by-name/{item_name}", response_model=ItemResponse)
def search_item_by_name(
    item_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search for an item by exact name (case-insensitive)"""
    item = db.query(Item).filter(
        Item.name.ilike(item_name),
        Item.is_active == True
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item '{item_name}' not found"
        )
    
    return item


@router.get("/low-stock/", response_model=List[ItemResponse])
def get_low_stock_items(
    threshold: int = Query(10, ge=1, description="Low stock threshold"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all items with low stock"""
    items = db.query(Item).filter(
        Item.quantity < threshold,
        Item.quantity > 0,
        Item.is_active == True
    ).all()
    
    return items


@router.get("/out-of-stock/", response_model=List[ItemResponse])
def get_out_of_stock_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all items that are out of stock"""
    items = db.query(Item).filter(
        Item.quantity <= 0,
        Item.is_active == True
    ).all()
    
    return items
