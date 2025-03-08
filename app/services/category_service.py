from typing import Optional
from sqlalchemy.orm import Session
from ..models.category import Category

def auto_categorize_vendor(vendor_name: str, db: Session) -> Optional[int]:
    """จัดประเภทอัตโนมัติตามชื่อผู้ให้บริการ"""
    if not vendor_name:
        return None
    
    vendor_lower = vendor_name.lower()
    
    # กำหนดคำสำคัญสำหรับแต่ละหมวดหมู่
    category_keywords = {
        "ช้อปปิ้ง": ["shopee", "lazada", "tiktok shop", "amazon", "ebay", "alibaba", "jd central", "central", "powerbuy"],
        "ความบันเทิง": ["apple", "steam", "netflix", "disney", "spotify", "joox", "youtube", "prime video", "hbo", "game", "entertainment"],
        "ธนาคาร": ["ธนาคาร", "bank", "kasikorn", "kbank", "scb", "bangkok bank", "krungsri", "ธ.ก.ส.", "ออมสิน", "tmb", "ttb", "kiatnakin", "visa", "mastercard"]
    }
    
    # ค้นหาหมวดหมู่ที่ตรงกับคำสำคัญ
    for category_name, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword in vendor_lower:
                # ค้นหา category_id จากชื่อหมวดหมู่
                category = db.query(Category).filter(Category.name == category_name).first()
                if category:
                    return category.id
    
    # ถ้าไม่พบหมวดหมู่ที่ตรงกัน ให้ใช้หมวดหมู่ "อื่นๆ"
    other_category = db.query(Category).filter(Category.name == "อื่นๆ").first()
    if other_category:
        return other_category.id
    
    return None