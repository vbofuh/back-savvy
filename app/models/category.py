from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship  # เพิ่ม import นี้
from ..database import Base

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    
    # เพิ่มฟิลด์เพื่อระบุว่าเป็นหมวดหมู่เริ่มต้นหรือไม่
    is_default = Column(Boolean, default=False)
    receipts = relationship("Receipt", back_populates="category")