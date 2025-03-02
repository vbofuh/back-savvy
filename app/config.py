import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from cryptography.fernet import Fernet

class Settings(BaseSettings):
    # เพิ่ม encryption key
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
    
    # Database
    DATABASE_URL: str = "mysql+pymysql://root@localhost:3308/receipt_manager"
    
    # JWT Authentication
    SECRET_KEY: str = "YOUR_SECRET_KEY_HERE"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    CORS_ORIGINS: list = ["http://localhost:3000"]
    API_V1_PREFIX: str = "/api/v1"
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()