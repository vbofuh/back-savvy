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