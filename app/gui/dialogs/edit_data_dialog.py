"""
دیالوگ ویرایش داده استخراج شده

توسعه‌دهنده: علیرضا حامد
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QFormLayout, QTextEdit,
    QMessageBox, QCheckBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import json
from datetime import datetime

from app.core.database import db_manager
from app.core.logger import app_logger


class EditDataDialog(QDialog):
    """دیالوگ ویرایش داده"""
    
    data_updated = pyqtSignal()
    
    def __init__(self, data_id, parent=None):
        super().__init__(parent)
        self.data_id = data_id
        self.original_data = None
        self.data_fields = {}
        
        self.load_data()
        self.init_ui()
    
    def load_data(self):
        """بارگذاری داده"""
        try:
            self.original_data = db_manager.get_sales_data_by_id(self.data_id)
            
            if not self.original_data:
                QMessageBox.critical(self, "خطا", "داده مورد نظر یافت نشد!")
                self.reject()
                return
            
        except Exception as e:
            app_logger.error(f"خطا در بارگذاری داده: {str(e)}")
            QMessageBox.critical(self, "خطا", f"خطا در بارگذاری: {str(e)}")
            self.reject()
    
    def init_ui(self):
        """راه‌اندازی رابط کاربری"""
        self.setWindowTitle("✏️ ویرایش داده")
        self.setMinimumWidth(600)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        layout = QVBoxLayout(self)
        
        # عنوان
        title = QLabel("✏️ ویرایش داده استخراج شده")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #FF9800; padding: 10px;")
        layout.addWidget(title)
        
        # اطلاعات اصلی
        info_group = QGroupBox("📊 اطلاعات داده")
        info_layout = QFormLayout()
        
        # نمایش اطلاعات ثابت
        info_layout.addRow("🆔 شناسه:", QLabel(str(self.original_data.id)))
        info_layout.addRow("📅 تاریخ استخراج:", 
                          QLabel(self.original_data.extracted_at.strftime("%Y-%m-%d %H:%M")))
        
        if self.original_data.is_exported:
            export_label = QLabel("✅ Export شده")
            export_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            info_layout.addRow("وضعیت:", export_label)
            
            if self.original_data.exported_at:
                info_layout.addRow("تاریخ Export:", 
                                  QLabel(self.original_data.exported_at.strftime("%Y-%m-%d %H:%M")))
        else:
            export_label = QLabel("❌ Export نشده")
            export_label.setStyleSheet("color: #F44336; font-weight: bold;")
            info_layout.addRow("وضعیت:", export_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # ویرایش داده‌ها
        edit_group = QGroupBox("✏️ ویرایش فیلدها")
        edit_layout = QVBoxLayout()
        
        # JSON Viewer/Editor
        json_label = QLabel("📝 داده JSON (قابل ویرایش):")
        edit_layout.addWidget(json_label)
        
        self.json_editor = QTextEdit()
        self.json_editor.setMinimumHeight(200)
        self.json_editor.setStyleSheet("""
            QTextEdit {
                border: 2px solid #e0e0e0;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Courier New';
                font-size: 10pt;
            }
        """)
        
        # نمایش JSON با فرمت زیبا
        try:
            # SalesData.data is already a dict (JSON column)
            if isinstance(self.original_data.data, dict):
                formatted_json = json.dumps(self.original_data.data, ensure_ascii=False, indent=2)
            else:
                # If it's a string, parse it first
                json_data = json.loads(self.original_data.data)
                formatted_json = json.dumps(json_data, ensure_ascii=False, indent=2)
            self.json_editor.setPlainText(formatted_json)
        except Exception as e:
            # Fallback to string representation
            self.json_editor.setPlainText(str(self.original_data.data))
        
        edit_layout.addWidget(self.json_editor)
        
        # گزینه‌ها
        options_layout = QHBoxLayout()
        
        self.mark_updated_check = QCheckBox("✨ علامت‌گذاری به عنوان 'ویرایش شده'")
        self.mark_updated_check.setChecked(True)
        self.mark_updated_check.setStyleSheet("font-size: 10pt;")
        options_layout.addWidget(self.mark_updated_check)
        
        if self.original_data.is_exported:
            self.reexport_check = QCheckBox("🔄 نیاز به Re-export")
            self.reexport_check.setChecked(True)
            self.reexport_check.setStyleSheet("font-size: 10pt; color: #FF9800;")
            options_layout.addWidget(self.reexport_check)
        
        edit_layout.addLayout(options_layout)
        
        edit_group.setLayout(edit_layout)
        layout.addWidget(edit_group)
        
        # راهنما
        help_label = QLabel(
            "💡 نکته: بعد از ویرایش، داده به عنوان 'ویرایش شده' علامت‌گذاری می‌شود "
            "و در صورت نیاز، می‌توانید دوباره Export کنید."
        )
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: #666; font-size: 9pt; padding: 10px; background: #f5f5f5; border-radius: 5px;")
        layout.addWidget(help_label)
        
        # دکمه‌ها
        buttons_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 ذخیره")
        save_btn.setStyleSheet(self.get_button_style("#4CAF50"))
        save_btn.clicked.connect(self.save_changes)
        buttons_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("❌ انصراف")
        cancel_btn.setStyleSheet(self.get_button_style("#F44336"))
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def save_changes(self):
        """ذخیره تغییرات"""
        try:
            # اعتبارسنجی JSON
            new_json_text = self.json_editor.toPlainText()
            
            try:
                new_data = json.loads(new_json_text)  # Parse to validate and use
            except json.JSONDecodeError as e:
                QMessageBox.warning(
                    self,
                    "خطای JSON",
                    f"فرمت JSON نامعتبر است!\n\n{str(e)}"
                )
                return
            
            # تأیید تغییرات
            reply = QMessageBox.question(
                self,
                "تأیید ذخیره",
                "آیا از ذخیره تغییرات اطمینان دارید؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                return
            
            # بروزرسانی داده
            update_data = {
                'data': new_data  # Store as dict, not string
            }
            
            # علامت‌گذاری به عنوان Updated
            if self.mark_updated_check.isChecked():
                update_data['is_updated'] = True
                update_data['update_count'] = (self.original_data.update_count or 0) + 1
            
            # Re-export
            if hasattr(self, 'reexport_check') and self.reexport_check.isChecked():
                update_data['is_exported'] = False
                update_data['exported_at'] = None
            
            # ذخیره در دیتابیس
            success = db_manager.update_sales_data(self.data_id, update_data)
            
            if success:
                QMessageBox.information(
                    self,
                    "موفق",
                    "✅ تغییرات با موفقیت ذخیره شد!"
                )
                
                self.data_updated.emit()
                self.accept()
            else:
                QMessageBox.critical(
                    self,
                    "خطا",
                    "❌ خطا در ذخیره تغییرات!"
                )
        
        except Exception as e:
            app_logger.error(f"خطا در ذخیره تغییرات: {str(e)}")
            QMessageBox.critical(
                self,
                "خطا",
                f"❌ خطا: {str(e)}"
            )
    
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
                min-width: 100px;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
        """
