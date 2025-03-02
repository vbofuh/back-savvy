from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import logging

from ...database import get_db
from ...schemas.token import Token
from ...services.auth_service import authenticate_user, create_access_token, get_user_by_email
from ...config import settings

# เพิ่ม logging สำหรับการดีบัก
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["authentication"])

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    # เพิ่มการบันทึกล็อกเพื่อดีบัก
    logger.info(f"พยายามล็อกอินด้วย username: {form_data.username}")
    
    # ตรวจสอบว่ามีผู้ใช้ตามอีเมลที่ให้มาหรือไม่
    user = get_user_by_email(db, form_data.username)
    if not user:
        logger.warning(f"ไม่พบผู้ใช้สำหรับอีเมล: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="อีเมลหรือรหัสผ่านไม่ถูกต้อง",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # ยืนยันตัวตนผู้ใช้
    authenticated_user = authenticate_user(db, form_data.username, form_data.password)
    if not authenticated_user:
        logger.warning(f"รหัสผ่านไม่ถูกต้องสำหรับอีเมล: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="อีเมลหรือรหัสผ่านไม่ถูกต้อง",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # สร้าง token
    access_token = create_access_token(
        data={"sub": authenticated_user.email}
    )
    logger.info(f"ล็อกอินสำเร็จสำหรับอีเมล: {form_data.username}")
    
    return {"access_token": access_token, "token_type": "bearer"}