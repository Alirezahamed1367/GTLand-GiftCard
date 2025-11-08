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
from app.gui.dialogs.template_manager_dialog import TemplateManagerDialog


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
        self.sheet_config = sheet_config  # اگر از یک شیت خاص باشد
        self.selected_data_ids = selected_data_ids  # داده‌های انتخابی (اگر باشد)
        self.selected_template = None
        self.output_path = None
        self.worker = None
        
        self.init_ui()
        self.load_templates()
        self.load_sheet_configs()  # بارگذاری لیست شیت‌ها
    
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
        
        # فیلتر شیت (جدید!)
        sheet_group = QGroupBox("📋 انتخاب شیت(ها)")
        sheet_layout = QVBoxLayout()
        
        self.sheet_combo = QComboBox()
        self.sheet_combo.currentIndexChanged.connect(self.update_data_count)
        sheet_layout.addWidget(self.sheet_combo)
        
        sheet_info = QLabel("💡 می‌توانید از یک یا چند شیت Export بگیرید")
        sheet_info.setStyleSheet("color: #666; font-size: 8pt; padding: 5px;")
        sheet_layout.addWidget(sheet_info)
        
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
    
    def load_sheet_configs(self):
        """بارگذاری لیست SheetConfig ها"""
        try:
            configs = db_manager.get_all_sheet_configs()
            
            self.sheet_combo.clear()
            self.sheet_combo.addItem("همه شیت‌ها", None)
            
            for config in configs:
                self.sheet_combo.addItem(
                    f"📊 {config.name}",
                    config.id
                )
            
            # اگر از قبل یک شیت انتخاب شده بود
            if self.sheet_config:
                for i in range(self.sheet_combo.count()):
                    if self.sheet_combo.itemData(i) == self.sheet_config.id:
                        self.sheet_combo.setCurrentIndex(i)
                        break
                        
        except Exception as e:
            app_logger.error(f"خطا در بارگذاری SheetConfig ها: {str(e)}")

    
    def on_template_changed(self, index):
        """تغییر Template"""
        template = self.template_combo.currentData()
        
        if template:
            self.selected_template = template
            
            # بررسی column_mappings
            mapping_count = 0
            if template.column_mappings and isinstance(template.column_mappings, (dict, list)):
                mapping_count = len(template.column_mappings)
            
            info = f"""
📋 نام: {template.name}
📄 Worksheet: {template.target_worksheet}
📍 شروع: سطر {template.start_row}, ستون {template.start_column}
🗺️ تعداد Mapping: {mapping_count} ستون
            """
            self.template_info_label.setText(info.strip())
            
            # پیشنهاد نام فایل
            if not self.output_path:
                suggested_name = excel_exporter.generate_output_filename(
                    template,
                    self.sheet_config.name if self.sheet_config else ""
                )
                self.output_path_label.setText(suggested_name)
        else:
            self.selected_template = None
            self.template_info_label.setText("هیچ Template فعالی وجود ندارد")
    
    def update_data_count(self):
        """بروزرسانی تعداد داده‌ها با توجه به فیلتر SheetConfig"""
        try:
            filter_index = self.filter_combo.currentIndex()
            selected_sheet_id = self.sheet_combo.currentData()
            
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
            
            # فیلتر بر اساس SheetConfig
            if selected_sheet_id is not None:
                data_list = [d for d in data_list if d.sheet_config_id == selected_sheet_id]
            
            count = len(data_list)
            
            # نمایش با جزئیات
            if selected_sheet_id:
                config = db_manager.get_sheet_config(selected_sheet_id)
                sheet_name = config.name if config else "نامشخص"
                self.data_count_label.setText(f"{count:,} رکورد از '{sheet_name}'")
            else:
                self.data_count_label.setText(f"{count:,} رکورد (همه شیت‌ها)")
            
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
            selected_sheet_id = self.sheet_combo.currentData()
            
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
            
            # فیلتر بر اساس SheetConfig انتخابی
            if selected_sheet_id is not None:
                data_list = [d for d in data_list if d.sheet_config_id == selected_sheet_id]
                
                # اطلاع به کاربر
                config = db_manager.get_sheet_config(selected_sheet_id)
                sheet_name = config.name if config else "نامشخص"
                app_logger.info(f"Export فقط از شیت '{sheet_name}' ({len(data_list)} رکورد)")
            
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
