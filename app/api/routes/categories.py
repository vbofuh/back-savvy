from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ...database import get_db
from ...models.user import User
from ...models.category import Category
from ...schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from ...services.auth_service import get_current_user

router = APIRouter(prefix="/categories", tags=["categories"])

@router.post("/", response_model=CategoryResponse)
def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db)
):
    """สร้างหมวดหมู่ใหม่"""
    # ตรวจสอบว่ามีหมวดหมู่นี้อยู่แล้วหรือไม่
    db_category = db.query(Category).filter(Category.name == category.name).first()
    if db_category:
        return db_category
    
    db_category = Category(
        name=category.name,
        color=category.color,
        icon=category.icon
    )
    
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    
    return db_category

@router.get("/", response_model=List[CategoryResponse])
def get_categories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """ดึงรายการหมวดหมู่ทั้งหมด"""
    categories = db.query(Category).offset(skip).limit(limit).all()
    return categories

@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """ดึงข้อมูลหมวดหมู่ตาม ID"""
    category = db.query(Category).filter(Category.id == category_id).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ไม่พบหมวดหมู่"
        )
    
    return category

@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    category_update: CategoryUpdate,
    db: Session = Depends(get_db)
):
    """อัปเดตข้อมูลหมวดหมู่"""
    db_category = db.query(Category).filter(Category.id == category_id).first()
    
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ไม่พบหมวดหมู่"
        )
    
    # อัปเดตฟิลด์ที่ไม่เป็น None
    update_data = category_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_category, key, value)
    
    db.commit()
    db.refresh(db_category)
    
    return db_category