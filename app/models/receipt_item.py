from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text
from sqlalchemy.sql import func
from ..database import Base

class ReceiptItem(Base):
    __tablename__ = "receipt_items"
    
    id = Column(Integer, primary_key=True, index=True)
    receipt_id = Column(Integer, ForeignKey("receipts.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    quantity = Column(Float, default=1)
    price = Column(Float, nullable=False)
    total = Column(Float, nullable=False)