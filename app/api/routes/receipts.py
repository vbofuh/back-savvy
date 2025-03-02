from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from ...database import get_db
from ...models.user import User
from ...models.receipt import Receipt
from ...schemas.receipt import ReceiptCreate, ReceiptUpdate, ReceiptResponse
from ...services.auth_service import get_current_user

router = APIRouter(prefix="/receipts", tags=["receipts"])

@router.post("/", response_model=ReceiptResponse)
def create_receipt(
    receipt: ReceiptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """สร้างใบเสร็จใหม่"""
    db_receipt = Receipt(
        user_id=current_user.id,
        email_id=receipt.email_id,
        email_subject=receipt.email_subject,
        email_from=receipt.email_from,
        email_date=receipt.email_date,
        vendor_name=receipt.vendor_name,
        category_id=receipt.category_id,
        receipt_date=receipt.receipt_date or datetime.now(),
        amount=receipt.amount,
        currency=receipt.currency,
        receipt_number=receipt.receipt_number,
        payment_method=receipt.payment_method,
        notes=receipt.notes,
        receipt_file_path=receipt.receipt_file_path
    )
    
    db.add(db_receipt)
    db.commit()
    db.refresh(db_receipt)
    
    return db_receipt

@router.get("/", response_model=List[ReceiptResponse])
def get_receipts(
    skip: int = 0,
    limit: int = 100,
    vendor: Optional[str] = None,
    category_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """ดึงรายการใบเสร็จทั้งหมดของผู้ใช้ พร้อมตัวกรอง"""
    query = db.query(Receipt).filter(Receipt.user_id == current_user.id)
    
    # เพิ่มตัวกรอง
    if vendor:
        query = query.filter(Receipt.vendor_name.ilike(f"%{vendor}%"))
    
    if category_id:
        query = query.filter(Receipt.category_id == category_id)
    
    if start_date:
        query = query.filter(Receipt.receipt_date >= start_date)
    
    if end_date:
        query = query.filter(Receipt.receipt_date <= end_date)
    
    if min_amount is not None:
        query = query.filter(Receipt.amount >= min_amount)
    
    if max_amount is not None:
        query = query.filter(Receipt.amount <= max_amount)
    
    # เรียงลำดับตามวันที่ใบเสร็จ จากใหม่ไปเก่า
    query = query.order_by(Receipt.receipt_date.desc())
    
    receipts = query.offset(skip).limit(limit).all()
    return receipts

@router.get("/{receipt_id}", response_model=ReceiptResponse)
def get_receipt(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """ดึงข้อมูลใบเสร็จตาม ID"""
    receipt = db.query(Receipt).filter(
        Receipt.id == receipt_id,
        Receipt.user_id == current_user.id
    ).first()
    
    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ไม่พบใบเสร็จ"
        )
    
    return receipt

@router.put("/{receipt_id}", response_model=ReceiptResponse)
def update_receipt(
    receipt_id: int,
    receipt_update: ReceiptUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """อัปเดตข้อมูลใบเสร็จ"""
    db_receipt = db.query(Receipt).filter(
        Receipt.id == receipt_id,
        Receipt.user_id == current_user.id
    ).first()
    
    if not db_receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ไม่พบใบเสร็จ"
        )
    
    # อัปเดตฟิลด์ที่ไม่เป็น None
    update_data = receipt_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_receipt, key, value)
    
    db.commit()
    db.refresh(db_receipt)
    
    return db_receipt

@router.delete("/{receipt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_receipt(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """ลบใบเสร็จ"""
    db_receipt = db.query(Receipt).filter(
        Receipt.id == receipt_id,
        Receipt.user_id == current_user.id
    ).first()
    
    if not db_receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ไม่พบใบเสร็จ"
        )
    
    db.delete(db_receipt)
    db.commit()
    
    return None