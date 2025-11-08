"""
مدل لاگ خروجی‌های تولید شده
"""
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, JSON, ForeignKey, Index, ARRAY
from sqlalchemy.sql import func
from .base import Base


class ExportLog(Base):
    """
    جدول لاگ فایل‌های خروجی تولید شده
    """
    __tablename__ = 'export_logs'
    
    # ستون‌های اصلی
    id = Column(Integer, primary_key=True, index=True)
    
    # شناسه تمپلیت
    template_id = Column(
        Integer,
        ForeignKey('export_templates.id', ondelete='SET NULL'),
        nullable=True,
        comment='شناسه تمپلیت'
    )
    
    # مشخصات فایل
    file_path = Column(Text, nullable=False, comment='مسیر فایل تولید شده')
    file_name = Column(String(255), nullable=False, comment='نام فایل')
    file_size = Column(Integer, nullable=True, comment='حجم فایل (بایت)')
    
    # آمار
    record_count = Column(Integer, default=0, comment='تعداد رکوردها')
    exported_data_ids = Column(JSON, comment='لیست آی‌دی‌های داده‌های استفاده شده')
    
    # فیلترها و تنظیمات اعمال شده
    applied_filters = Column(JSON, comment='فیلترهای اعمال شده')
    settings = Column(JSON, comment='تنظیمات خروجی')
    
    # وضعیت
    status = Column(
        String(20),
        default='completed',
        comment='وضعیت (completed, failed, partial)'
    )
    
    # خطا
    error_message = Column(Text, nullable=True, comment='پیام خطا (در صورت وجود)')
    
    # زمان
    duration_seconds = Column(Integer, nullable=True, comment='مدت زمان تولید (ثانیه)')
    
    # تاریخ ایجاد
    created_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        index=True,
        comment='تاریخ ایجاد'
    )
    
    # یادداشت‌ها
    notes = Column(Text, nullable=True, comment='یادداشت‌ها')
    
    # ایندکس‌ها
    __table_args__ = (
        Index('idx_export_log_template', 'template_id'),
        Index('idx_export_log_created', 'created_at'),
        Index('idx_export_log_status', 'status'),
    )
    
    def __repr__(self):
        return f"<ExportLog(id={self.id}, file='{self.file_name}', status='{self.status}')>"
    
    def to_dict(self):
        """تبدیل به دیکشنری"""
        return {
            'id': self.id,
            'template_id': self.template_id,
            'file_path': self.file_path,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'record_count': self.record_count,
            'exported_data_ids': self.exported_data_ids,
            'applied_filters': self.applied_filters,
            'settings': self.settings,
            'status': self.status,
            'error_message': self.error_message,
            'duration_seconds': self.duration_seconds,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'notes': self.notes,
        }
