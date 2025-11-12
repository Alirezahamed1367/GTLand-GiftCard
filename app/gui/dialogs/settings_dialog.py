"""
دیالوگ تنظیمات برنامه
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QCheckBox, QLabel, 
    QMessageBox, QGroupBox, QFileDialog, QTabWidget,
    QTextEdit, QSpinBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import os
from pathlib import Path
from dotenv import load_dotenv, set_key

from app.core.logger import app_logger


class SettingsDialog(QDialog):
    """دیالوگ تنظیمات برنامه"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = app_logger
        self.env_file = Path(".env")
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """راه‌اندازی رابط کاربری"""
        self.setWindowTitle("⚙️ تنظیمات برنامه")
        self.setMinimumSize(700, 600)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # عنوان
        title_label = QLabel("⚙️ تنظیمات برنامه")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2196F3; padding: 10px;")
        layout.addWidget(title_label)
        
        # تب‌ها
        tabs = QTabWidget()
        
        # تب عمومی
        tabs.addTab(self.create_general_tab(), "🔧 عمومی")
        
        # تب Google
        tabs.addTab(self.create_google_tab(), "🔐 Google Sheets")
        
        # تب دیتابیس
        tabs.addTab(self.create_database_tab(), "💾 دیتابیس")
        
        # تب خروجی
        tabs.addTab(self.create_export_tab(), "📤 خروجی")
        
        layout.addWidget(tabs)
        
        # دکمه‌ها
        buttons_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 ذخیره")
        save_btn.setStyleSheet(self.get_button_style("#4CAF50"))
        save_btn.clicked.connect(self.save_settings)
        buttons_layout.addWidget(save_btn)
        
        reset_btn = QPushButton("🔄 بازگردانی")
        reset_btn.setStyleSheet(self.get_button_style("#FF9800"))
        reset_btn.clicked.connect(self.reset_settings)
        buttons_layout.addWidget(reset_btn)
        
        close_btn = QPushButton("❌ بستن")
        close_btn.setStyleSheet(self.get_button_style("#F44336"))
        close_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
    
    def create_general_tab(self):
        """ایجاد تب تنظیمات عمومی"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # اطلاعات برنامه
        info_group = QGroupBox("📋 اطلاعات برنامه")
        info_layout = QFormLayout()
        
        self.app_name_input = QLineEdit()
        self.app_name_input.setPlaceholderText("GT-Land Manager")
        info_layout.addRow("نام برنامه:", self.app_name_input)
        
        self.app_version_input = QLineEdit()
        self.app_version_input.setPlaceholderText("1.0.0")
        info_layout.addRow("نسخه:", self.app_version_input)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # تنظیمات لاگ
        log_group = QGroupBox("📝 تنظیمات لاگ")
        log_layout = QVBoxLayout()
        
        self.log_to_file_checkbox = QCheckBox("✅ ذخیره لاگ در فایل")
        self.log_to_file_checkbox.setChecked(True)
        log_layout.addWidget(self.log_to_file_checkbox)
        
        self.log_to_db_checkbox = QCheckBox("✅ ذخیره لاگ در دیتابیس")
        self.log_to_db_checkbox.setChecked(True)
        log_layout.addWidget(self.log_to_db_checkbox)
        
        log_level_layout = QFormLayout()
        self.log_retention_input = QSpinBox()
        self.log_retention_input.setMinimum(1)
        self.log_retention_input.setMaximum(365)
        self.log_retention_input.setValue(30)
        self.log_retention_input.setSuffix(" روز")
        log_level_layout.addRow("نگهداری لاگ:", self.log_retention_input)
        
        log_layout.addLayout(log_level_layout)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        layout.addStretch()
        return widget
    
    def create_google_tab(self):
        """ایجاد تب تنظیمات Google"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # فایل احراز هویت
        cred_group = QGroupBox("🔐 احراز هویت")
        cred_layout = QVBoxLayout()
        
        info_label = QLabel(
            "فایل credentials.json را از Google Cloud Console دانلود کنید:\n"
            "1. بروید به: console.cloud.google.com\n"
            "2. پروژه خود را انتخاب کنید\n"
            "3. APIs & Services > Credentials\n"
            "4. Service Account را ایجاد کنید\n"
            "5. فایل JSON را دانلود کنید"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("background: #f5f5f5; padding: 10px; border-radius: 5px; color: #555;")
        cred_layout.addWidget(info_label)
        
        file_layout = QHBoxLayout()
        self.credentials_path_input = QLineEdit()
        self.credentials_path_input.setPlaceholderText("config/credentials.json")
        file_layout.addWidget(self.credentials_path_input)
        
        browse_btn = QPushButton("📁 انتخاب فایل")
        browse_btn.clicked.connect(self.browse_credentials)
        file_layout.addWidget(browse_btn)
        
        cred_layout.addLayout(file_layout)
        
        test_btn = QPushButton("✅ تست اتصال")
        test_btn.setStyleSheet(self.get_button_style("#2196F3"))
        test_btn.clicked.connect(self.test_google_connection)
        cred_layout.addWidget(test_btn)
        
        cred_group.setLayout(cred_layout)
        layout.addWidget(cred_group)
        
        # تنظیمات API
        api_group = QGroupBox("⚡ تنظیمات API")
        api_layout = QFormLayout()
        
        self.retry_count_input = QSpinBox()
        self.retry_count_input.setMinimum(1)
        self.retry_count_input.setMaximum(10)
        self.retry_count_input.setValue(3)
        api_layout.addRow("تعداد تلاش مجدد:", self.retry_count_input)
        
        self.batch_size_input = QSpinBox()
        self.batch_size_input.setMinimum(10)
        self.batch_size_input.setMaximum(1000)
        self.batch_size_input.setValue(100)
        api_layout.addRow("اندازه دسته:", self.batch_size_input)
        
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)
        
        layout.addStretch()
        return widget
    
    def create_database_tab(self):
        """ایجاد تب تنظیمات دیتابیس"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        
        # اطلاعات دیتابیس
        db_group = QGroupBox("💾 اطلاعات دیتابیس")
        db_layout = QVBoxLayout()
        
        info_label = QLabel(
            f"📊 نوع دیتابیس: SQLite\n"
            f"📁 مسیر: data/gt_land.db\n"
            f"✅ وضعیت: متصل"
        )
        info_label.setStyleSheet("background: #e8f5e9; padding: 15px; border-radius: 5px; font-weight: bold;")
        db_layout.addWidget(info_label)
        
        db_group.setLayout(db_layout)
        layout.addWidget(db_group)
        
        # عملیات دیتابیس
        ops_group = QGroupBox("🔧 عملیات دیتابیس")
        ops_layout = QVBoxLayout()
        ops_layout.setSpacing(8)
        
        # ردیف اول: پشتیبان‌گیری و بازیابی
        row1 = QHBoxLayout()
        
        backup_btn = QPushButton("💾 پشتیبان‌گیری")
        backup_btn.setStyleSheet(self.get_button_style("#4CAF50"))
        backup_btn.setToolTip("ایجاد نسخه پشتیبان از دیتابیس")
        backup_btn.clicked.connect(self.backup_database)
        row1.addWidget(backup_btn)
        
        restore_btn = QPushButton("📥 بازیابی پشتیبان")
        restore_btn.setStyleSheet(self.get_button_style("#00BCD4"))
        restore_btn.setToolTip("بارگذاری دیتابیس از فایل پشتیبان")
        restore_btn.clicked.connect(self.restore_database)
        row1.addWidget(restore_btn)
        
        ops_layout.addLayout(row1)
        
        # ردیف دوم: بهینه‌سازی و پاکسازی
        row2 = QHBoxLayout()
        
        optimize_btn = QPushButton("⚡ بهینه‌سازی (ANALYZE)")
        optimize_btn.setStyleSheet(self.get_button_style("#2196F3"))
        optimize_btn.setToolTip("بروزرسانی آمار جداول برای query های سریع‌تر")
        optimize_btn.clicked.connect(self.optimize_database)
        row2.addWidget(optimize_btn)
        
        vacuum_btn = QPushButton("🧹 فشرده‌سازی (VACUUM)")
        vacuum_btn.setStyleSheet(self.get_button_style("#FF9800"))
        vacuum_btn.setToolTip("آزادسازی فضای خالی و فشرده‌سازی دیتابیس")
        vacuum_btn.clicked.connect(self.vacuum_database)
        row2.addWidget(vacuum_btn)
        
        ops_layout.addLayout(row2)
        
        # ردیف سوم: آرشیو و خالی کردن
        row3 = QHBoxLayout()
        
        archive_btn = QPushButton("📦 آرشیو داده‌ها")
        archive_btn.setStyleSheet(self.get_button_style("#9C27B0"))
        archive_btn.setToolTip("انتقال داده‌ها به آرشیو + صفر کردن آمار + پاکسازی")
        archive_btn.clicked.connect(self.archive_sales_data)
        row3.addWidget(archive_btn)
        
        clear_btn = QPushButton("🗑️ خالی کردن دیتابیس")
        clear_btn.setStyleSheet(self.get_button_style("#F44336"))
        clear_btn.setToolTip("حذف تمام داده‌ها + صفر کردن آمار (بدون آرشیو)")
        clear_btn.clicked.connect(self.clear_database)
        row3.addWidget(clear_btn)
        
        ops_layout.addLayout(row3)
        
        # ردیف چهارم: مشاهده آرشیوها
        row4 = QHBoxLayout()
        
        view_archives_btn = QPushButton("📚 مشاهده آرشیوها")
        view_archives_btn.setStyleSheet(self.get_button_style("#607D8B"))
        view_archives_btn.setToolTip("مشاهده لیست آرشیوها و پشتیبان‌ها")
        view_archives_btn.clicked.connect(self.view_archives)
        row4.addWidget(view_archives_btn)
        
        stats_btn = QPushButton("📊 مشاهده آمار دیتابیس")
        stats_btn.setStyleSheet(self.get_button_style("#795548"))
        stats_btn.setToolTip("نمایش آمار کامل جداول و حجم")
        stats_btn.clicked.connect(self.show_database_stats)
        row4.addWidget(stats_btn)
        
        ops_layout.addLayout(row4)
        
        ops_group.setLayout(ops_layout)
        layout.addWidget(ops_group)
        
        layout.addStretch()
        return widget
    
    def create_export_tab(self):
        """ایجاد تب تنظیمات خروجی"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # مسیر خروجی
        path_group = QGroupBox("📁 مسیرها")
        path_layout = QFormLayout()
        
        self.export_path_input = QLineEdit()
        self.export_path_input.setPlaceholderText("data/exports")
        path_layout.addRow("پوشه خروجی:", self.export_path_input)
        
        self.template_path_input = QLineEdit()
        self.template_path_input.setPlaceholderText("templates")
        path_layout.addRow("پوشه تمپلیت:", self.template_path_input)
        
        path_group.setLayout(path_layout)
        layout.addWidget(path_group)
        
        # تنظیمات Excel
        excel_group = QGroupBox("📊 تنظیمات Excel")
        excel_layout = QVBoxLayout()
        
        self.auto_width_checkbox = QCheckBox("✅ تنظیم خودکار عرض ستون‌ها")
        self.auto_width_checkbox.setChecked(True)
        excel_layout.addWidget(self.auto_width_checkbox)
        
        self.freeze_header_checkbox = QCheckBox("✅ ثابت نگه داشتن سرتیتر")
        self.freeze_header_checkbox.setChecked(True)
        excel_layout.addWidget(self.freeze_header_checkbox)
        
        self.add_filters_checkbox = QCheckBox("✅ افزودن فیلتر خودکار")
        self.add_filters_checkbox.setChecked(True)
        excel_layout.addWidget(self.add_filters_checkbox)
        
        excel_group.setLayout(excel_layout)
        layout.addWidget(excel_group)
        
        layout.addStretch()
        return widget
    
    def load_settings(self):
        """بارگذاری تنظیمات"""
        load_dotenv()
        
        # عمومی
        self.app_name_input.setText(os.getenv("APP_NAME", "GT-Land Manager"))
        self.app_version_input.setText(os.getenv("APP_VERSION", "1.0.0"))
        self.log_retention_input.setValue(int(os.getenv("LOG_RETENTION_DAYS", "30")))
        
        # Google
        self.credentials_path_input.setText(os.getenv("GOOGLE_CREDENTIALS_PATH", "config/credentials.json"))
        self.retry_count_input.setValue(int(os.getenv("API_RETRY_COUNT", "3")))
        self.batch_size_input.setValue(int(os.getenv("BATCH_SIZE", "100")))
        
        # خروجی
        self.export_path_input.setText(os.getenv("EXPORT_PATH", "data/exports"))
        self.template_path_input.setText(os.getenv("TEMPLATE_PATH", "templates"))
    
    def save_settings(self):
        """ذخیره تنظیمات"""
        try:
            # ایجاد فایل .env اگر وجود ندارد
            if not self.env_file.exists():
                self.env_file.touch()
            
            # ذخیره تنظیمات
            settings = {
                "APP_NAME": self.app_name_input.text(),
                "APP_VERSION": self.app_version_input.text(),
                "LOG_RETENTION_DAYS": str(self.log_retention_input.value()),
                "GOOGLE_CREDENTIALS_PATH": self.credentials_path_input.text(),
                "API_RETRY_COUNT": str(self.retry_count_input.value()),
                "BATCH_SIZE": str(self.batch_size_input.value()),
                "EXPORT_PATH": self.export_path_input.text(),
                "TEMPLATE_PATH": self.template_path_input.text(),
            }
            
            for key, value in settings.items():
                set_key(str(self.env_file), key, value)
            
            self.logger.success("تنظیمات ذخیره شد")
            QMessageBox.information(self, "موفق", "✅ تنظیمات با موفقیت ذخیره شد!")
            
        except Exception as e:
            self.logger.error(f"خطا در ذخیره تنظیمات: {str(e)}")
            QMessageBox.critical(self, "خطا", f"❌ خطا در ذخیره تنظیمات:\n{str(e)}")
    
    def reset_settings(self):
        """بازگردانی تنظیمات پیش‌فرض"""
        reply = QMessageBox.question(
            self,
            "تایید",
            "آیا می‌خواهید تنظیمات را به حالت پیش‌فرض بازگردانید؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.app_name_input.setText("GT-Land Manager")
            self.app_version_input.setText("1.0.0")
            self.log_retention_input.setValue(30)
            self.credentials_path_input.setText("config/credentials.json")
            self.retry_count_input.setValue(3)
            self.batch_size_input.setValue(100)
            self.export_path_input.setText("data/exports")
            self.template_path_input.setText("templates")
            
            QMessageBox.information(self, "موفق", "✅ تنظیمات به حالت پیش‌فرض بازگردانده شد!")
    
    def browse_credentials(self):
        """انتخاب فایل credentials"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "انتخاب فایل credentials.json",
            "",
            "JSON Files (*.json)"
        )
        
        if file_path:
            self.credentials_path_input.setText(file_path)
    
    def test_google_connection(self):
        """تست اتصال Google"""
        cred_path = self.credentials_path_input.text()
        
        if not Path(cred_path).exists():
            QMessageBox.warning(self, "خطا", f"❌ فایل credentials یافت نشد:\n{cred_path}")
            return
        
        try:
            import gspread
            from oauth2client.service_account import ServiceAccountCredentials
            
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            creds = ServiceAccountCredentials.from_json_keyfile_name(cred_path, scope)
            client = gspread.authorize(creds)
            
            QMessageBox.information(
                self,
                "موفق",
                "✅ اتصال به Google Sheets با موفقیت برقرار شد!"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "خطا",
                f"❌ خطا در اتصال:\n{str(e)}"
            )
    
    def backup_database(self):
        """پشتیبان‌گیری از دیتابیس"""
        try:
            import shutil
            from datetime import datetime
            
            backup_dir = Path("data/backups")
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"gt_land_{timestamp}.db"
            
            shutil.copy2("data/gt_land.db", backup_file)
            
            QMessageBox.information(
                self,
                "موفق",
                f"✅ پشتیبان با موفقیت ایجاد شد:\n{backup_file}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"❌ خطا در پشتیبان‌گیری:\n{str(e)}")
    
    def optimize_database(self):
        """بهینه‌سازی دیتابیس (ANALYZE)"""
        reply = QMessageBox.question(
            self,
            "تایید",
            "آیا می‌خواهید دیتابیس را بهینه‌سازی کنید?\n\n"
            "این عملیات آمارهای دیتابیس را بروزرسانی می‌کند.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            from app.models import engine
            from sqlalchemy import text
            
            # ANALYZE برای بهینه‌سازی query ها
            with engine.begin() as conn:
                conn.execute(text("ANALYZE"))
            
            QMessageBox.information(
                self, 
                "موفق", 
                "✅ دیتابیس بهینه‌سازی شد!\n\n"
                "آمارهای جداول بروزرسانی شدند."
            )
            
        except Exception as e:
            app_logger.error(f"خطا در بهینه‌سازی: {str(e)}")
            QMessageBox.critical(self, "خطا", f"❌ خطا در بهینه‌سازی:\n{str(e)}")
    
    def vacuum_database(self):
        """پاکسازی و فشرده‌سازی دیتابیس (VACUUM)"""
        reply = QMessageBox.question(
            self,
            "تایید",
            "آیا می‌خواهید دیتابیس را پاکسازی کنید?\n\n"
            "⚠️ این عملیات:\n"
            "• فضای خالی را آزاد می‌کند\n"
            "• دیتابیس را فشرده می‌کند\n"
            "• ممکن است چند ثانیه طول بکشد",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            from app.models import engine
            import os
            
            # اندازه قبل
            db_path = "data/gt_land.db"
            size_before = os.path.getsize(db_path) / 1024 / 1024  # MB
            
            # VACUUM برای فشرده‌سازی (باید connection جدا باشد)
            raw_conn = engine.raw_connection()
            try:
                cursor = raw_conn.cursor()
                cursor.execute("VACUUM")
                cursor.close()
            finally:
                raw_conn.close()
            
            # اندازه بعد
            size_after = os.path.getsize(db_path) / 1024 / 1024  # MB
            saved = size_before - size_after
            
            QMessageBox.information(
                self, 
                "موفق", 
                f"✅ دیتابیس پاکسازی شد!\n\n"
                f"📊 حجم قبل: {size_before:.2f} MB\n"
                f"📊 حجم بعد: {size_after:.2f} MB\n"
                f"💾 فضای آزاد شده: {saved:.2f} MB"
            )
            
        except Exception as e:
            app_logger.error(f"خطا در پاکسازی: {str(e)}")
            QMessageBox.critical(self, "خطا", f"❌ خطا در پاکسازی:\n{str(e)}")
    
    def archive_sales_data(self):
        """آرشیو کردن داده‌های فروش + صفر کردن آمار"""
        from app.core.database import db_manager
        from app.models import SalesData, ProcessLog, ExportLog, engine
        from sqlalchemy import text
        import shutil
        from datetime import datetime
        from pathlib import Path
        
        # دیالوگ تایید
        reply = QMessageBox.question(
            self,
            "⚠️ تایید آرشیو",
            "این عملیات:\n\n"
            "1️⃣ یک نسخه پشتیبان کامل می‌گیرد\n"
            "2️⃣ داده‌های فروش را به فایل آرشیو منتقل می‌کند\n"
            "3️⃣ تمام داده‌ها و آمارها را صفر می‌کند\n"
            "4️⃣ دیتابیس را بهینه‌سازی می‌کند\n\n"
            "⚠️ این عملیات قابل بازگشت نیست!\n\n"
            "آیا ادامه می‌دهید؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            # 1. پشتیبان‌گیری
            self.logger.info("🔄 شروع عملیات آرشیو...")
            
            backup_dir = Path("data/backups")
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"before_archive_{timestamp}.db"
            
            shutil.copy2("data/gt_land.db", backup_file)
            self.logger.success(f"✅ پشتیبان ایجاد شد: {backup_file}")
            
            # 2. شمارش رکوردها
            db = db_manager.get_session()
            sales_count = db.query(SalesData).count()
            process_count = db.query(ProcessLog).count()
            export_count = db.query(ExportLog).count()
            db.close()
            
            if sales_count == 0 and process_count == 0 and export_count == 0:
                QMessageBox.information(
                    self,
                    "اطلاع",
                    "⚠️ هیچ داده‌ای برای آرشیو وجود ندارد!"
                )
                return
            
            # 3. ایجاد دیتابیس آرشیو
            archive_dir = Path("data/archives")
            archive_dir.mkdir(exist_ok=True)
            archive_db_path = archive_dir / f"archive_{timestamp}.db"
            
            # کپی کامل دیتابیس به آرشیو
            shutil.copy2("data/gt_land.db", archive_db_path)
            self.logger.success(f"✅ دیتابیس آرشیو ایجاد شد: {archive_db_path}")
            
            # 4. پاک کردن تمام داده‌ها از دیتابیس اصلی
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM sales_data"))
                conn.execute(text("DELETE FROM process_logs"))
                conn.execute(text("DELETE FROM export_logs"))
            
            self.logger.success(f"✅ داده‌ها پاک شدند (Sales: {sales_count:,}, Process: {process_count:,}, Export: {export_count:,})")
            
            # 5. بهینه‌سازی و فشرده‌سازی
            with engine.begin() as conn:
                conn.execute(text("ANALYZE"))
            
            raw_conn = engine.raw_connection()
            try:
                cursor = raw_conn.cursor()
                cursor.execute("VACUUM")
                cursor.close()
            finally:
                raw_conn.close()
            
            self.logger.success("✅ دیتابیس بهینه‌سازی شد")
            
            # نمایش نتیجه
            QMessageBox.information(
                self,
                "✅ موفق",
                f"عملیات آرشیو با موفقیت انجام شد!\n\n"
                f"📊 آمار آرشیو شده:\n"
                f"  • داده‌های فروش: {sales_count:,}\n"
                f"  • لاگ عملیات: {process_count:,}\n"
                f"  • لاگ Export: {export_count:,}\n\n"
                f"💾 پشتیبان: {backup_file.name}\n"
                f"📦 آرشیو: {archive_db_path.name}\n\n"
                f"✅ تمام آمارها صفر شدند"
            )
            
        except Exception as e:
            self.logger.error(f"خطا در آرشیو: {str(e)}")
            QMessageBox.critical(
                self,
                "❌ خطا",
                f"خطا در عملیات آرشیو:\n{str(e)}\n\n"
                f"دیتابیس از پشتیبان قابل بازیابی است."
            )
    
    def clear_database(self):
        """خالی کردن کامل دیتابیس بدون آرشیو + صفر کردن آمار"""
        from app.core.database import db_manager
        from app.models import SalesData, ProcessLog, ExportLog, engine
        from sqlalchemy import text
        import shutil
        from datetime import datetime
        from pathlib import Path
        
        # دیالوگ تایید (فقط یک بار)
        reply = QMessageBox.warning(
            self,
            "⚠️⚠️⚠️ هشدار شدید",
            "این عملیات:\n\n"
            "🗑️ تمام داده‌های فروش را حذف می‌کند\n"
            "🗑️ تمام لاگ عملیات را حذف می‌کند\n"
            "🗑️ تمام لاگ Export را حذف می‌کند\n"
            "📊 تمام آمارها را صفر می‌کند\n\n"
            "⚠️ بدون ایجاد آرشیو!\n"
            "⚠️ این عملیات قابل بازگشت نیست!\n\n"
            "💾 یک پشتیبان اضطراری ایجاد می‌شود.\n\n"
            "آیا مطمئن هستید که می‌خواهید ادامه دهید؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            # 1. پشتیبان اضطراری
            backup_dir = Path("data/backups")
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"before_clear_{timestamp}.db"
            
            shutil.copy2("data/gt_land.db", backup_file)
            self.logger.info(f"پشتیبان اضطراری: {backup_file}")
            
            # 2. شمارش رکوردها
            db = db_manager.get_session()
            sales_count = db.query(SalesData).count()
            process_count = db.query(ProcessLog).count()
            export_count = db.query(ExportLog).count()
            db.close()
            
            # 3. حذف تمام داده‌ها
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM sales_data"))
                conn.execute(text("DELETE FROM process_logs"))
                conn.execute(text("DELETE FROM export_logs"))
            
            self.logger.success("✅ تمام داده‌ها حذف شدند")
            
            # 4. بهینه‌سازی
            with engine.begin() as conn:
                conn.execute(text("ANALYZE"))
            
            raw_conn = engine.raw_connection()
            try:
                cursor = raw_conn.cursor()
                cursor.execute("VACUUM")
                cursor.close()
            finally:
                raw_conn.close()
            
            # نمایش نتیجه
            QMessageBox.information(
                self,
                "✅ انجام شد",
                f"دیتابیس کاملاً خالی شد!\n\n"
                f"🗑️ داده‌های حذف شده:\n"
                f"  • داده‌های فروش: {sales_count:,}\n"
                f"  • لاگ عملیات: {process_count:,}\n"
                f"  • لاگ Export: {export_count:,}\n\n"
                f"💾 پشتیبان اضطراری: {backup_file.name}\n\n"
                f"✅ آمارها صفر شدند"
            )
            
            # اطلاع به پنل اصلی برای بروزرسانی
            if hasattr(self.parent(), 'refresh_all_stats'):
                self.parent().refresh_all_stats()
            
        except Exception as e:
            self.logger.error(f"خطا در خالی کردن: {str(e)}")
            QMessageBox.critical(
                self,
                "❌ خطا",
                f"خطا در خالی کردن دیتابیس:\n{str(e)}"
            )
    
    def restore_database(self):
        """بازیابی دیتابیس از فایل پشتیبان یا آرشیو"""
        from pathlib import Path
        import shutil
        from datetime import datetime
        
        # انتخاب نوع بازیابی
        reply = QMessageBox.question(
            self,
            "انتخاب نوع بازیابی",
            "کدام نوع فایل را می‌خواهید بازیابی کنید؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
        )
        
        if reply == QMessageBox.StandardButton.Cancel:
            return
        
        # انتخاب فایل
        if reply == QMessageBox.StandardButton.Yes:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "انتخاب فایل پشتیبان",
                "data/backups",
                "Database Files (*.db);;All Files (*.*)"
            )
        else:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "انتخاب فایل آرشیو",
                "data/archives",
                "Database Files (*.db);;All Files (*.*)"
            )
        
        if not file_path:
            return
        
        # تایید نهایی
        reply = QMessageBox.warning(
            self,
            "⚠️ هشدار",
            f"این عملیات دیتابیس فعلی را با فایل انتخابی جایگزین می‌کند!\n\n"
            f"📁 فایل انتخابی:\n{Path(file_path).name}\n\n"
            f"⚠️ یک پشتیبان از دیتابیس فعلی گرفته می‌شود\n\n"
            f"آیا ادامه می‌دهید؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            # 1. پشتیبان از دیتابیس فعلی
            backup_dir = Path("data/backups")
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            current_backup = backup_dir / f"before_restore_{timestamp}.db"
            
            shutil.copy2("data/gt_land.db", current_backup)
            self.logger.info(f"پشتیبان فعلی: {current_backup}")
            
            # 2. جایگزینی دیتابیس
            shutil.copy2(file_path, "data/gt_land.db")
            self.logger.success("✅ دیتابیس بازیابی شد")
            
            # نمایش نتیجه
            QMessageBox.information(
                self,
                "✅ موفق",
                f"دیتابیس با موفقیت بازیابی شد!\n\n"
                f"📥 فایل بازیابی: {Path(file_path).name}\n"
                f"� پشتیبان فعلی: {current_backup.name}\n\n"
                f"⚠️ برنامه را مجدد راه‌اندازی کنید"
            )
            
        except Exception as e:
            self.logger.error(f"خطا در بازیابی: {str(e)}")
            QMessageBox.critical(
                self,
                "❌ خطا",
                f"خطا در بازیابی دیتابیس:\n{str(e)}"
            )
    
    def view_archives(self):
        """نمایش لیست آرشیوها و پشتیبان‌ها"""
        from pathlib import Path
        import os
        from datetime import datetime
        
        # جمع‌آوری اطلاعات
        backup_dir = Path("data/backups")
        archive_dir = Path("data/archives")
        
        backups = []
        if backup_dir.exists():
            for file in sorted(backup_dir.glob("*.db"), reverse=True):
                size = os.path.getsize(file) / 1024 / 1024  # MB
                mtime = datetime.fromtimestamp(file.stat().st_mtime)
                backups.append(f"📁 {file.name}\n   حجم: {size:.2f} MB | تاریخ: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        
        archives = []
        if archive_dir.exists():
            for file in sorted(archive_dir.glob("*.db"), reverse=True):
                size = os.path.getsize(file) / 1024 / 1024  # MB
                mtime = datetime.fromtimestamp(file.stat().st_mtime)
                archives.append(f"📦 {file.name}\n   حجم: {size:.2f} MB | تاریخ: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # ساخت پیام
        msg = "📚 لیست آرشیوها و پشتیبان‌ها\n\n"
        
        msg += "=" * 50 + "\n"
        msg += "💾 پشتیبان‌ها:\n"
        msg += "=" * 50 + "\n"
        if backups:
            msg += "\n".join(backups[:10])  # فقط 10 تای اول
            if len(backups) > 10:
                msg += f"\n\n... و {len(backups) - 10} فایل دیگر"
        else:
            msg += "هیچ فایل پشتیبانی وجود ندارد"
        
        msg += "\n\n" + "=" * 50 + "\n"
        msg += "📦 آرشیوها:\n"
        msg += "=" * 50 + "\n"
        if archives:
            msg += "\n".join(archives[:10])  # فقط 10 تای اول
            if len(archives) > 10:
                msg += f"\n\n... و {len(archives) - 10} فایل دیگر"
        else:
            msg += "هیچ فایل آرشیوی وجود ندارد"
        
        msg += f"\n\n📊 جمع کل: {len(backups)} پشتیبان + {len(archives)} آرشیو"
        
        # نمایش
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("📚 آرشیوها و پشتیبان‌ها")
        msg_box.setText(msg)
        msg_box.setFont(QFont("Courier New", 9))
        msg_box.setStyleSheet("QLabel { min-width: 600px; max-height: 500px; }")
        msg_box.exec()
    
    def show_database_stats(self):
        """نمایش آمار کامل دیتابیس"""
        from app.core.database import db_manager
        from app.models import SalesData, SheetConfig, ExportTemplate, ProcessLog, ExportLog
        from pathlib import Path
        import os
        
        try:
            db = db_manager.get_session()
            
            # شمارش رکوردها
            sales_count = db.query(SalesData).count()
            sheets_count = db.query(SheetConfig).count()
            templates_count = db.query(ExportTemplate).count()
            process_count = db.query(ProcessLog).count()
            export_count = db.query(ExportLog).count()
            
            # حجم دیتابیس
            db_path = Path("data/gt_land.db")
            db_size = os.path.getsize(db_path) / 1024 / 1024  # MB
            
            db.close()
            
            # ساخت پیام
            msg = f"""
📊 آمار کامل دیتابیس
{'=' * 50}

📁 اطلاعات فایل:
  • مسیر: {db_path}
  • حجم: {db_size:.2f} MB
  • نوع: SQLite

{'=' * 50}

📊 آمار جداول:

  📦 داده‌های فروش (sales_data):
     تعداد: {sales_count:,} رکورد

  📂 تنظیمات شیت (sheet_config):
     تعداد: {sheets_count:,} شیت

  📋 قالب‌های Export (export_template):
     تعداد: {templates_count:,} قالب

  📝 لاگ عملیات (process_logs):
     تعداد: {process_count:,} لاگ

  📤 لاگ Export (export_logs):
     تعداد: {export_count:,} لاگ

{'=' * 50}

✅ دیتابیس سالم و متصل است
            """
            
            QMessageBox.information(self, "📊 آمار دیتابیس", msg)
            
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در دریافت آمار:\n{str(e)}")
    
    def get_button_style(self, color):
        """استایل دکمه"""
        return f"""
            QPushButton {{
                background: {color};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 10pt;
                font-weight: bold;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
        """


from PyQt6.QtWidgets import QWidget

