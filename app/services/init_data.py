from sqlalchemy.orm import Session
from ..models.category import Category

def create_initial_categories(db: Session):
    """สร้างข้อมูลหมวดหมู่เริ่มต้น"""
    # รายการหมวดหมู่เริ่มต้น
    default_categories = [
        {"name": "อาหารและเครื่องดื่ม", "color": "#e74c3c", "icon": "food"},
        {"name": "ช้อปปิ้ง", "color": "#3498db", "icon": "shopping"},
        {"name": "บิลและสาธารณูปโภค", "color": "#2ecc71", "icon": "utility"},
        {"name": "การเดินทาง", "color": "#f39c12", "icon": "travel"},
        {"name": "ความบันเทิง", "color": "#9b59b6", "icon": "entertainment"},
        {"name": "สุขภาพ", "color": "#1abc9c", "icon": "health"},
        {"name": "อื่นๆ", "color": "#95a5a6", "icon": "other"}
    ]
    
    # ตรวจสอบว่ามีหมวดหมู่อยู่แล้วหรือไม่
    existing_count = db.query(Category).count()
    if existing_count > 0:
        return
    
    # สร้างหมวดหมู่เริ่มต้น
    for category_data in default_categories:
        category = Category(**category_data)
        db.add(category)
    
    db.commit()