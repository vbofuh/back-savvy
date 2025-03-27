from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.budget import Budget
from app.schemas.budget import BudgetCreate, BudgetUpdate, BudgetResponse, BudgetWithSpentResponse
from app.services.auth_service import get_current_user


router = APIRouter(prefix="/budgets", tags=["budgets"])

@router.post("/", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def create_budget(
    budget: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """สร้างงบประมาณใหม่"""
    # ตรวจสอบว่ามีงบประมาณสำหรับหมวดหมู่นี้ในเดือนและปีที่เลือกอยู่แล้วหรือไม่
    existing_budget = db.query(Budget).filter(
        Budget.user_id == current_user.id,
        Budget.category_id == budget.category_id,
        Budget.month == budget.month,
        Budget.year == budget.year
    ).first()
    
    if existing_budget:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="คุณมีงบประมาณสำหรับหมวดหมู่นี้ในเดือนนี้อยู่แล้ว"
        )
    
    # สร้างงบประมาณใหม่
    db_budget = Budget(
        user_id=current_user.id,
        category_id=budget.category_id,
        amount=budget.amount,
        month=budget.month,
        year=budget.year
    )
    
    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)
    
    return db_budget

@router.get("/", response_model=List[BudgetResponse])
def get_budgets(
    month: Optional[int] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """ดึงรายการงบประมาณทั้งหมดของผู้ใช้"""
    query = db.query(Budget).filter(Budget.user_id == current_user.id)
    
    # กรองตามเดือนและปี (ถ้ามี)
    if month is not None:
        query = query.filter(Budget.month == month)
    
    if year is not None:
        query = query.filter(Budget.year == year)
    
    # เรียงลำดับตามปี เดือน และหมวดหมู่
    query = query.order_by(Budget.year, Budget.month, Budget.category_id)
    
    return query.all()

@router.get("/{budget_id}", response_model=BudgetResponse)
def get_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """ดึงข้อมูลงบประมาณตาม ID"""
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id
    ).first()
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ไม่พบงบประมาณ"
        )
    
    return budget

@router.put("/{budget_id}", response_model=BudgetResponse)
def update_budget(
    budget_id: int,
    budget_update: BudgetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """อัปเดตข้อมูลงบประมาณ"""
    db_budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id
    ).first()
    
    if not db_budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ไม่พบงบประมาณ"
        )
    
    # ตรวจสอบการซ้ำกัน ถ้ามีการเปลี่ยนหมวดหมู่ เดือน หรือปี
    if ((budget_update.category_id is not None and budget_update.category_id != db_budget.category_id) or 
        (budget_update.month is not None and budget_update.month != db_budget.month) or 
        (budget_update.year is not None and budget_update.year != db_budget.year)):
        
        # ใช้ค่าเดิมถ้าไม่มีการอัปเดต
        category_id = budget_update.category_id if budget_update.category_id is not None else db_budget.category_id
        month = budget_update.month if budget_update.month is not None else db_budget.month
        year = budget_update.year if budget_update.year is not None else db_budget.year
        
        # ตรวจสอบว่ามีงบประมาณซ้ำกันหรือไม่
        existing_budget = db.query(Budget).filter(
            Budget.user_id == current_user.id,
            Budget.category_id == category_id,
            Budget.month == month,
            Budget.year == year,
            Budget.id != budget_id  # ไม่นับตัวเอง
        ).first()
        
        if existing_budget:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="คุณมีงบประมาณสำหรับหมวดหมู่นี้ในเดือนนี้อยู่แล้ว"
            )
    
    # อัปเดตฟิลด์ที่ไม่เป็น None
    update_data = budget_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_budget, key, value)
    
    db.commit()
    db.refresh(db_budget)
    
    return db_budget

@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """ลบงบประมาณ"""
    db_budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id
    ).first()
    
    if not db_budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ไม่พบงบประมาณ"
        )
    
    db.delete(db_budget)
    db.commit()
    
    return None

# routes/analytics.py (เพิ่ม endpoint ใหม่)
@router.get("/budget-comparison", response_model=List[BudgetWithSpentResponse])
def get_budget_comparison(
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """ดึงข้อมูลเปรียบเทียบงบประมาณกับค่าใช้จ่ายจริง"""
    # ถ้าไม่ระบุเดือนและปี ให้ใช้เดือนและปีปัจจุบัน
    if month is None or year is None:
        today = datetime.now()
        month = month or today.month
        year = year or today.year
    
    # ใช้ common table expression (CTE) ใน SQLAlchemy
    from sqlalchemy import func, text
    from sqlalchemy.sql import select
    from ..models.receipt import Receipt
    from ..models.category import Category
    
    # สร้าง subquery สำหรับค่าใช้จ่ายจริงในแต่ละหมวดหมู่
    expenses_subquery = (
        db.query(
            Receipt.category_id,
            func.sum(Receipt.amount).label('total_spent')
        )
        .filter(
            Receipt.user_id == current_user.id,
            func.extract('month', Receipt.receipt_date) == month,
            func.extract('year', Receipt.receipt_date) == year
        )
        .group_by(Receipt.category_id)
        .subquery()
    )
    
    # ดึงข้อมูลงบประมาณพร้อมค่าใช้จ่ายจริง
    results = (
        db.query(
            Budget.id,
            Budget.user_id,
            Budget.category_id,
            Category.name.label('category_name'),
            Budget.amount,
            Budget.month,
            Budget.year,
            Budget.created_at,
            func.coalesce(expenses_subquery.c.total_spent, 0).label('spent')
        )
        .join(Category, Budget.category_id == Category.id)
        .outerjoin(expenses_subquery, Budget.category_id == expenses_subquery.c.category_id)
        .filter(
            Budget.user_id == current_user.id,
            Budget.month == month,
            Budget.year == year
        )
        .all()
    )
    
    # คำนวณเปอร์เซ็นต์การใช้จ่าย
    response_data = []
    for row in results:
        percentage = round((row.spent / row.amount * 100) if row.amount > 0 else 0)
        
        response_data.append({
            "id": row.id,
            "user_id": row.user_id,
            "category_id": row.category_id,
            "category_name": row.category_name,
            "amount": row.amount,
            "month": row.month,
            "year": row.year,
            "created_at": row.created_at,
            "spent": row.spent,
            "percentage": percentage
        })
    
    return response_data