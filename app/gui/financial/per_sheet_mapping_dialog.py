"""
UI جدید برای مدیریت Field Mapping به تفکیک هر SheetConfig
Per-Sheet Field Mapping Manager UI
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from typing import List

from app.core.financial.sheet_mapping_manager import SheetFieldMappingManager
from app.models.financial import TargetField, DataType
from app.models.sheet_config import SheetConfig


class PerSheetFieldMappingDialog(QDialog):
    """
    دیالوگ مدیریت Field Mapping برای هر SheetConfig
    
    ویژگی‌ها:
    - انتخاب SheetConfig از لیست
    - نمایش ستون‌های شیت
    - تعیین نقش برای هر ستون
    - Preset های از پیش آماده
    - اعتبارسنجی
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = SheetFieldMappingManager()
        self.current_config: SheetConfig = None
        
        self.setWindowTitle("🗂️ مدیریت نقش‌های فیلد - به تفکیک شیت")
        self.setMinimumSize(1000, 700)
        self.setup_ui()
        self.load_sheet_configs()
    
    def setup_ui(self):
        """ساخت رابط کاربری"""
        layout = QVBoxLayout(self)
        
        # === Header ===
        header = QLabel("🗂️ مدیریت نقش‌های فیلد - مخصوص هر شیت")
        header.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # === انتخاب SheetConfig ===
        config_group = QGroupBox("📋 انتخاب شیت")
        config_layout = QHBoxLayout()
        
        config_layout.addWidget(QLabel("شیت:"))
        self.combo_sheets = QComboBox()
        self.combo_sheets.currentIndexChanged.connect(self.on_sheet_changed)
        config_layout.addWidget(self.combo_sheets, 2)
        
        self.btn_apply_preset = QPushButton("🎯 اعمال Preset")
        self.btn_apply_preset.clicked.connect(self.apply_preset)
        config_layout.addWidget(self.btn_apply_preset)
        
        self.btn_validate = QPushButton("✅ اعتبارسنجی")
        self.btn_validate.clicked.connect(self.validate_mappings)
        config_layout.addWidget(self.btn_validate)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # === اطلاعات SheetConfig ===
        self.info_group = QGroupBox("ℹ️ اطلاعات شیت")
        info_layout = QGridLayout()
        
        self.lbl_name = QLabel()
        self.lbl_type = QLabel()
        self.lbl_url = QLabel()
        self.lbl_worksheet = QLabel()
        
        info_layout.addWidget(QLabel("نام:"), 0, 0)
        self.lbl_name.setWordWrap(True)
        info_layout.addWidget(self.lbl_name, 0, 1)
        
        info_layout.addWidget(QLabel("نوع:"), 1, 0)
        info_layout.addWidget(self.lbl_type, 1, 1)
        
        info_layout.addWidget(QLabel("Worksheet:"), 2, 0)
        info_layout.addWidget(self.lbl_worksheet, 2, 1)
        
        self.info_group.setLayout(info_layout)
        layout.addWidget(self.info_group)
        
        # === جدول Mapping ===
        table_label = QLabel("🗂️ نقش‌های فیلدها")
        table_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        layout.addWidget(table_label)
        
        self.table_mappings = QTableWidget()
        self.table_mappings.setColumnCount(6)
        self.table_mappings.setHorizontalHeaderLabels([
            "ستون در شیت", "نقش در سیستم", "نوع داده", "الزامی", "مقدار پیش‌فرض", "عملیات"
        ])
        self.table_mappings.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table_mappings.horizontalHeader().setStretchLastSection(True)
        self.table_mappings.setAlternatingRowColors(True)
        layout.addWidget(self.table_mappings)
        
        # === دکمه‌ها ===
        btn_layout = QHBoxLayout()
        
        self.btn_add_mapping = QPushButton("➕ افزودن نقش")
        self.btn_add_mapping.clicked.connect(self.add_mapping_row)
        btn_layout.addWidget(self.btn_add_mapping)
        
        self.btn_save_all = QPushButton("💾 ذخیره همه")
        self.btn_save_all.clicked.connect(self.save_all_mappings)
        btn_layout.addWidget(self.btn_save_all)
        
        btn_layout.addStretch()
        
        btn_close = QPushButton("بستن")
        btn_close.clicked.connect(self.close)
        btn_layout.addWidget(btn_close)
        
        layout.addLayout(btn_layout)
    
    def load_sheet_configs(self):
        """بارگذاری لیست SheetConfig ها"""
        self.combo_sheets.clear()
        
        configs = self.manager.get_sheet_configs()
        
        if not configs:
            QMessageBox.warning(
                self,
                "هشدار",
                "هیچ SheetConfig فعالی یافت نشد!\n\nابتدا از تنظیمات اولیه، شیت‌های خود را تعریف کنید."
            )
            return
        
        for config in configs:
            self.combo_sheets.addItem(
                f"{config.name} ({config.sheet_type})",
                userData=config
            )
    
    def on_sheet_changed(self, index: int):
        """تغییر SheetConfig"""
        if index < 0:
            return
        
        self.current_config = self.combo_sheets.itemData(index)
        if not self.current_config:
            return
        
        # نمایش اطلاعات
        self.lbl_name.setText(self.current_config.name)
        self.lbl_type.setText(self.current_config.sheet_type or "N/A")
        self.lbl_worksheet.setText(self.current_config.worksheet_name or "N/A")
        
        # بارگذاری Mapping ها
        self.load_mappings()
    
    def load_mappings(self):
        """بارگذاری Mapping های این SheetConfig"""
        if not self.current_config:
            return
        
        mappings = self.manager.get_mappings_for_sheet(self.current_config.id)
        
        self.table_mappings.setRowCount(len(mappings))
        
        for row, mapping in enumerate(mappings):
            # ستون در شیت
            self.table_mappings.setItem(row, 0, QTableWidgetItem(mapping.source_column))
            
            # نقش
            role_combo = QComboBox()
            for field in TargetField:
                role_combo.addItem(field.value, userData=field)
            role_combo.setCurrentText(mapping.target_field.value)
            self.table_mappings.setCellWidget(row, 1, role_combo)
            
            # نوع داده
            type_combo = QComboBox()
            for dtype in DataType:
                type_combo.addItem(dtype.value, userData=dtype)
            type_combo.setCurrentText(mapping.data_type.value)
            self.table_mappings.setCellWidget(row, 2, type_combo)
            
            # الزامی
            req_item = QTableWidgetItem("✅" if mapping.is_required else "❌")
            req_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_mappings.setItem(row, 3, req_item)
            
            # مقدار پیش‌فرض
            self.table_mappings.setItem(row, 4, QTableWidgetItem(mapping.default_value or ""))
            
            # دکمه حذف
            btn_delete = QPushButton("🗑️")
            btn_delete.clicked.connect(lambda checked, col=mapping.source_column: self.delete_mapping(col))
            self.table_mappings.setCellWidget(row, 5, btn_delete)
    
    def add_mapping_row(self):
        """افزودن یک ردیف جدید"""
        row = self.table_mappings.rowCount()
        self.table_mappings.insertRow(row)
        
        # ستون
        self.table_mappings.setItem(row, 0, QTableWidgetItem(""))
        
        # نقش
        role_combo = QComboBox()
        for field in TargetField:
            role_combo.addItem(field.value, userData=field)
        self.table_mappings.setCellWidget(row, 1, role_combo)
        
        # نوع داده
        type_combo = QComboBox()
        for dtype in DataType:
            type_combo.addItem(dtype.value, userData=dtype)
        self.table_mappings.setCellWidget(row, 2, type_combo)
        
        # الزامی
        self.table_mappings.setItem(row, 3, QTableWidgetItem("❌"))
        
        # پیش‌فرض
        self.table_mappings.setItem(row, 4, QTableWidgetItem(""))
        
        # حذف
        btn_delete = QPushButton("🗑️")
        btn_delete.clicked.connect(lambda: self.table_mappings.removeRow(row))
        self.table_mappings.setCellWidget(row, 5, btn_delete)
    
    def save_all_mappings(self):
        """ذخیره تمام Mapping ها"""
        if not self.current_config:
            QMessageBox.warning(self, "خطا", "لطفاً یک شیت انتخاب کنید")
            return
        
        saved_count = 0
        
        for row in range(self.table_mappings.rowCount()):
            # ستون
            source_col_item = self.table_mappings.item(row, 0)
            if not source_col_item or not source_col_item.text().strip():
                continue
            
            source_col = source_col_item.text().strip()
            
            # نقش
            role_combo = self.table_mappings.cellWidget(row, 1)
            target_field = role_combo.currentData()
            
            # نوع
            type_combo = self.table_mappings.cellWidget(row, 2)
            data_type = type_combo.currentData()
            
            # الزامی
            req_item = self.table_mappings.item(row, 3)
            is_required = req_item.text() == "✅"
            
            # پیش‌فرض
            default_item = self.table_mappings.item(row, 4)
            default_value = default_item.text() if default_item else None
            
            # ذخیره
            try:
                self.manager.set_mapping_for_sheet(
                    config_id=self.current_config.id,
                    config_name=self.current_config.name,
                    source_column=source_col,
                    target_field=target_field,
                    data_type=data_type,
                    is_required=is_required,
                    default_value=default_value
                )
                saved_count += 1
            except Exception as e:
                QMessageBox.warning(self, "خطا", f"خطا در ذخیره '{source_col}': {str(e)}")
        
        QMessageBox.information(
            self,
            "✅ موفق",
            f"{saved_count} نقش با موفقیت ذخیره شد"
        )
        
        # بروزرسانی
        self.load_mappings()
    
    def delete_mapping(self, source_column: str):
        """حذف یک Mapping"""
        if not self.current_config:
            return
        
        reply = QMessageBox.question(
            self,
            "تأیید",
            f"آیا مطمئن هستید که می‌خواهید نقش '{source_column}' را حذف کنید؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.manager.delete_mapping_for_sheet(self.current_config.id, source_column)
            self.load_mappings()
    
    def apply_preset(self):
        """اعمال Preset بر اساس نوع شیت"""
        if not self.current_config:
            QMessageBox.warning(self, "خطا", "لطفاً یک شیت انتخاب کنید")
            return
        
        sheet_type = self.current_config.sheet_type
        
        if sheet_type == "Purchase":
            preset = "Purchase"
        elif sheet_type == "Sale":
            preset = "Sale"
        elif sheet_type == "Bonus":
            preset = "Bonus"
        else:
            QMessageBox.warning(self, "خطا", f"نوع شیت '{sheet_type}' پشتیبانی نمی‌شود")
            return
        
        reply = QMessageBox.question(
            self,
            "تأیید",
            f"آیا می‌خواهید Preset '{preset}' را اعمال کنید?\n\n⚠️ نقش‌های فعلی حذف می‌شوند!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.manager.apply_preset_for_sheet(self.current_config.id, preset)
                self.load_mappings()
                QMessageBox.information(self, "✅ موفق", f"Preset '{preset}' با موفقیت اعمال شد")
            except Exception as e:
                QMessageBox.critical(self, "خطا", f"خطا در اعمال Preset:\n{str(e)}")
    
    def validate_mappings(self):
        """اعتبارسنجی Mapping ها"""
        if not self.current_config:
            QMessageBox.warning(self, "خطا", "لطفاً یک شیت انتخاب کنید")
            return
        
        result = self.manager.validate_mappings_for_sheet(self.current_config.id)
        
        message = f"📊 نتیجه اعتبارسنجی:\n\n"
        
        if result["valid"]:
            message += "✅ Mapping ها معتبر هستند\n"
        else:
            message += "❌ Mapping ها معتبر نیستند\n"
        
        if result["errors"]:
            message += "\n🔴 خطاها:\n"
            for error in result["errors"]:
                message += f"  • {error}\n"
        
        if result["warnings"]:
            message += "\n⚠️ هشدارها:\n"
            for warning in result["warnings"]:
                message += f"  • {warning}\n"
        
        if result["valid"] and not result["warnings"]:
            message += "\n✅ همه چیز آماده است!"
        
        QMessageBox.information(self, "اعتبارسنجی", message)
    
    def closeEvent(self, event):
        """بستن manager"""
        if self.manager:
            self.manager.close()
        super().closeEvent(event)
