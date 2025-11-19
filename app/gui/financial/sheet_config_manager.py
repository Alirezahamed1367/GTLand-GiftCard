"""
Sheet Financial Config Manager UI
مدیریت تنظیمات مالی sheets - کاربر مشخص می‌کند هر sheet چه نوعی است
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QDialog, QFormLayout, QComboBox, QLineEdit,
    QTextEdit, QCheckBox, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from app.core.database import SessionLocal
from app.models.sheet_config import SheetConfig
from app.models.financial import FinancialSessionLocal, SheetFinancialConfig
from app.core.logger import app_logger
import json


class SheetConfigDialog(QDialog):
    """دیالوگ تنظیمات یک sheet"""
    
    def __init__(self, sheet_config: SheetConfig, financial_config: SheetFinancialConfig = None, parent=None):
        super().__init__(parent)
        self.sheet_config = sheet_config
        self.financial_config = financial_config
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle(f"Sheet Settings: {self.sheet_config.name}")
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)
        
        layout = QVBoxLayout(self)
        
        # فرم اصلی
        form = QFormLayout()
        
        # نام sheet (فقط نمایش)
        sheet_label = QLabel(self.sheet_config.name)
        sheet_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        form.addRow("Sheet Name:", sheet_label)
        
        # نوع داده
        self.data_type_combo = QComboBox()
        self.data_type_combo.addItems([
            "sale",      # فروش
            "purchase",  # خرید
            "payment",   # تسویه
            "mixed",     # ترکیبی
            "other"      # سایر
        ])
        self.data_type_combo.currentTextChanged.connect(self.on_type_changed)
        form.addRow("Data Type:", self.data_type_combo)
        
        # دپارتمان
        self.department_combo = QComboBox()
        self.department_combo.addItems(["Auto-detect", "TOPUP", "GIFTCARD"])
        form.addRow("Department:", self.department_combo)
        
        # Product Type
        self.product_input = QLineEdit()
        self.product_input.setPlaceholderText("Auto-detect or enter: PUBG, COD, RG, etc.")
        form.addRow("Product Type:", self.product_input)
        
        # فعال/غیرفعال
        self.active_checkbox = QCheckBox("Active for conversion")
        self.active_checkbox.setChecked(True)
        form.addRow("Status:", self.active_checkbox)
        
        layout.addLayout(form)
        
        # Field Mappings
        layout.addWidget(QLabel("Field Mappings:"))
        layout.addWidget(QLabel("Map each sheet column to financial field"))
        
        # بخش mapping بر اساس نوع
        self.mapping_widget = QWidget()
        self.mapping_layout = QFormLayout(self.mapping_widget)
        layout.addWidget(self.mapping_widget)
        
        # نمایش ستون‌های موجود در sheet
        available_columns = list(self.sheet_config.column_mappings.keys()) if self.sheet_config.column_mappings else []
        cols_text = ", ".join(available_columns[:10])
        if len(available_columns) > 10:
            cols_text += f", ... ({len(available_columns)} total)"
        
        available_label = QLabel(f"Available columns: {cols_text}")
        available_label.setWordWrap(True)
        available_label.setStyleSheet("color: #666; font-size: 9pt; padding: 5px;")
        layout.addWidget(available_label)
        
        # یادداشت
        layout.addWidget(QLabel("Notes:"))
        self.notes_text = QTextEdit()
        self.notes_text.setMaximumHeight(80)
        layout.addWidget(self.notes_text)
        
        # دکمه‌ها
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_config)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        # بارگذاری داده‌های موجود
        if self.financial_config:
            self.load_existing_config()
        else:
            self.on_type_changed("sale")  # default
    
    def on_type_changed(self, data_type):
        """تغییر فیلدهای mapping بر اساس نوع"""
        # پاک کردن mapping قبلی
        while self.mapping_layout.count():
            child = self.mapping_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        self.mapping_inputs = {}
        
        # فیلدهای مورد نیاز بر اساس نوع
        fields = {
            'sale': [
                ('label', 'Account Label/ID', True),
                ('customer', 'Customer Name', True),
                ('rate', 'Sale Rate', True),
                ('price', 'Final Price', True),
                ('amount', 'Amount Sold', False),
                ('date', 'Sale Date', False),
                ('seller', 'Seller Name', False),
            ],
            'purchase': [
                ('label', 'Account Label/ID', True),
                ('supplier', 'Supplier Name', True),
                ('purchase_price', 'Purchase Price', True),
                ('initial_balance', 'Initial Balance', False),
                ('date', 'Purchase Date', False),
            ],
            'payment': [
                ('customer', 'Customer Name', True),
                ('amount', 'Payment Amount', True),
                ('currency', 'Currency (USDT/IRR)', False),
                ('date', 'Payment Date', False),
                ('method', 'Payment Method', False),
            ]
        }
        
        if data_type not in fields:
            return
        
        for field_key, field_label, is_required in fields[data_type]:
            label_text = f"{field_label}{'*' if is_required else ''}"
            input_widget = QComboBox()
            input_widget.setEditable(True)
            
            # افزودن ستون‌های موجود
            if self.sheet_config.column_mappings:
                input_widget.addItems([""] + list(self.sheet_config.column_mappings.keys()))
            
            self.mapping_inputs[field_key] = input_widget
            self.mapping_layout.addRow(label_text, input_widget)
    
    def load_existing_config(self):
        """بارگذاری تنظیمات موجود"""
        cfg = self.financial_config
        
        self.data_type_combo.setCurrentText(cfg.data_type)
        
        if cfg.department_code:
            self.department_combo.setCurrentText(cfg.department_code)
        
        if cfg.product_type:
            self.product_input.setText(cfg.product_type)
        
        self.active_checkbox.setChecked(cfg.is_active)
        
        if cfg.notes:
            self.notes_text.setPlainText(cfg.notes)
        
        # بارگذاری mappings
        if cfg.field_mappings and cfg.data_type in cfg.field_mappings:
            mappings = cfg.field_mappings[cfg.data_type]
            for field_key, column_name in mappings.items():
                if field_key in self.mapping_inputs:
                    self.mapping_inputs[field_key].setCurrentText(column_name)
    
    def save_config(self):
        """ذخیره تنظیمات"""
        data_type = self.data_type_combo.currentText()
        
        # ساخت field mappings
        field_mappings = {
            data_type: {}
        }
        
        for field_key, input_widget in self.mapping_inputs.items():
            column_name = input_widget.currentText().strip()
            if column_name:
                field_mappings[data_type][field_key] = column_name
        
        # اعتبارسنجی فیلدهای ضروری
        required_fields = {
            'sale': ['label', 'customer', 'rate', 'price'],
            'purchase': ['label', 'supplier', 'purchase_price'],
            'payment': ['customer', 'amount']
        }
        
        if data_type in required_fields:
            missing = []
            for field in required_fields[data_type]:
                if not field_mappings[data_type].get(field):
                    missing.append(field)
            
            if missing:
                QMessageBox.warning(
                    self,
                    "Missing Required Fields",
                    f"Please map these required fields:\n{', '.join(missing)}"
                )
                return
        
        # ساخت/بروزرسانی config
        db = FinancialSessionLocal()
        try:
            if self.financial_config:
                config = self.financial_config
            else:
                config = SheetFinancialConfig(
                    sheet_config_id=self.sheet_config.id,
                    sheet_name=self.sheet_config.name
                )
                db.add(config)
            
            config.data_type = data_type
            config.field_mappings = field_mappings
            config.is_active = self.active_checkbox.isChecked()
            
            dept_text = self.department_combo.currentText()
            config.department_code = None if dept_text == "Auto-detect" else dept_text
            
            product = self.product_input.text().strip()
            config.product_type = product if product else None
            
            config.notes = self.notes_text.toPlainText().strip() or None
            
            db.commit()
            
            QMessageBox.information(self, "Success", "Configuration saved successfully!")
            self.accept()
            
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Error", f"Failed to save: {str(e)}")
        finally:
            db.close()


class SheetFinancialConfigManager(QWidget):
    """
    مدیریت تنظیمات مالی sheets
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = app_logger
        self.init_ui()
        self.load_sheets()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # عنوان
        title = QLabel("Sheet Financial Configuration")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #2196F3; padding: 10px;")
        layout.addWidget(title)
        
        desc = QLabel("Configure how each Google Sheet should be imported into the financial system.")
        desc.setStyleSheet("color: #666; padding: 5px 10px;")
        layout.addWidget(desc)
        
        # دکمه‌ها
        btn_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_sheets)
        btn_layout.addWidget(refresh_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # جدول sheets
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Sheet Name", "Type", "Status", "Records", "Converted", "Last Update", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
    
    def load_sheets(self):
        """بارگذاری sheets"""
        phase1_db = SessionLocal()
        financial_db = FinancialSessionLocal()
        
        try:
            sheets = phase1_db.query(SheetConfig).filter(SheetConfig.is_active == True).all()
            
            self.table.setRowCount(len(sheets))
            
            for row, sheet in enumerate(sheets):
                # نام
                self.table.setItem(row, 0, QTableWidgetItem(sheet.name))
                
                # چک کردن config مالی
                financial_config = financial_db.query(SheetFinancialConfig).filter(
                    SheetFinancialConfig.sheet_config_id == sheet.id
                ).first()
                
                # نوع
                if financial_config:
                    self.table.setItem(row, 1, QTableWidgetItem(financial_config.data_type.upper()))
                    status = "ACTIVE" if financial_config.is_active else "INACTIVE"
                    status_item = QTableWidgetItem(status)
                    if financial_config.is_active:
                        status_item.setForeground(Qt.GlobalColor.darkGreen)
                    self.table.setItem(row, 2, status_item)
                    
                    self.table.setItem(row, 4, QTableWidgetItem(f"{financial_config.total_records_converted:,}"))
                    last_update = str(financial_config.updated_at)[:16] if financial_config.updated_at else "Never"
                    self.table.setItem(row, 5, QTableWidgetItem(last_update))
                else:
                    self.table.setItem(row, 1, QTableWidgetItem("Not Configured"))
                    self.table.setItem(row, 2, QTableWidgetItem("N/A"))
                    self.table.setItem(row, 4, QTableWidgetItem("0"))
                    self.table.setItem(row, 5, QTableWidgetItem("Never"))
                
                # تعداد رکوردها
                from app.models.sales_data import SalesData
                count = phase1_db.query(SalesData).filter(
                    SalesData.sheet_config_id == sheet.id
                ).count()
                self.table.setItem(row, 3, QTableWidgetItem(f"{count:,}"))
                
                # دکمه Configure
                config_btn = QPushButton("Configure" if not financial_config else "Edit")
                config_btn.clicked.connect(lambda checked, s=sheet, fc=financial_config: self.configure_sheet(s, fc))
                self.table.setCellWidget(row, 6, config_btn)
        
        finally:
            phase1_db.close()
            financial_db.close()
    
    def configure_sheet(self, sheet: SheetConfig, financial_config: SheetFinancialConfig = None):
        """باز کردن دیالوگ تنظیمات"""
        dialog = SheetConfigDialog(sheet, financial_config, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_sheets()


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    window = SheetFinancialConfigManager()
    window.resize(1000, 600)
    window.show()
    sys.exit(app.exec())
