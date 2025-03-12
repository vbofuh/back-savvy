from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    receipts = relationship("Receipt", back_populates="user", cascade="all, delete-orphan")
    
    # เพิ่มความสัมพันธ์ในคลาส User
    imap_settings = relationship("ImapSetting", back_populates="user", cascade="all, delete-orphan")
    
    # อ้างถึง Budget ด้วยชื่อเป็น string แทนการ import คลาส
    budgets = relationship("Budget", back_populates="user", cascade="all, delete-orphan")