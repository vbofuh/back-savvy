from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

class ImapSetting(Base):
    __tablename__ = "imap_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(100), nullable=False)
    server = Column(String(100), nullable=False)
    port = Column(Integer, default=993, nullable=False)
    username = Column(String(100), nullable=False)
    password_encrypted = Column(String(255), nullable=False)
    use_ssl = Column(Boolean, default=True)
    folder = Column(String(50), default="INBOX")
    last_sync = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    # ความสัมพันธ์
    user = relationship("User", back_populates="imap_settings")