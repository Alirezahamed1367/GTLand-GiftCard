"""
دیالوگ Export پیشرفته به Excel

توسعه‌دهنده: علیرضا حامد
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QComboBox, QFileDialog, QCheckBox,
    QProgressDialog, QGroupBox, QFormLayout, QSpinBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from pathlib import Path
from datetime import datetime
from typing import Optional

from app.core.database import db_manager
from app.core.excel_exporter import excel_exporter
from app.core.logger import app_logger
from app.gui.dialogs.template_manager_dialog_advanced import TemplateManagerDialog


class ExportWorker(QThread):
    """Worker برای Export در Background"""
    
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, template, data_list, output_path, apply_styling=True):
        super().__init__()
        self.template = template
        self.data_list = data_list
        self.output_path = output_path
        self.apply_styling = apply_styling
    
    def run(self):
        """اجرای Export"""
        try:
            self.progress.emit(10, "شروع Export...")
            
            if not self.data_list:
                self.finished.emit(False, "هیچ داده‌ای برای Export یافت نشد!")
                return
            
            self.progress.emit(30, f"Export {len(self.data_list)} رکورد...")
            
            # Export اصلی
            if self.apply_styling:
                success, message = excel_exporter.export_with_formatting(
                    self.template,
                    self.data_list,
                    self.output_path
                )
            else:
                success, message = excel_exporter.export_to_excel(
                    self.template,
                    self.data_list,
                    self.output_path
                )
            
            self.progress.emit(100, "تکمیل شد!")
            self.finished.emit(success, message)
            
        except Exception as e:
            app_logger.error(f"خطا در Export Worker: {str(e)}")
            self.finished.emit(False, f"خطا: {str(e)}")


class AdvancedExportDialog(QDialog):
    """دیالوگ Export پیشرفته"""
    
    export_completed = pyqtSignal(bool, str)
    
    def __init__(self, parent=None, sheet_config=None, selected_data_ids=None):
        super().__init__(parent)
        self.sheet_config = sheet_config  # اگر از یک شیت خاص باشد (deprecated)
        self.selected_data_ids = selected_data_ids  # داده‌های انتخابی (اگر باشد)
        self.selected_template = None
        self.output_path = None
        self.worker = None
        
        self.init_ui()
        self.load_templates()
    
    def init_ui(self):
        """راه‌اندازی رابط کاربری"""
        self.setWindowTitle("📤 Export به Excel")
        self.setMinimumWidth(600)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        layout = QVBoxLayout(self)
        
        # عنوان
        title = QLabel("📤 Export داده‌ها به Excel")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #2196F3; padding: 10px;")
        layout.addWidget(title)
        
        # انتخاب Template
        template_group = QGroupBox("🗂️ انتخاب Template")
        template_layout = QVBoxLayout()
        
        template_select_layout = QHBoxLayout()
        template_select_layout.addWidget(QLabel("Template:"))
        
        self.template_combo = QComboBox()
        self.template_combo.currentIndexChanged.connect(self.on_template_changed)
        template_select_layout.addWidget(self.template_combo, stretch=1)
        
        manage_template_btn = QPushButton("⚙️ مدیریت")
        manage_template_btn.clicked.connect(self.manage_templates)
        manage_template_btn.setStyleSheet(self.get_button_style("#9C27B0"))
        template_select_layout.addWidget(manage_template_btn)
        
        template_layout.addLayout(template_select_layout)
        
        # اطلاعات Template
        self.template_info_label = QLabel("هیچ Template انتخاب نشده")
        self.template_info_label.setStyleSheet("color: #666; padding: 5px; font-size: 9pt;")
        template_layout.addWidget(self.template_info_label)
        
        template_group.setLayout(template_layout)
        layout.addWidget(template_group)
        
        # حذف شد: انتخاب شیت (چون Template مشخص می‌کند)
        # به جای آن، نمایش شیت‌های Template
        sheet_group = QGroupBox("📋 شیت‌های منبع داده")
        sheet_layout = QVBoxLayout()
        
        self.sheet_info_label = QLabel("⏳ لطفاً ابتدا یک Template انتخاب کنید")
        self.sheet_info_label.setStyleSheet("""
            background: #E3F2FD;
            padding: 10px;
            border-radius: 5px;
            color: #1976D2;
            font-size: 10pt;
        """)
        self.sheet_info_label.setWordWrap(True)
        sheet_layout.addWidget(self.sheet_info_label)
        
        sheet_group.setLayout(sheet_layout)
        layout.addWidget(sheet_group)
        
        # فیلتر داده‌ها
        data_group = QGroupBox("📊 داده‌های Export")
        data_layout = QFormLayout()
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            "فقط داده‌های جدید (Export نشده)",
            "داده‌های ویرایش شده (Re-export)",
            "همه داده‌ها",
            "محدوده سفارشی"
        ])
        self.filter_combo.currentIndexChanged.connect(self.update_data_count)
        data_layout.addRow("فیلتر:", self.filter_combo)
        
        # محدوده سفارشی
        range_layout = QHBoxLayout()
        self.limit_spin = QSpinBox()
        self.limit_spin.setMinimum(1)
        self.limit_spin.setMaximum(100000)
        self.limit_spin.setValue(1000)
        self.limit_spin.setEnabled(False)
        range_layout.addWidget(QLabel("حداکثر:"))
        range_layout.addWidget(self.limit_spin)
        range_layout.addStretch()
        data_layout.addRow("", range_layout)
        
        self.data_count_label = QLabel("0 رکورد")
        self.data_count_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        data_layout.addRow("تعداد:", self.data_count_label)
        
        data_group.setLayout(data_layout)
        layout.addWidget(data_group)
        
        # تنظیمات Export
        settings_group = QGroupBox("⚙️ تنظیمات")
        settings_layout = QVBoxLayout()
        
        self.styling_checkbox = QCheckBox("✨ اعمال فرمت‌بندی (رنگ، border، ...)")
        self.styling_checkbox.setChecked(True)
        settings_layout.addWidget(self.styling_checkbox)
        
        self.auto_open_checkbox = QCheckBox("📂 باز کردن خودکار فایل بعد از Export")
        self.auto_open_checkbox.setChecked(True)
        settings_layout.addWidget(self.auto_open_checkbox)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # انتخاب مسیر خروجی
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("📁 مسیر ذخیره:"))
        
        self.output_path_label = QLabel("انتخاب نشده")
        self.output_path_label.setStyleSheet("color: #666; font-style: italic;")
        output_layout.addWidget(self.output_path_label, stretch=1)
        
        browse_btn = QPushButton("📂 انتخاب")
        browse_btn.clicked.connect(self.browse_output_path)
        browse_btn.setStyleSheet(self.get_button_style("#FF9800"))
        output_layout.addWidget(browse_btn)
        
        layout.addLayout(output_layout)
        
        layout.addStretch()
        
        # دکمه‌های اصلی
        buttons_layout = QHBoxLayout()
        
        export_btn = QPushButton("🚀 شروع Export")
        export_btn.setStyleSheet(self.get_button_style("#4CAF50"))
        export_btn.clicked.connect(self.start_export)
        buttons_layout.addWidget(export_btn)
        
        cancel_btn = QPushButton("❌ انصراف")
        cancel_btn.setStyleSheet(self.get_button_style("#F44336"))
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
        
        # بروزرسانی تعداد داده‌ها
        self.update_data_count()
    
    def load_templates(self):
        """بارگذاری Template ها"""
        try:
            templates = db_manager.get_all_export_templates(active_only=True)
            
            self.template_combo.clear()
            
            if not templates:
                self.template_combo.addItem("هیچ Template فعالی وجود ندارد", None)
                return
            
            for template in templates:
                self.template_combo.addItem(template.name, template)
            
            # انتخاب اولین Template
            if templates:
                self.on_template_changed(0)
                
        except Exception as e:
            app_logger.error(f"خطا در بارگذاری Template ها: {str(e)}")
    
    def on_template_changed(self, index):
        """تغییر Template - نمایش شیت‌های مرتبط"""
        template = self.template_combo.currentData()
        
        if template:
            self.selected_template = template
            
            # بررسی column_mappings
            mapping_count = 0
            if template.column_mappings and isinstance(template.column_mappings, (dict, list)):
                mapping_count = len(template.column_mappings)
            
            # نمایش اطلاعات Template
            info = f"""
📋 نام: {template.name}
� نوع: {template.template_type}
�📄 Worksheet: {template.target_worksheet}
📍 شروع: سطر {template.start_row}, ستون {template.start_column}
🗺️ تعداد Mapping: {mapping_count} ستون
            """
            self.template_info_label.setText(info.strip())
            
            # استخراج و نمایش شیت‌های منبع داده از Template
            source_sheet_ids = self.extract_source_sheets_from_template(template)
            
            if source_sheet_ids:
                sheets_text = "📊 داده از این شیت‌ها استخراج می‌شود:\n\n"
                sheet_names = []
                for sheet_id in source_sheet_ids:
                    config = db_manager.get_sheet_config(sheet_id)
                    if config:
                        sheets_text += f"  ✓ {config.name}\n"
                        sheet_names.append(config.name)
                    else:
                        sheets_text += f"  ⚠️ شیت #{sheet_id} (حذف شده)\n"
                
                sheets_text += f"\n💡 {len(source_sheet_ids)} شیت در Template تعریف شده است"
                self.sheet_info_label.setText(sheets_text)
                self.sheet_info_label.setStyleSheet("""
                    background: #E8F5E9;
                    padding: 10px;
                    border-radius: 5px;
                    color: #2E7D32;
                    font-size: 10pt;
                    border-left: 4px solid #4CAF50;
                """)
            else:
                self.sheet_info_label.setText("⚠️ این Template هنوز شیت منبع ندارد")
                self.sheet_info_label.setStyleSheet("""
                    background: #FFF3E0;
                    padding: 10px;
                    border-radius: 5px;
                    color: #E65100;
                    font-size: 10pt;
                    border-left: 4px solid #FF9800;
                """)
            
            # پیشنهاد نام فایل
            if not self.output_path:
                suggested_name = excel_exporter.generate_output_filename(
                    template,
                    ""  # نام شیت دیگر استفاده نمی‌شود
                )
                self.output_path_label.setText(suggested_name)
        else:
            self.selected_template = None
            self.template_info_label.setText("هیچ Template فعالی وجود ندارد")
            self.sheet_info_label.setText("⏳ لطفاً ابتدا یک Template انتخاب کنید")
        
        self.update_data_count()
    
    def extract_source_sheets_from_template(self, template):
        """استخراج ID های شیت‌های منبع از column_mappings"""
        source_sheet_ids = set()
        
        try:
            if not template.column_mappings:
                return []
            
            mappings = template.column_mappings
            if isinstance(mappings, str):
                import json
                mappings = json.loads(mappings)
            
            # اگر dict است (فرمت: {"A": {"source_sheet": 2, ...}, ...})
            if isinstance(mappings, dict):
                for mapping in mappings.values():
                    if isinstance(mapping, dict) and 'source_sheet' in mapping:
                        sheet_id = mapping['source_sheet']
                        # تبدیل به int در صورت لزوم
                        if isinstance(sheet_id, (int, float)):
                            source_sheet_ids.add(int(sheet_id))
                        elif isinstance(sheet_id, str) and sheet_id.isdigit():
                            source_sheet_ids.add(int(sheet_id))
            # اگر list است (فرمت: [{"source_sheet": 2, ...}, ...])
            elif isinstance(mappings, list):
                for mapping in mappings:
                    if isinstance(mapping, dict) and 'source_sheet' in mapping:
                        sheet_id = mapping['source_sheet']
                        if isinstance(sheet_id, (int, float)):
                            source_sheet_ids.add(int(sheet_id))
                        elif isinstance(sheet_id, str) and sheet_id.isdigit():
                            source_sheet_ids.add(int(sheet_id))
            
            return sorted(list(source_sheet_ids))
            
        except Exception as e:
            app_logger.error(f"خطا در استخراج شیت‌های منبع: {str(e)}")
            return []
    
    def update_data_count(self):
        """بروزرسانی تعداد داده‌ها - فیلتر بر اساس شیت‌های Template"""
        try:
            filter_index = self.filter_combo.currentIndex()
            
            # فعال/غیرفعال کردن محدوده
            self.limit_spin.setEnabled(filter_index == 3)
            
            # دریافت داده‌ها
            if filter_index == 0:  # فقط جدید
                data_list = db_manager.get_sales_data_by_export_status(is_exported=False)
            elif filter_index == 1:  # ویرایش شده
                data_list = db_manager.get_updated_sales_data()
            elif filter_index == 2:  # همه
                data_list = db_manager.get_all_sales_data()
            else:  # محدوده سفارشی
                data_list = db_manager.get_all_sales_data()[:self.limit_spin.value()]
            
            # فیلتر بر اساس شیت‌های Template
            selected_template = self.template_combo.currentData()
            if selected_template:
                # دریافت ID های شیت‌های منبع از Template
                source_sheet_ids = self.extract_source_sheets_from_template(selected_template)
                
                if source_sheet_ids:
                    # فیلتر داده‌ها فقط از شیت‌های Template
                    data_list = [d for d in data_list if d.sheet_config_id in source_sheet_ids]
                    
                    # دریافت نام شیت‌ها برای نمایش
                    sheet_names = []
                    for sheet_id in source_sheet_ids:
                        config = db_manager.get_sheet_config(sheet_id)
                        if config:
                            sheet_names.append(config.name)
            
            count = len(data_list)
            
            # نمایش با جزئیات
            if selected_template and source_sheet_ids:
                if len(source_sheet_ids) == 1 and sheet_names:
                    self.data_count_label.setText(f"{count:,} رکورد از '{sheet_names[0]}'")
                else:
                    self.data_count_label.setText(f"{count:,} رکورد از {len(source_sheet_ids)} شیت")
            else:
                self.data_count_label.setText(f"{count:,} رکورد")
            
        except Exception as e:
            app_logger.error(f"خطا در شمارش: {str(e)}")
            self.data_count_label.setText("0 رکورد")

    
    def manage_templates(self):
        """مدیریت Template ها"""
        dialog = TemplateManagerDialog(self)
        if dialog.exec():
            # بروزرسانی لیست
            self.load_templates()
    
    def browse_output_path(self):
        """انتخاب مسیر خروجی"""
        suggested_name = self.output_path_label.text()
        if suggested_name == "انتخاب نشده" and self.selected_template:
            suggested_name = excel_exporter.generate_output_filename(
                self.selected_template,
                self.sheet_config.name if self.sheet_config else ""
            )
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "انتخاب مسیر ذخیره",
            str(Path.home() / "Downloads" / suggested_name),
            "Excel Files (*.xlsx)"
        )
        
        if file_path:
            self.output_path = file_path
            self.output_path_label.setText(Path(file_path).name)
            self.output_path_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
    
    def start_export(self):
        """شروع Export"""
        # اعتبارسنجی
        if not self.selected_template:
            QMessageBox.warning(self, "هشدار", "لطفاً یک Template انتخاب کنید!")
            return
        
        if not self.output_path:
            QMessageBox.warning(self, "هشدار", "لطفاً مسیر ذخیره را انتخاب کنید!")
            return
        
        try:
            # دریافت داده‌ها بر اساس فیلتر
            filter_index = self.filter_combo.currentIndex()
            
            if filter_index == 0:  # فقط جدید
                data_list = db_manager.get_sales_data_by_export_status(is_exported=False)
            elif filter_index == 1:  # ویرایش شده
                # تأیید Re-export
                reply = QMessageBox.question(
                    self,
                    "تأیید Re-export",
                    "این داده‌ها قبلاً Export شده‌اند.\nآیا می‌خواهید دوباره Export شوند؟",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.No:
                    return
                
                data_list = db_manager.get_updated_sales_data()
            elif filter_index == 2:  # همه
                data_list = db_manager.get_all_sales_data()
            else:  # محدوده سفارشی
                data_list = db_manager.get_all_sales_data()[:self.limit_spin.value()]
            
            # فیلتر بر اساس شیت‌های Template
            source_sheet_ids = self.extract_source_sheets_from_template(self.selected_template)
            
            if source_sheet_ids:
                # فیلتر داده‌ها فقط از شیت‌های Template
                data_list = [d for d in data_list if d.sheet_config_id in source_sheet_ids]
                
                # دریافت نام شیت‌ها برای لاگ
                sheet_names = []
                for sheet_id in source_sheet_ids:
                    config = db_manager.get_sheet_config(sheet_id)
                    if config:
                        sheet_names.append(config.name)
                
                # اطلاع به کاربر
                if len(sheet_names) == 1:
                    app_logger.info(f"Export فقط از شیت '{sheet_names[0]}' ({len(data_list)} رکورد)")
                else:
                    app_logger.info(f"Export از {len(sheet_names)} شیت: {', '.join(sheet_names)} ({len(data_list)} رکورد)")
            
            if not data_list:
                QMessageBox.information(self, "اطلاع", "هیچ داده‌ای برای Export یافت نشد!")
                return
            
            # نمایش Progress Dialog
            progress = QProgressDialog("در حال Export...", "لغو", 0, 100, self)
            progress.setWindowTitle("Export")
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setAutoClose(True)
            
            # ایجاد Worker
            self.worker = ExportWorker(
                self.selected_template,
                data_list,
                self.output_path,
                self.styling_checkbox.isChecked()
            )
            
            # اتصال سیگنال‌ها
            self.worker.progress.connect(lambda val, msg: (
                progress.setValue(val),
                progress.setLabelText(msg)
            ))
            self.worker.finished.connect(lambda success, msg: self.on_export_finished(success, msg, progress))
            
            # شروع
            self.worker.start()
            progress.show()
            
        except Exception as e:
            app_logger.error(f"خطا در شروع Export: {str(e)}")
            QMessageBox.critical(self, "خطا", f"❌ خطا: {str(e)}")
    
    def on_export_finished(self, success, message, progress_dialog):
        """پایان Export"""
        progress_dialog.close()
        
        if success:
            QMessageBox.information(self, "موفق", message)
            
            # باز کردن فایل
            if self.auto_open_checkbox.isChecked():
                import os
                os.startfile(self.output_path)
            
            self.export_completed.emit(True, message)
            self.accept()
        else:
            QMessageBox.critical(self, "خطا", f"❌ {message}")
            self.export_completed.emit(False, message)
    
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
