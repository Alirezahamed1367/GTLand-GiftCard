"""
سیستم لاگ‌گیری پیشرفته با Loguru
"""
from loguru import logger
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
from app.utils.constants import ProcessStatus, ProcessType
from app.models import ProcessLog, SessionLocal


class AppLogger:
    """
    کلاس مدیریت لاگ‌ها
    """
    
    def __init__(self, log_dir: str = "logs"):
        """
        راه‌اندازی سیستم لاگ
        
        Args:
            log_dir: مسیر دایرکتوری لاگ‌ها
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # حذف handler پیش‌فرض
        logger.remove()
        
        # اضافه کردن handler برای کنسول
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
            level="INFO",
            colorize=True,
        )
        
        # اضافه کردن handler برای فایل (همه لاگ‌ها)
        logger.add(
            str(self.log_dir / "app_{time:YYYY-MM-DD}.log"),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="DEBUG",
            rotation="00:00",  # تغییر فایل در نیمه شب
            retention="30 days",  # نگهداری 30 روز
            compression="zip",  # فشرده‌سازی فایل‌های قدیمی
            encoding="utf-8",
        )
        
        # اضافه کردن handler برای خطاها
        logger.add(
            str(self.log_dir / "error_{time:YYYY-MM-DD}.log"),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="ERROR",
            rotation="00:00",
            retention="90 days",  # نگهداری 90 روز برای خطاها
            compression="zip",
            encoding="utf-8",
        )
        
        self.logger = logger
    
    def info(self, message: str, **kwargs):
        """ثبت لاگ اطلاعاتی"""
        self.logger.info(message, **kwargs)
    
    def success(self, message: str, **kwargs):
        """ثبت لاگ موفقیت"""
        self.logger.success(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """ثبت لاگ هشدار"""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """ثبت لاگ خطا"""
        self.logger.error(message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """ثبت لاگ دیباگ"""
        self.logger.debug(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """ثبت لاگ بحرانی"""
        self.logger.critical(message, **kwargs)
    
    def log_to_db(
        self,
        process_type: ProcessType,
        status: ProcessStatus,
        message: str,
        details: Optional[dict] = None,
        sheet_config_id: Optional[int] = None,
        export_template_id: Optional[int] = None,
        **kwargs
    ):
        """
        ثبت لاگ در دیتابیس
        
        Args:
            process_type: نوع فرآیند
            status: وضعیت
            message: پیام فارسی
            details: جزئیات
            sheet_config_id: شناسه تنظیمات شیت
            export_template_id: شناسه تمپلیت
            **kwargs: آرگومان‌های اضافی
        """
        try:
            db = SessionLocal()
            
            log_entry = ProcessLog(
                process_type=process_type.value,
                status=status.value,
                message=message,
                details=details or {},
                sheet_config_id=sheet_config_id,
                export_template_id=export_template_id,
                **kwargs
            )
            
            db.add(log_entry)
            db.commit()
            db.close()
            
        except Exception as e:
            self.error(f"خطا در ثبت لاگ در دیتابیس: {str(e)}")
    
    def start_process(
        self,
        process_type: ProcessType,
        message: str,
        **kwargs
    ) -> int:
        """
        شروع یک فرآیند و ثبت در دیتابیس
        
        Args:
            process_type: نوع فرآیند
            message: پیام
            **kwargs: آرگومان‌های اضافی
            
        Returns:
            شناسه لاگ در دیتابیس
        """
        try:
            db = SessionLocal()
            
            log_entry = ProcessLog(
                process_type=process_type.value,
                status=ProcessStatus.IN_PROGRESS.value,
                message=message,
                started_at=datetime.now(),
                **kwargs
            )
            
            db.add(log_entry)
            db.commit()
            log_id = log_entry.id
            db.close()
            
            self.info(f"شروع فرآیند: {message}")
            return log_id
            
        except Exception as e:
            self.error(f"خطا در شروع فرآیند: {str(e)}")
            return -1
    
    def complete_process(
        self,
        log_id: int,
        status: ProcessStatus,
        message: Optional[str] = None,
        **kwargs
    ):
        """
        پایان یک فرآیند
        
        Args:
            log_id: شناسه لاگ
            status: وضعیت نهایی
            message: پیام پایانی
            **kwargs: آرگومان‌های اضافی
        """
        try:
            db = SessionLocal()
            
            log_entry = db.query(ProcessLog).filter_by(id=log_id).first()
            if log_entry:
                log_entry.status = status.value
                if message:
                    log_entry.message = message
                
                log_entry.completed_at = datetime.now()
                
                # محاسبه مدت زمان
                if log_entry.started_at:
                    duration = (log_entry.completed_at - log_entry.started_at).total_seconds()
                    log_entry.duration_seconds = int(duration)
                
                # بروزرسانی سایر فیلدها
                for key, value in kwargs.items():
                    if hasattr(log_entry, key):
                        setattr(log_entry, key, value)
                
                db.commit()
                
                if status == ProcessStatus.SUCCESS:
                    self.success(f"پایان موفق فرآیند: {message or log_entry.message}")
                elif status == ProcessStatus.ERROR:
                    self.error(f"خطا در فرآیند: {message or log_entry.message}")
                else:
                    self.warning(f"پایان فرآیند با هشدار: {message or log_entry.message}")
            
            db.close()
            
        except Exception as e:
            self.error(f"خطا در پایان فرآیند: {str(e)}")


# نمونه سراسری
app_logger = AppLogger()
