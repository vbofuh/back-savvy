from pydantic import BaseModel
from typing import Optional, List

class ReceiptItemBase(BaseModel):
    name: str
    quantity: float = 1.0
    price: float
    total: float

class ReceiptItemCreate(ReceiptItemBase):
    receipt_id: int

class ReceiptItemUpdate(BaseModel):
    name: Optional[str] = None
    quantity: Optional[float] = None
    price: Optional[float] = None
    total: Optional[float] = None

class ReceiptItemInDB(ReceiptItemBase):
    id: int
    receipt_id: int

    class Config:
        orm_mode = True

class ReceiptItemResponse(ReceiptItemInDB):
    pass