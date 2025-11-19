"""
مدل‌های پایه دیتابیس
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Base برای تمام مدل‌ها
Base = declarative_base()

# تنظیمات دیتابیس
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/gt_land.db')

# ایجاد پوشه data در صورت عدم وجود
if DATABASE_URL.startswith('sqlite:///'):
    from pathlib import Path
    db_file_path = DATABASE_URL.replace('sqlite:///', '')
    Path(db_file_path).parent.mkdir(parents=True, exist_ok=True)

# ایجاد Engine
if DATABASE_URL.startswith('sqlite'):
    # تنظیمات SQLite
    engine = create_engine(
        DATABASE_URL,
        echo=False,  # برای دیباگ روی True قرار دهید
        connect_args={"check_same_thread": False}  # برای SQLite
    )
else:
    # تنظیمات PostgreSQL
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

# Session Factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)


def get_db():
    """
    دریافت session دیتابیس
    
    Yields:
        Session object
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    ایجاد تمام جداول در دیتابیس
    """
    Base.metadata.create_all(bind=engine)


def drop_db():
    """
    حذف تمام جداول از دیتابیس
    """
    Base.metadata.drop_all(bind=engine)
