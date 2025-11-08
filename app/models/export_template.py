"""
مدل تمپلیت‌های خروجی Excel
"""
from sqlalchemy import Column, Integer, String, Boolean, Text, TIMESTAMP, JSON, Index
from sqlalchemy.sql import func
from .base import Base


class ExportTemplate(Base):
    """
    جدول تمپلیت‌های خروجی اکسل
    """
    __tablename__ = 'export_templates'
    
    # ستون‌های اصلی
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, comment='نام تمپلیت')
    template_type = Column(String(50), nullable=False, comment='نوع تمپلیت (type1, type2, type3)')
    
    # مسیر فایل تمپلیت
    template_path = Column(Text, nullable=False, comment='مسیر فایل تمپلیت')
    
    # الگوی نام فایل خروجی
    output_filename_pattern = Column(
        String(255), 
        default='Export_{type}_{date}.xlsx',
        comment='الگوی نام فایل خروجی'
    )
    
    # نقشه ستون‌ها
    column_mappings = Column(
        JSON,
        comment='نقشه ستون‌های دیتابیس به Excel: {"db_column": "excel_column"}'
    )
    
    # شیت مقصد در Excel
    target_worksheet = Column(String(255), default='Sheet1', comment='نام ورک‌شیت مقصد')
    start_row = Column(Integer, default=2, comment='ردیف شروع داده‌ها')
    start_column = Column(Integer, default=1, comment='ستون شروع داده‌ها')
    
    # فیلترها
    filters = Column(
        JSON,
        comment='فیلترهای اعمالی بر داده‌ها قبل از خروجی'
    )
    
    # مرتب‌سازی
    sort_by = Column(JSON, comment='ستون‌های مرتب‌سازی: [{"column": "name", "order": "asc"}]')
    
    # فرمول‌ها و محاسبات
    formulas = Column(JSON, comment='فرمول‌های اکسل برای ستون‌ها')
    
    # فرمت‌بندی
    styling = Column(JSON, comment='تنظیمات فرمت‌بندی (رنگ، فونت، ...)')
    
    # وضعیت
    is_active = Column(Boolean, default=True, comment='فعال/غیرفعال')
    
    # تاریخ‌ها
    created_at = Column(TIMESTAMP, server_default=func.now(), comment='تاریخ ایجاد')
    updated_at = Column(
        TIMESTAMP, 
        server_default=func.now(), 
        onupdate=func.now(), 
        comment='تاریخ آخرین بروزرسانی'
    )
    
    # توضیحات
    description = Column(Text, nullable=True, comment='توضیحات')
    
    # ایندکس‌ها
    __table_args__ = (
        Index('idx_export_template_type', 'template_type'),
        Index('idx_export_template_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<ExportTemplate(id={self.id}, name='{self.name}', type='{self.template_type}')>"
    
    def to_dict(self):
        """تبدیل به دیکشنری"""
        return {
            'id': self.id,
            'name': self.name,
            'template_type': self.template_type,
            'template_path': self.template_path,
            'output_filename_pattern': self.output_filename_pattern,
            'column_mappings': self.column_mappings,
            'target_worksheet': self.target_worksheet,
            'start_row': self.start_row,
            'start_column': self.start_column,
            'filters': self.filters,
            'sort_by': self.sort_by,
            'formulas': self.formulas,
            'styling': self.styling,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'description': self.description,
        }
