from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import func, desc, extract
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional  # เพิ่ม Optional ตรงนี้
from datetime import datetime, timedelta

from ...database import get_db
from ...models.user import User
from ...models.receipt import Receipt
from ...schemas.analytics import (
    ExpenseSummary, 
    MonthlyExpense,
    VendorExpense,
    CategoryExpense
)
from ...services.auth_service import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])

# ขั้นตอนที่ 3: เพิ่ม endpoint สำหรับสรุปค่าใช้จ่ายทั้งหมด
@router.get("/summary", response_model=ExpenseSummary)
def get_expense_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """ดึงข้อมูลสรุปค่าใช้จ่ายทั้งหมด"""
    
    # คำนวณสรุปค่าใช้จ่าย
    query = db.query(
        func.sum(Receipt.amount).label("total"),
        func.avg(Receipt.amount).label("average"),
        func.max(Receipt.amount).label("max"),
        func.min(Receipt.amount).label("min"),
        func.count(Receipt.id).label("count")
    ).filter(Receipt.user_id == current_user.id)
    
    result = query.first()
    
    if not result or result.count == 0:
        return ExpenseSummary(
            total_expense=0,
            average_monthly=0,
            max_expense=0,
            min_expense=0,
            receipt_count=0
        )
    
    # คำนวณค่าเฉลี่ยรายเดือน
    months_data = db.query(
        extract('year', Receipt.receipt_date).label('year'),
        extract('month', Receipt.receipt_date).label('month'),
        func.sum(Receipt.amount).label('total')
    ).filter(
        Receipt.user_id == current_user.id
    ).group_by(
        extract('year', Receipt.receipt_date),
        extract('month', Receipt.receipt_date)
    ).all()
    
    avg_monthly = result.total / len(months_data) if months_data else result.total
    
    return ExpenseSummary(
        total_expense=result.total or 0,
        average_monthly=avg_monthly,
        max_expense=result.max or 0,
        min_expense=result.min or 0,
        receipt_count=result.count or 0
    )
    
@router.get("/monthly", response_model=List[MonthlyExpense])
def get_monthly_expenses(
    year: Optional[int] = None,
    months: Optional[int] = 12,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """ดึงข้อมูลค่าใช้จ่ายรายเดือน"""
    
    # ถ้าไม่ระบุปี ให้ใช้ปีปัจจุบัน
    if not year:
        year = datetime.now().year
    
    # สร้างคำสั่ง SQL สำหรับดึงข้อมูลรายเดือน
    query = db.query(
        extract('year', Receipt.receipt_date).label('year'),
        extract('month', Receipt.receipt_date).label('month'),
        func.sum(Receipt.amount).label('total'),
        func.count(Receipt.id).label('count')
    ).filter(
        Receipt.user_id == current_user.id
    )
    
    if year:
        query = query.filter(extract('year', Receipt.receipt_date) == year)
    
    query = query.group_by(
        extract('year', Receipt.receipt_date),
        extract('month', Receipt.receipt_date)
    ).order_by(
        desc(extract('year', Receipt.receipt_date)),
        desc(extract('month', Receipt.receipt_date))
    ).limit(months)
    
    results = query.all()
    
    # แปลงผลลัพธ์เป็นรูปแบบที่ต้องการ
    month_names = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", 
                  "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
    
    return [
        MonthlyExpense(
            year=int(item.year),
            month=int(item.month),
            month_name=month_names[int(item.month) - 1],
            total=float(item.total) if item.total else 0,
            receipt_count=item.count
        )
        for item in results
    ]
    
@router.get("/vendors", response_model=List[VendorExpense])
def get_vendor_expenses(
    limit: Optional[int] = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """ดึงข้อมูลค่าใช้จ่ายตามผู้ให้บริการ"""
    
    # คำนวณค่าใช้จ่ายรวมทั้งหมด
    total_query = db.query(func.sum(Receipt.amount)).filter(Receipt.user_id == current_user.id)
    total_expense = total_query.scalar() or 0
    
    # สร้างคำสั่ง SQL สำหรับดึงข้อมูลตามผู้ให้บริการ
    query = db.query(
        Receipt.vendor_name,
        func.sum(Receipt.amount).label('total'),
        func.count(Receipt.id).label('count')
    ).filter(
        Receipt.user_id == current_user.id
    ).group_by(
        Receipt.vendor_name
    ).order_by(
        desc(func.sum(Receipt.amount))
    ).limit(limit)
    
    results = query.all()
    
    # แปลงผลลัพธ์เป็นรูปแบบที่ต้องการ
    return [
        VendorExpense(
            vendor_name=item.vendor_name or "ไม่ระบุ",
            total=float(item.total) if item.total else 0,
            receipt_count=item.count,
            percentage=round((item.total / total_expense) * 100, 2) if total_expense > 0 else 0
        )
        for item in results
    ]
    
@router.get("/categories", response_model=List[CategoryExpense])
def get_category_expenses(
    limit: Optional[int] = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """ดึงข้อมูลค่าใช้จ่ายตามหมวดหมู่"""
    
    # คำนวณค่าใช้จ่ายรวมทั้งหมด
    total_query = db.query(func.sum(Receipt.amount)).filter(Receipt.user_id == current_user.id)
    total_expense = total_query.scalar() or 0
    
    # สร้างคำสั่ง SQL สำหรับดึงข้อมูลตามหมวดหมู่
    from ...models.category import Category
    
    query = db.query(
        Category.name.label('category_name'),
        func.sum(Receipt.amount).label('total'),
        func.count(Receipt.id).label('count')
    ).join(
        Category, Receipt.category_id == Category.id
    ).filter(
        Receipt.user_id == current_user.id
    ).group_by(
        Category.name
    ).order_by(
        desc(func.sum(Receipt.amount))
    ).limit(limit)
    
    results = query.all()
    
    # แปลงผลลัพธ์เป็นรูปแบบที่ต้องการ
    return [
        CategoryExpense(
            category_name=item.category_name or "ไม่ระบุหมวดหมู่",
            total=float(item.total) if item.total else 0,
            receipt_count=item.count,
            percentage=round((item.total / total_expense) * 100, 2) if total_expense > 0 else 0
        )
        for item in results
    ]    