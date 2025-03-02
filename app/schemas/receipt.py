from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ReceiptBase(BaseModel):
    email_subject: Optional[str] = None
    email_from: Optional[str] = None
    email_date: Optional[datetime] = None
    vendor_name: Optional[str] = None
    category_id: Optional[int] = None
    receipt_date: Optional[datetime] = None
    amount: float
    currency: str = "THB"
    receipt_number: Optional[str] = None
    payment_method: Optional[str] = None
    notes: Optional[str] = None

class ReceiptCreate(ReceiptBase):
    email_id: Optional[str] = None
    receipt_file_path: Optional[str] = None

class ReceiptUpdate(BaseModel):
    email_subject: Optional[str] = None
    email_from: Optional[str] = None
    email_date: Optional[datetime] = None
    vendor_name: Optional[str] = None
    category_id: Optional[int] = None
    receipt_date: Optional[datetime] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    receipt_number: Optional[str] = None
    payment_method: Optional[str] = None
    notes: Optional[str] = None
    receipt_file_path: Optional[str] = None

class ReceiptResponse(ReceiptBase):
    id: int
    user_id: int
    email_id: Optional[str] = None
    receipt_file_path: Optional[str] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}