from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .config import settings
from .models import User, Category, Receipt
from .api.routes import auth_router, users_router, receipts_router, categories_router
from .services.init_data import create_initial_categories
from .database import SessionLocal
from .api.routes import auth_router, users_router, receipts_router, categories_router, imap_settings_router

# สร้างตารางในฐานข้อมูล
Base.metadata.create_all(bind=engine)

# สร้างข้อมูลหมวดหมู่เริ่มต้น
db = SessionLocal()
create_initial_categories(db)
db.close()

app = FastAPI(
    title="Receipt Manager API",
    description="API for managing receipts extracted from emails via IMAP",
    version="1.0.0"
)

# เพิ่ม CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# รวม routers
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(users_router, prefix=settings.API_V1_PREFIX)
app.include_router(receipts_router, prefix=settings.API_V1_PREFIX)
app.include_router(categories_router, prefix=settings.API_V1_PREFIX)
app.include_router(imap_settings_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def read_root():
    return {"message": "Welcome to Receipt Manager API"}