"""
Stage 1: ImportBatch Model - مدیریت batch های import
=====================================================
⚠️ RawData مدل به dynamic_models.py منتقل شده است
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from datetime import datetime

from .base_financial import FinancialBase


class ImportBatch(FinancialBase):
    """
    اطلاعات هر دسته Import
    """
    __tablename__ = 'import_batches'
    
    id = Column(Integer, primary_key=True)
    batch_id = Column(String(50), nullable=False, unique=True, index=True)
    
    # مشخصات شیت
    sheet_name = Column(String(200), nullable=False)
    sheet_id = Column(String(100), nullable=True)
    sheet_url = Column(Text, nullable=True)
    
    # آمار
    total_rows = Column(Integer, default=0, comment="تعداد کل ردیف‌ها")
    new_rows = Column(Integer, default=0, comment="ردیف‌های جدید")
    updated_rows = Column(Integer, default=0, comment="ردیف‌های بروز شده")
    unchanged_rows = Column(Integer, default=0, comment="ردیف‌های بدون تغییر")
    error_rows = Column(Integer, default=0, comment="ردیف‌های خطا")
    
    # تنظیمات
    unique_key_fields = Column(JSON, nullable=True, comment="فیلدهای استفاده شده در unique key")
    field_mappings = Column(JSON, nullable=True, comment="نگاشت فیلدها")
    
    # وضعیت
    status = Column(String(50), default='running', comment="running, completed, failed")
    error_message = Column(Text, nullable=True)
    
    # زمان‌ها
    started_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    def __repr__(self):
        return f"<ImportBatch(batch_id='{self.batch_id}', status='{self.status}')>"
