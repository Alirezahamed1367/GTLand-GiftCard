"""
GT-Land Manager - نقطه شروع برنامه

توسعه دهنده: علیرضا حامد
تاریخ: 2025
نسخه: Ver 9
"""
import sys
import os
from pathlib import Path

# اضافه کردن مسیر پروژه
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from dotenv import load_dotenv

# بارگذاری متغیرهای محیطی
load_dotenv()

from app.core.logger import app_logger
from app.utils.constants import ERROR_MESSAGES


class GTLandApplication:
    """
    کلاس اصلی برنامه
    """
    
    def __init__(self):
        """راه‌اندازی برنامه"""
        self.app = None
        self.main_window = None
        self.logger = app_logger
    
    def check_requirements(self) -> bool:
        """
        بررسی پیش‌نیازهای برنامه
        
        Returns:
            True اگر همه چیز آماده باشد
        """
        errors = []
        
        # بررسی فایل credentials
        credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 'config/credentials.json')
        if not Path(credentials_path).exists():
            errors.append(f"❌ فایل credentials یافت نشد: {credentials_path}")
        
        # بررسی اتصال دیتابیس
        try:
            from app.models import SessionLocal
            from sqlalchemy import text
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
            self.logger.success("✅ اتصال به دیتابیس برقرار است.")
        except Exception as e:
            errors.append(f"❌ خطا در اتصال به دیتابیس: {str(e)}")
        
        # بررسی دایرکتوری‌ها
        directories = ['logs', 'data/exports', 'templates']
        for directory in directories:
            dir_path = Path(directory)
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"✅ دایرکتوری ایجاد شد: {directory}")
        
        # نمایش خطاها
        if errors:
            error_message = "\n".join(errors)
            error_message += "\n\n📝 لطفاً مراحل راه‌اندازی را از README.md دنبال کنید."
            
            self.logger.error("خطا در بررسی پیش‌نیازها:")
            self.logger.error(error_message)
            
            # نمایش پیام خطا
            self.show_error_dialog("خطا در راه‌اندازی", error_message)
            return False
        
        return True
    
    def show_error_dialog(self, title: str, message: str):
        """نمایش دیالوگ خطا"""
        app = QApplication(sys.argv)
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
        app.quit()
    
    def run(self):
        """اجرای برنامه"""
        try:
            # بررسی پیش‌نیازها
            if not self.check_requirements():
                return 1
            
            # ایجاد اپلیکیشن Qt
            self.app = QApplication(sys.argv)
            self.app.setApplicationName(os.getenv('APP_NAME', 'GT-Land Manager'))
            self.app.setApplicationVersion(os.getenv('APP_VERSION', 'Ver 9'))
            
            # تنظیم فونت فارسی
            from PyQt6.QtGui import QFont
            font = QFont("Segoe UI", 10)
            self.app.setFont(font)
            
            # تنظیم جهت راست به چپ
            self.app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            
            # لاگ شروع برنامه
            self.logger.success("=" * 60)
            self.logger.success(f"🚀 {self.app.applicationName()} نسخه {self.app.applicationVersion()}")
            self.logger.success("=" * 60)
            
            # ایجاد پنجره اصلی
            from app.gui.main_window import MainWindow
            self.main_window = MainWindow()
            self.main_window.show()
            
            # اجرای حلقه اصلی برنامه
            return self.app.exec()
            
        except Exception as e:
            self.logger.critical(f"خطای بحرانی در اجرای برنامه: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return 1


def main():
    """تابع اصلی"""
    app = GTLandApplication()
    exit_code = app.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
