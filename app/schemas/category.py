from pydantic import BaseModel
from typing import Optional

class CategoryBase(BaseModel):
    name: str
    color: Optional[str] = "#3498db"
    icon: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None

class CategoryResponse(CategoryBase):
    id: int
    
    model_config = {"from_attributes": True}