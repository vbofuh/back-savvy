from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime

class ExpenseSummary(BaseModel):
    total_expense: float
    average_monthly: float
    max_expense: float
    min_expense: float
    receipt_count: int
    
class MonthlyExpense(BaseModel):
    year: int
    month: int
    month_name: str
    total: float
    receipt_count: int
    
class VendorExpense(BaseModel):
    vendor_name: str
    total: float
    receipt_count: int
    percentage: float
    
class CategoryExpense(BaseModel):
    category_name: str
    total: float
    receipt_count: int
    percentage: float