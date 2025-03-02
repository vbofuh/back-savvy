from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from ..database import Base

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    color = Column(String(20), default="#3498db")
    icon = Column(String(30), nullable=True)
    
    # ความสัมพันธ์กับตารางอื่น
    receipts = relationship("Receipt", back_populates="category")