from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

class Receipt(Base):
    __tablename__ = "receipts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    email_id = Column(String(255), index=True, nullable=True)
    email_subject = Column(String(255), nullable=True)
    email_from = Column(String(100), index=True, nullable=True)
    email_date = Column(DateTime, nullable=True)
    vendor_name = Column(String(100), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    receipt_date = Column(DateTime, index=True, nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="THB")
    receipt_number = Column(String(50), nullable=True)
    payment_method = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    receipt_file_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    # ความสัมพันธ์กับตารางอื่น
    user = relationship("User", back_populates="receipts")
    category = relationship("Category", back_populates="receipts")