"""
مدل تنظیمات Google Sheets
"""
from sqlalchemy import Column, Integer, String, Boolean, Text, TIMESTAMP, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class SheetConfig(Base):
    """
    جدول تنظیمات فایل‌های Google Sheets
    """
    __tablename__ = 'sheet_configs'
    
    # ستون‌های اصلی
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, comment='نام تنظیمات')
    sheet_url = Column(Text, nullable=False, comment='URL گوگل شیت')
    worksheet_name = Column(String(255), nullable=True, comment='نام ورک‌شیت')
    
    # وضعیت
    is_active = Column(Boolean, default=True, comment='فعال/غیرفعال')
    
    # تنظیمات ستون‌ها
    column_mappings = Column(
        JSON, 
        comment='نقشه ستون‌ها: {"نام_ستون_شیت": "نام_ستون_دیتابیس"}'
    )
    ready_column = Column(String(100), comment='نام ستون "آماده برای استخراج"')
    extracted_column = Column(String(100), comment='نام ستون "استخراج شده"')
    
    # کلیدهای یکتا
    unique_key_columns = Column(
        JSON,
        comment='لیست ستون‌هایی که کلید یکتا را می‌سازند'
    )
    
    # ستون‌های مورد نیاز برای استخراج
    columns_to_extract = Column(
        JSON,
        nullable=True,
        comment='لیست ستون‌هایی که باید استخراج شوند (None = همه ستون‌ها)'
    )
    
    # تنظیمات پیشرفته
    skip_rows = Column(Integer, default=0, comment='تعداد ردیف‌های ابتدایی که باید رد شوند')
    max_rows = Column(Integer, nullable=True, comment='حداکثر تعداد ردیف‌های قابل استخراج')
    
    # فیلترها و شرایط
    filters = Column(JSON, comment='فیلترهای اعمالی بر داده‌ها')
    
    # تاریخ‌ها
    created_at = Column(TIMESTAMP, server_default=func.now(), comment='تاریخ ایجاد')
    updated_at = Column(
        TIMESTAMP, 
        server_default=func.now(), 
        onupdate=func.now(), 
        comment='تاریخ آخرین بروزرسانی'
    )
    last_synced_at = Column(TIMESTAMP, nullable=True, comment='تاریخ آخرین همگام‌سازی')
    
    # توضیحات
    description = Column(Text, nullable=True, comment='توضیحات')
    
    # روابط
    sales_data = relationship("SalesData", back_populates="sheet_config", cascade="all, delete-orphan")
    
    # ایندکس‌ها
    __table_args__ = (
        Index('idx_sheet_config_active', 'is_active'),
        Index('idx_sheet_config_name', 'name'),
    )
    
    def __repr__(self):
        return f"<SheetConfig(id={self.id}, name='{self.name}', active={self.is_active})>"
    
    def to_dict(self):
        """تبدیل به دیکشنری"""
        return {
            'id': self.id,
            'name': self.name,
            'sheet_url': self.sheet_url,
            'worksheet_name': self.worksheet_name,
            'is_active': self.is_active,
            'column_mappings': self.column_mappings,
            'ready_column': self.ready_column,
            'extracted_column': self.extracted_column,
            'unique_key_columns': self.unique_key_columns,
            'skip_rows': self.skip_rows,
            'max_rows': self.max_rows,
            'filters': self.filters,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_synced_at': self.last_synced_at.isoformat() if self.last_synced_at else None,
            'description': self.description,
        }
