"""
پایه دیتابیس مالی - Financial Database Base

دیتابیس جداگانه برای سیستم مالی
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path

# Base برای تمام مدل‌های مالی
FinancialBase = declarative_base()

# مسیر دیتابیس مالی
FINANCIAL_DB_PATH = os.getenv(
    'FINANCIAL_DATABASE_URL',
    'sqlite:///data/financial/gt_financial.db'
)

# ایجاد پوشه در صورت عدم وجود
if FINANCIAL_DB_PATH.startswith('sqlite:///'):
    db_file_path = FINANCIAL_DB_PATH.replace('sqlite:///', '')
    Path(db_file_path).parent.mkdir(parents=True, exist_ok=True)

# ایجاد Engine
if FINANCIAL_DB_PATH.startswith('sqlite'):
    financial_engine = create_engine(
        FINANCIAL_DB_PATH,
        echo=False,
        connect_args={"check_same_thread": False}
    )
else:
    # برای PostgreSQL
    financial_engine = create_engine(
        FINANCIAL_DB_PATH,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

# Session Factory
FinancialSessionLocal = sessionmaker(
    bind=financial_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)


def get_financial_db():
    """
    دریافت session دیتابیس مالی
    
    Yields:
        Session object
    """
    db = FinancialSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_financial_session():
    """
    دریافت session دیتابیس مالی (برای استفاده مستقیم)
    
    Returns:
        Session object
    """
    return FinancialSessionLocal()


def init_financial_db():
    """
    ایجاد تمام جداول در دیتابیس مالی
    """
    # Import models to register them with SQLAlchemy
    from app.models.financial import (
        Account, AccountGold, AccountSilver, Sale, Customer, Payment,
        SheetImport, RawData, FieldMapping, Platform,
        DiscrepancyReport, CustomReport, ImportBatch
    )
    
    FinancialBase.metadata.create_all(bind=financial_engine)
    print("✅ دیتابیس مالی با موفقیت ایجاد شد!")


def drop_financial_db():
    """
    حذف تمام جداول از دیتابیس مالی
    """
    FinancialBase.metadata.drop_all(bind=financial_engine)
    print("🗑️ دیتابیس مالی حذف شد!")
