from sqlalchemy.orm import Session
from ..models.category import Category

def create_initial_categories(db):
    """สร้างหมวดหมู่เริ่มต้น"""
    # ตรวจสอบว่ามีหมวดหมู่อยู่แล้วหรือไม่
    from ..models.category import Category
    
    if db.query(Category).count() > 0:
        return
    
    categories = [
        {"name": "ช้อปปิ้ง", "description": "ช้อปปิ้งออนไลน์และห้างร้าน", "is_default": True},
        {"name": "ความบันเทิง", "description": "เกม, เพลง, หนัง, และบริการสตรีมมิ่ง", "is_default": True},
        {"name": "ธนาคาร", "description": "การทำธุรกรรมทางการเงิน", "is_default": True},
        {"name": "อื่นๆ", "description": "รายการที่ไม่เข้าหมวดหมู่ใด", "is_default": True}
    ]
    
    for category_data in categories:
        category = Category(**category_data)
        db.add(category)
    
    db.commit()
    
def update_categories(db):
    """อัปเดตหมวดหมู่ให้เป็นไปตามที่กำหนด"""
    from ..models.category import Category
    
    # ลบหมวดหมู่ที่ไม่ต้องการแล้ว
    db.query(Category).filter(Category.name.in_(["อาหารและเครื่องดื่ม", "ค่าสาธารณูปโภค"])).delete(synchronize_session=False)
    
    # ตรวจสอบว่ามีหมวดหมู่ที่ต้องการแล้วหรือไม่
    required_categories = ["ช้อปปิ้ง", "ความบันเทิง", "ธนาคาร", "อื่นๆ"]
    for cat_name in required_categories:
        if not db.query(Category).filter(Category.name == cat_name).first():
            # ถ้ายังไม่มี ให้สร้างใหม่
            description = ""
            if cat_name == "ช้อปปิ้ง":
                description = "ช้อปปิ้งออนไลน์และห้างร้าน"
            elif cat_name == "ความบันเทิง":
                description = "เกม, เพลง, หนัง, และบริการสตรีมมิ่ง"
            elif cat_name == "ธนาคาร":
                description = "การทำธุรกรรมทางการเงิน"
            elif cat_name == "อื่นๆ":
                description = "รายการที่ไม่เข้าหมวดหมู่ใด"
            
            category = Category(name=cat_name, description=description, is_default=True)
            db.add(category)
    
    db.commit()