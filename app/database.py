from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings
import pymysql
pymysql.install_as_MySQLdb()

# สร้าง engine สำหรับเชื่อมต่อฐานข้อมูล
engine = create_engine(settings.DATABASE_URL)

# สร้าง session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# สร้าง Base class สำหรับ models
Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()