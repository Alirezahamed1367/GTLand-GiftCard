"""
مدل لاگ فرآیندها
"""
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, JSON, Index
from sqlalchemy.sql import func
from .base import Base


class ProcessLog(Base):
    """
    جدول لاگ عملیات‌ها
    """
    __tablename__ = 'process_logs'
    
    # ستون‌های اصلی
    id = Column(Integer, primary_key=True, index=True)
    
    # نوع و وضعیت فرآیند
    process_type = Column(
        String(50), 
        nullable=False, 
        index=True,
        comment='نوع فرآیند (extract, export, update, delete, sync)'
    )
    status = Column(
        String(20), 
        nullable=False, 
        index=True,
        comment='وضعیت (success, error, warning, info, in_progress)'
    )
    
    # پیام‌ها
    message = Column(Text, comment='پیام فارسی')
    message_en = Column(Text, nullable=True, comment='پیام انگلیسی')
    
    # جزئیات
    details = Column(JSON, comment='جزئیات کامل به صورت JSON')
    
    # شناسه‌های مرتبط
    sheet_config_id = Column(Integer, nullable=True, comment='شناسه تنظیمات شیت')
    export_template_id = Column(Integer, nullable=True, comment='شناسه تمپلیت')
    
    # آمار
    records_processed = Column(Integer, default=0, comment='تعداد رکوردهای پردازش شده')
    records_success = Column(Integer, default=0, comment='تعداد موفق')
    records_failed = Column(Integer, default=0, comment='تعداد ناموفق')
    
    # زمان
    duration_seconds = Column(Integer, nullable=True, comment='مدت زمان عملیات (ثانیه)')
    started_at = Column(TIMESTAMP, nullable=True, comment='زمان شروع')
    completed_at = Column(TIMESTAMP, nullable=True, comment='زمان پایان')
    
    # کاربر (برای آینده اگر نیاز شد)
    user_id = Column(Integer, nullable=True, comment='شناسه کاربر')
    
    # خطا
    error_code = Column(String(50), nullable=True, comment='کد خطا')
    error_traceback = Column(Text, nullable=True, comment='Stack trace خطا')
    
    # تاریخ ایجاد
    created_at = Column(
        TIMESTAMP, 
        server_default=func.now(), 
        index=True,
        comment='تاریخ ایجاد'
    )
    
    # ایندکس‌ها
    __table_args__ = (
        Index('idx_process_log_type_status', 'process_type', 'status'),
        Index('idx_process_log_created', 'created_at'),
        Index('idx_process_log_sheet_config', 'sheet_config_id'),
    )
    
    def __repr__(self):
        return f"<ProcessLog(id={self.id}, type='{self.process_type}', status='{self.status}')>"
    
    def to_dict(self):
        """تبدیل به دیکشنری"""
        return {
            'id': self.id,
            'process_type': self.process_type,
            'status': self.status,
            'message': self.message,
            'message_en': self.message_en,
            'details': self.details,
            'sheet_config_id': self.sheet_config_id,
            'export_template_id': self.export_template_id,
            'records_processed': self.records_processed,
            'records_success': self.records_success,
            'records_failed': self.records_failed,
            'duration_seconds': self.duration_seconds,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'user_id': self.user_id,
            'error_code': self.error_code,
            'error_traceback': self.error_traceback,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
