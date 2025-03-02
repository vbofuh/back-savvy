from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class ImapSettingBase(BaseModel):
    email: EmailStr
    server: str
    port: int = 993
    username: str
    use_ssl: bool = True
    folder: str = "INBOX"

class ImapSettingCreate(ImapSettingBase):
    password: str

class ImapSettingUpdate(BaseModel):
    email: Optional[EmailStr] = None
    server: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    use_ssl: Optional[bool] = None
    folder: Optional[str] = None

class ImapSettingResponse(ImapSettingBase):
    id: int
    user_id: int
    last_sync: Optional[datetime] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}