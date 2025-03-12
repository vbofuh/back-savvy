from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

class Budget(Base):
    __tablename__ = "budgets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Float, nullable=False)
    month = Column(Integer, nullable=False)  # 1-12
    year = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # ความสัมพันธ์
    user = relationship("User", back_populates="budgets")
    category = relationship("Category")

# schemas/budget.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class BudgetBase(BaseModel):
    category_id: int
    amount: float
    month: int
    year: int

class BudgetCreate(BudgetBase):
    pass

class BudgetUpdate(BaseModel):
    category_id: Optional[int] = None
    amount: Optional[float] = None
    month: Optional[int] = None
    year: Optional[int] = None

class BudgetResponse(BudgetBase):
    id: int
    user_id: int
    created_at: datetime
    
    model_config = {"from_attributes": True}

class BudgetWithSpentResponse(BudgetResponse):
    category_name: str
    spent: float
    percentage: float