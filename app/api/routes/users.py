from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ...database import get_db
from ...models.user import User
from ...schemas.user import UserCreate, UserUpdate, UserResponse
from ...services.auth_service import get_password_hash, get_current_user

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # ตรวจสอบว่ามีอีเมลซ้ำหรือไม่
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="อีเมลนี้มีในระบบแล้ว")
    
    # ตรวจสอบว่ามีชื่อผู้ใช้ซ้ำหรือไม่
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="ชื่อผู้ใช้นี้มีในระบบแล้ว")
    
    # สร้างรหัสผ่านแบบ hash
    hashed_password = get_password_hash(user.password)
    
    # สร้างผู้ใช้ใหม่
    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        full_name=user.full_name
    )
    
    # บันทึกลงฐานข้อมูล
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserResponse)
def update_user(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # อัปเดตข้อมูลที่ไม่ว่าง
    if user_update.username is not None:
        # ตรวจสอบว่ามีชื่อผู้ใช้ซ้ำหรือไม่
        db_user = db.query(User).filter(User.username == user_update.username).first()
        if db_user and db_user.id != current_user.id:
            raise HTTPException(status_code=400, detail="ชื่อผู้ใช้นี้มีในระบบแล้ว")
        current_user.username = user_update.username
    
    if user_update.email is not None:
        # ตรวจสอบว่ามีอีเมลซ้ำหรือไม่
        db_user = db.query(User).filter(User.email == user_update.email).first()
        if db_user and db_user.id != current_user.id:
            raise HTTPException(status_code=400, detail="อีเมลนี้มีในระบบแล้ว")
        current_user.email = user_update.email
    
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    
    if user_update.password is not None:
        current_user.password_hash = get_password_hash(user_update.password)
    
    # บันทึกการเปลี่ยนแปลง
    db.commit()
    db.refresh(current_user)
    
    return current_user