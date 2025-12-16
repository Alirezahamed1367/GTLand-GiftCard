"""
دیالوگ افزودن/ویرایش تنظیمات Google Sheet
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QPushButton, QCheckBox,
    QLabel, QMessageBox, QGroupBox, QSpinBox, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QScreen, QColor
import json
from typing import Tuple

from app.models import SheetConfig
from app.models.financial import get_financial_session, FieldRole
from app.core.database import db_manager
from app.core.google_sheets import GoogleSheetExtractor
from app.utils.ui_constants import (
    FONT_SIZE_TITLE, BUTTON_HEIGHT_MEDIUM, COLOR_PRIMARY, 
    COLOR_SUCCESS, COLOR_DANGER, get_button_style, get_responsive_dialog_size
)


class SheetConfigDialog(QDialog):
    """دیالوگ تنظیمات Google Sheet"""
    
    def __init__(self, parent=None, sheet_config=None):
        super().__init__(parent)
        self.sheet_config = sheet_config
        self.is_edit_mode = sheet_config is not None
        self.column_headers = []
        self.sample_data = []
        self.role_mappings = {}  # {column_name: role_id}
        self.financial_db = get_financial_session()
        self.init_ui()
        
        if self.is_edit_mode:
            self.load_data()
    
    def init_ui(self):
        """راه‌اندازی رابط کاربری"""
        title = "✏️ ویرایش" if self.is_edit_mode else "➕ افزودن شیت"
        self.setWindowTitle(title)
        
        # سایز بهینه - کوچک‌تر
        self.resize(700, 600)  # قبلاً خیلی بزرگ بود
        self.setMaximumWidth(800)
        
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)  # کاهش فاصله
        layout.setContentsMargins(15, 15, 15, 15)  # کاهش حاشیه
        
        # عنوان کوچک‌تر
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", FONT_SIZE_TITLE, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {COLOR_PRIMARY}; padding: 10px;")
        layout.addWidget(title_label)
        
        # اطلاعات اصلی
        main_group = QGroupBox("📋 اطلاعات اصلی")
        main_layout = QFormLayout()
        main_layout.setSpacing(10)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("مثال: فروش تهران")
        main_layout.addRow("نام:", self.name_input)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://docs.google.com/spreadsheets/d/...")
        main_layout.addRow("آدرس شیت:", self.url_input)
        
        self.worksheet_input = QLineEdit()
        self.worksheet_input.setPlaceholderText("مثال: Sheet1")
        self.worksheet_input.setText("Sheet1")
        main_layout.addRow("نام برگه:", self.worksheet_input)
        
        # ⭐ نوع شیت - بسیار مهم!
        self.type_combo = QComboBox()
        self.type_combo.addItem("🛒 خرید (Purchase)", "Purchase")
        self.type_combo.addItem("💰 فروش (Sale)", "Sale")
        self.type_combo.addItem("🎁 بونوس (Bonus)", "Bonus")
        self.type_combo.setStyleSheet("""
            QComboBox {
                padding: 6px;
                border: 2px solid #2196F3;
                border-radius: 5px;
                background: white;
                font-size: 10pt;
                font-weight: bold;
            }
            QComboBox:hover {
                border-color: #1976D2;
                background: #E3F2FD;
            }
        """)
        type_help = QLabel("🔔 این انتخاب بسیار مهم است و نمی‌توان بعداً تغییرش داد!")
        type_help.setStyleSheet("color: #D32F2F; font-weight: bold; font-size: 9pt;")
        main_layout.addRow("نوع شیت:", self.type_combo)
        main_layout.addRow("", type_help)
        
        main_group.setLayout(main_layout)
        layout.addWidget(main_group)
        
        # دکمه تست ارتباط
        test_btn = QPushButton("🔌 تست ارتباط و دریافت ستون‌ها")
        test_btn.setStyleSheet("""
            QPushButton {
                background: #FF9800;
                color: white;
                padding: 12px;
                border: none;
                border-radius: 5px;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #F57C00;
            }
        """)
        test_btn.clicked.connect(self.test_connection)
        layout.addWidget(test_btn)
        
        # ستون‌های کنترل
        control_group = QGroupBox("🎯 ستون‌های کنترل")
        control_layout = QFormLayout()
        control_layout.setSpacing(8)
        
        # توضیحات کوچک‌تر
        help_label = QLabel(
            "💡 نام Header یا حرف ستون\n"
            "پیشنهاد: Ready و Extracted"
        )
        help_label.setWordWrap(True)
        help_label.setStyleSheet("""
            background: #E3F2FD;
            padding: 6px;
            border-radius: 3px;
            color: #1565C0;
            font-size: 8pt;
            border-left: 3px solid #2196F3;
        """)
        control_layout.addRow(help_label)
        
        self.ready_col_input = QLineEdit()
        self.ready_col_input.setPlaceholderText("مثال: Ready یا H")
        self.ready_col_input.setText("Ready")
        self.ready_col_input.setToolTip("نام header یا حرف ستون در Google Sheet")
        control_layout.addRow("ستون آماده:", self.ready_col_input)
        
        self.extracted_col_input = QLineEdit()
        self.extracted_col_input.setPlaceholderText("مثال: Extracted یا I")
        self.extracted_col_input.setText("Extracted")
        self.extracted_col_input.setToolTip("نام header یا حرف ستون در Google Sheet")
        control_layout.addRow("ستون استخراج شده:", self.extracted_col_input)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # ستون‌های کلید یکتا
        unique_group = QGroupBox("🔑 ستون‌های کلیدی")
        unique_layout = QVBoxLayout()
        unique_layout.setSpacing(6)
        
        info_label = QLabel("ستون‌های یکتا (با کاما جدا کنید)")
        info_label.setStyleSheet("color: #666; font-size: 8pt;")
        unique_layout.addWidget(info_label)
        
        self.unique_cols_input = QLineEdit()
        self.unique_cols_input.setPlaceholderText("مثال: A,B,C")
        self.unique_cols_input.setText("A,B,C")
        unique_layout.addWidget(self.unique_cols_input)
        
        unique_group.setLayout(unique_layout)
        layout.addWidget(unique_group)
        
        # ستون‌های استخراج - کوچک‌تر
        columns_group = QGroupBox("📥 ستون‌های استخراج")
        columns_layout = QVBoxLayout()
        columns_layout.setSpacing(6)
        
        info_label2 = QLabel("خالی = همه ستون‌ها")
        info_label2.setStyleSheet("color: #666; font-size: 8pt;")
        columns_layout.addWidget(info_label2)
        
        self.columns_to_extract_input = QLineEdit()
        self.columns_to_extract_input.setPlaceholderText("مثال: A,B,C,D,E")
        columns_layout.addWidget(self.columns_to_extract_input)
        
        columns_group.setLayout(columns_layout)
        layout.addWidget(columns_group)
        
        # نقشه ستون‌ها - حذف (اختیاری)
        # mapping_group کاملاً حذف شد برای کوچک کردن
        
        # تنظیمات اضافی
        settings_layout = QHBoxLayout()
        
        self.active_checkbox = QCheckBox("✅ فعال")
        self.active_checkbox.setChecked(True)
        settings_layout.addWidget(self.active_checkbox)
        
        settings_layout.addWidget(QLabel("سطر شروع:"))
        self.start_row_input = QSpinBox()
        self.start_row_input.setMinimum(1)
        self.start_row_input.setMaximum(1000000)
        self.start_row_input.setValue(2)
        settings_layout.addWidget(self.start_row_input)
        
        settings_layout.addStretch()
        layout.addLayout(settings_layout)
        
        # دکمه‌ها
        buttons_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 ذخیره")
        save_btn.setMinimumHeight(BUTTON_HEIGHT_MEDIUM)
        save_btn.setStyleSheet(get_button_style(COLOR_SUCCESS))
        save_btn.clicked.connect(self.save)
        buttons_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("❌ انصراف")
        cancel_btn.setMinimumHeight(BUTTON_HEIGHT_MEDIUM)
        cancel_btn.setStyleSheet(get_button_style(COLOR_DANGER))
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_data(self):
        """بارگذاری داده‌های موجود"""
        if not self.sheet_config:
            return
        
        self.name_input.setText(self.sheet_config.name)
        self.url_input.setText(self.sheet_config.sheet_url)
        self.worksheet_input.setText(self.sheet_config.worksheet_name or "Sheet1")
        self.ready_col_input.setText(self.sheet_config.ready_column or "H")
        self.extracted_col_input.setText(self.sheet_config.extracted_column or "I")
        
        # نوع شیت
        sheet_type = self.sheet_config.sheet_type or "Purchase"
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == sheet_type:
                self.type_combo.setCurrentIndex(i)
                break
        
        # ستون‌های یکتا
        if self.sheet_config.unique_key_columns:
            unique_cols = ",".join(self.sheet_config.unique_key_columns)
            self.unique_cols_input.setText(unique_cols)
        
        # ستون‌های استخراج
        if hasattr(self.sheet_config, 'columns_to_extract') and self.sheet_config.columns_to_extract:
            extract_cols = ",".join(self.sheet_config.columns_to_extract)
            self.columns_to_extract_input.setText(extract_cols)
        
        self.active_checkbox.setChecked(self.sheet_config.is_active)
    
    def test_connection(self):
        """تست ارتباط با Google Sheets و دریافت ستون‌ها"""
        # بررسی URL
        url = self.url_input.text().strip()
        worksheet = self.worksheet_input.text().strip()
        
        if not url:
            QMessageBox.warning(self, "خطا", "لطفاً آدرس شیت را وارد کنید")
            return
        
        if not worksheet:
            QMessageBox.warning(self, "خطا", "لطفاً نام برگه را وارد کنید")
            return
        
        try:
            # دریافت داده از Google Sheets
            gs_extractor = GoogleSheetExtractor()
            sheet_data = gs_extractor.extract_ready_rows(
                sheet_url=url,
                worksheet_name=worksheet,
                ready_column=None,
                extracted_column=None,
                columns_to_extract=None,
                skip_rows=0
            )
            
            if not sheet_data or len(sheet_data) < 1:
                QMessageBox.warning(self, "خطا", "شیت خالی است یا قابل دسترسی نیست")
                return
            
            # ردیف اول = headers
            self.column_headers = sheet_data[0]
            
            # ردیف دوم = نمونه داده
            if len(sheet_data) > 1:
                self.sample_data = sheet_data[1]
            else:
                self.sample_data = [""] * len(self.column_headers)
            
            # نمایش جدول نگاشت
            self.show_mapping_table()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "خطا",
                f"❌ خطا در اتصال به Google Sheets:\n{str(e)}"
            )
    
    def show_mapping_table(self):
        """باز کردن دیالوگ نگاشت ستون‌ها"""
        # نمایش پیام آمار قبل از باز کردن دیالوگ
        QMessageBox.information(
            self,
            "ارتباط موفق",
            f"✅ ارتباط با Google Sheets برقرار شد!\n\n"
            f"📊 تعداد ستون‌ها: {len(self.column_headers)}\n"
            f"📝 تعداد ردیف‌های موجود: {len(self.sample_data)}\n\n"
            f"لطفاً در مرحله بعد نقش‌ها را برای هر ستون تنظیم کنید."
        )
        
        from app.gui.dialogs.column_role_mapping_dialog import ColumnRoleMappingDialog
        
        dialog = ColumnRoleMappingDialog(
            self.column_headers,
            self.sample_data,
            self
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # دریافت نگاشت‌ها
            self.role_mappings = dialog.get_mappings()
    
    def validate(self) -> Tuple[bool, str]:
        """اعتبارسنجی ورودی‌ها"""
        if not self.name_input.text().strip():
            return False, "نام شیت الزامی است!"
        
        if not self.url_input.text().strip():
            return False, "آدرس شیت الزامی است!"
        
        if not self.url_input.text().startswith("https://docs.google.com/spreadsheets/"):
            return False, "آدرس شیت نامعتبر است!"
        
        if not self.worksheet_input.text().strip():
            return False, "نام برگه الزامی است!"
        
        if not self.ready_col_input.text().strip():
            return False, "ستون آماده الزامی است!"
        
        if not self.extracted_col_input.text().strip():
            return False, "ستون استخراج شده الزامی است!"
        
        if not self.unique_cols_input.text().strip():
            return False, "حداقل یک ستون کلید یکتا الزامی است!"
        
        return True, ""
    
    def save(self):
        """ذخیره اطلاعات"""
        # اعتبارسنجی
        is_valid, error_msg = self.validate()
        if not is_valid:
            QMessageBox.warning(self, "خطا", error_msg)
            return
        
        # ⭐ بررسی اجباری: آیا نگاشت ستون‌ها انجام شده؟
        if not self.role_mappings:
            reply = QMessageBox.question(
                self,
                "⚠️ نگاشت ستون‌ها تنظیم نشده",
                "❌ شما هنوز نگاشت ستون‌ها را تنظیم نکرده‌اید!\n\n"
                "برای ذخیره شیت، باید:\n"
                "  1️⃣ دکمه 'تست ارتباط و دریافت ستون‌ها' را بزنید\n"
                "  2️⃣ نقش‌های ضروری را تنظیم کنید:\n"
                "      • identifier (کد محصول)\n"
                "      • value (مقدار)\n"
                "      • rate (نرخ)\n\n"
                "آیا می‌خواهید الان تست ارتباط انجام دهید؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.test_connection()
            return
        
        try:
            # آماده‌سازی داده‌ها
            unique_cols = [col.strip() for col in self.unique_cols_input.text().split(",")]
            
            # ستون‌های استخراج
            columns_text = self.columns_to_extract_input.text().strip()
            columns_to_extract = [col.strip() for col in columns_text.split(",")] if columns_text else None
            
            # نقشه ستون‌ها حذف شد (ساده‌سازی)
            column_mappings = None
            
            # ⭐ نوع شیت (بسیار مهم!)
            sheet_type = self.type_combo.currentData()
            
            data = {
                'name': self.name_input.text().strip(),
                'sheet_url': self.url_input.text().strip(),
                'worksheet_name': self.worksheet_input.text().strip(),
                'sheet_type': sheet_type,
                'ready_column': self.ready_col_input.text().strip(),
                'extracted_column': self.extracted_col_input.text().strip(),
                'unique_key_columns': unique_cols,
                'columns_to_extract': columns_to_extract,
                'column_mappings': column_mappings,
                'is_active': self.active_checkbox.isChecked()
            }
            
            if self.is_edit_mode:
                # بروزرسانی
                success, message = db_manager.update_sheet_config(self.sheet_config.id, data)
                sheet_id = self.sheet_config.id
            else:
                # ایجاد جدید (3 مقدار بازگشت می‌دهد)
                success, sheet_config, message = db_manager.create_sheet_config(data)
                sheet_id = sheet_config.id if sheet_config else None
            
            if success and sheet_id:
                # ذخیره نگاشت ستون‌ها
                self.save_column_mappings(sheet_id)
                
                QMessageBox.information(self, "موفق", "✅ " + message)
                self.accept()
            else:
                QMessageBox.critical(self, "خطا", "❌ " + message)
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "خطا", f"❌ خطا در ذخیره: {str(e)}")
    
    def save_column_mappings(self, sheet_id):
        """ذخیره نگاشت ستون‌ها به نقش‌ها"""
        if not self.role_mappings:
            return  # نگاشت تنظیم نشده
        
        try:
            saved_count = 0
            
            for column_name, (role_id, is_active) in self.role_mappings.items():
                # پیدا یا ایجاد CustomField
                custom_field = self.financial_db.query(CustomField).filter(
                    CustomField.name == column_name
                ).first()
                
                if custom_field:
                    # بروزرسانی
                    custom_field.role_id = role_id
                    custom_field.is_active = is_active
                else:
                    # ایجاد جدید
                    custom_field = CustomField(
                        name=column_name,
                        label_fa=column_name,
                        role_id=role_id,
                        data_type='text',
                        is_active=is_active
                    )
                    self.financial_db.add(custom_field)
                
                saved_count += 1
            
            # Commit
            self.financial_db.commit()
            
            print(f"✅ {saved_count} نگاشت ذخیره شد")
            
        except Exception as e:
            self.financial_db.rollback()
            print(f"❌ خطا در ذخیره نگاشت‌ها: {e}")
            raise
    
    def closeEvent(self, event):
        """بستن دیتابیس"""
        if hasattr(self, 'financial_db'):
            self.financial_db.close()
        event.accept()

