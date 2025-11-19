"""
Dynamic Data Import Wizard - ویزارد وارد کردن داده بر اساس فیلدهای کاربر
==================================================================
این ویزارد:
1. از کاربر می‌خواهد نوع تراکنش را انتخاب کند
2. فیلدهای مربوط به آن تراکنش را نمایش می‌دهد
3. کاربر ستون‌های شیت را به فیلدها map می‌کند
4. داده‌ها را وارد می‌کند
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox, QLineEdit,
    QGroupBox, QFormLayout, QMessageBox, QWizard, QWizardPage,
    QTextEdit, QCheckBox, QProgressBar, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont

from app.models.financial import (
    FinancialSessionLocal,
    CustomField,
    FieldMapping,
    TransactionSchema,
    AccountInventory,
    Purchase,
    Sale,
    Platform,
    Region,
    Department
)
from app.models import SalesData, SheetConfig, SessionLocal
from app.core.logger import logger

from typing import Dict, List, Optional, Any
import traceback
from datetime import datetime


class DynamicImportThread(QThread):
    """
    Thread برای import داده بر اساس فیلدهای داینامیک
    """
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, config: Dict):
        super().__init__()
        self.config = config
        
    def run(self):
        """اجرای import"""
        try:
            self.status.emit("🔄 شروع import...")
            
            # اتصال به دیتابیس
            phase1_db = SessionLocal()
            phase2_db = FinancialSessionLocal()
            
            # دریافت تنظیمات
            sheet_config_id = self.config.get("sheet_config_id")
            transaction_type = self.config.get("transaction_type")
            field_mappings = self.config.get("field_mappings", {})  # {field_name: column_name}
            platform_id = self.config.get("platform_id")
            region_id = self.config.get("region_id")
            department_id = self.config.get("department_id")
            
            # دریافت داده‌های Phase 1
            self.status.emit("📥 دریافت داده از شیت...")
            sheet_config = phase1_db.query(SheetConfig).filter_by(id=sheet_config_id).first()
            
            if not sheet_config:
                raise Exception("شیت یافت نشد!")
            
            sales_data = phase1_db.query(SalesData).filter_by(
                sheet_config_id=sheet_config_id
            ).all()
            
            total = len(sales_data)
            self.status.emit(f"📊 تعداد رکورد: {total}")
            
            if total == 0:
                raise Exception("داده‌ای برای import وجود ندارد!")
            
            # دریافت schema
            schema = phase2_db.query(TransactionSchema).filter_by(
                transaction_type=transaction_type,
                is_active=True
            ).first()
            
            if not schema:
                raise Exception(f"Schema برای {transaction_type} یافت نشد!")
            
            # دریافت فیلدهای مربوطه
            fields = schema.get_fields(phase2_db)
            
            # Import بر اساس نوع
            if transaction_type == "purchase":
                success = self.import_purchase_dynamic(
                    phase2_db, sales_data, fields, field_mappings,
                    platform_id, region_id, department_id
                )
            elif transaction_type == "sale":
                success = self.import_sale_dynamic(
                    phase2_db, sales_data, fields, field_mappings,
                    platform_id, region_id, department_id
                )
            else:
                raise Exception(f"نوع تراکنش {transaction_type} پشتیبانی نمی‌شود!")
            
            if success:
                phase2_db.commit()
                self.status.emit("✅ Import با موفقیت انجام شد")
                self.finished_signal.emit(True, "موفق")
            else:
                phase2_db.rollback()
                self.finished_signal.emit(False, "خطا در import")
            
            phase1_db.close()
            phase2_db.close()
            
        except Exception as e:
            error_msg = f"خطا: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            self.status.emit(f"❌ {str(e)}")
            self.finished_signal.emit(False, error_msg)
    
    def import_purchase_dynamic(self, db, sales_data, fields, mappings, platform_id, region_id, department_id):
        """
        Import خرید بر اساس فیلدهای داینامیک
        """
        total = len(sales_data)
        
        for idx, row in enumerate(sales_data):
            try:
                # ساخت دیکشنری داده
                data_dict = {}
                
                # پر کردن فیلدها بر اساس mapping
                for field in fields:
                    field_name = field.name
                    column_name = mappings.get(field_name)
                    
                    if column_name and hasattr(row, 'data_json') and row.data_json:
                        # دریافت مقدار از data_json
                        value = row.data_json.get(column_name)
                        
                        # تبدیل نوع
                        value = self.convert_value(value, field.data_type)
                        
                        data_dict[field_name] = value
                
                # ایجاد Purchase
                purchase = Purchase()
                
                # تنظیم فیلدهای استاندارد
                purchase.platform_id = platform_id
                purchase.region_id = region_id
                purchase.department_id = department_id
                
                # تنظیم فیلدهای داینامیک
                for field_name, value in data_dict.items():
                    if hasattr(purchase, field_name):
                        setattr(purchase, field_name, value)
                
                db.add(purchase)
                
                # Progress
                progress_pct = int((idx + 1) / total * 100)
                self.progress.emit(progress_pct)
                self.status.emit(f"⏳ در حال import: {idx + 1}/{total}")
                
            except Exception as e:
                logger.error(f"خطا در رکورد {idx}: {str(e)}")
                continue
        
        return True
    
    def import_sale_dynamic(self, db, sales_data, fields, mappings, platform_id, region_id, department_id):
        """
        Import فروش بر اساس فیلدهای داینامیک
        """
        total = len(sales_data)
        
        for idx, row in enumerate(sales_data):
            try:
                data_dict = {}
                
                for field in fields:
                    field_name = field.name
                    column_name = mappings.get(field_name)
                    
                    if column_name and hasattr(row, 'data_json') and row.data_json:
                        value = row.data_json.get(column_name)
                        value = self.convert_value(value, field.data_type)
                        data_dict[field_name] = value
                
                # ایجاد Sale
                sale = Sale()
                sale.platform_id = platform_id
                sale.region_id = region_id
                sale.department_id = department_id
                
                for field_name, value in data_dict.items():
                    if hasattr(sale, field_name):
                        setattr(sale, field_name, value)
                
                db.add(sale)
                
                progress_pct = int((idx + 1) / total * 100)
                self.progress.emit(progress_pct)
                self.status.emit(f"⏳ در حال import: {idx + 1}/{total}")
                
            except Exception as e:
                logger.error(f"خطا در رکورد {idx}: {str(e)}")
                continue
        
        return True
    
    def convert_value(self, value, data_type: str):
        """تبدیل نوع داده"""
        if value is None or value == "":
            return None
        
        try:
            if data_type == "number":
                return int(value)
            elif data_type == "decimal":
                # حذف کاما
                if isinstance(value, str):
                    value = value.replace(",", "")
                return float(value)
            elif data_type == "boolean":
                return value in [True, "true", "True", "1", 1, "بله", "yes"]
            elif data_type == "date":
                # تبدیل به تاریخ
                if isinstance(value, str):
                    return datetime.strptime(value, "%Y-%m-%d").date()
                return value
            elif data_type == "datetime":
                if isinstance(value, str):
                    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                return value
            else:
                return str(value)
        except:
            return None


class DynamicImportWizard(QDialog):
    """
    ویزارد import داینامیک
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔄 Import داده (سیستم داینامیک)")
        self.setMinimumSize(900, 700)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        self.db = FinancialSessionLocal()
        self.phase1_db = SessionLocal()
        
        self.selected_schema = None
        self.selected_fields = []
        self.column_mappings = {}
        
        self.setup_ui()
        self.load_initial_data()
    
    def setup_ui(self):
        """راه‌اندازی UI"""
        layout = QVBoxLayout(self)
        
        # عنوان
        title = QLabel("🔄 ورود داده بر اساس فیلدهای تعریف شده")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #673AB7, stop:1 #9C27B0);
            color: white;
            padding: 15px;
            border-radius: 8px;
        """)
        layout.addWidget(title)
        
        # مرحله 1: انتخاب شیت و نوع تراکنش
        step1 = self.create_step1()
        layout.addWidget(step1)
        
        # مرحله 2: نگاشت ستون‌ها
        step2 = self.create_step2()
        layout.addWidget(step2)
        
        # مرحله 3: Progress
        step3 = self.create_step3()
        layout.addWidget(step3)
        
        # دکمه‌ها
        buttons = QHBoxLayout()
        
        self.start_btn = QPushButton("▶️ شروع Import")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #45a049;
            }
        """)
        self.start_btn.clicked.connect(self.start_import)
        buttons.addWidget(self.start_btn)
        
        close_btn = QPushButton("بستن")
        close_btn.clicked.connect(self.accept)
        buttons.addWidget(close_btn)
        
        layout.addLayout(buttons)
    
    def create_step1(self) -> QGroupBox:
        """مرحله 1: انتخاب"""
        group = QGroupBox("1️⃣ انتخاب شیت و نوع تراکنش")
        group.setStyleSheet("QGroupBox { font-weight: bold; }")
        layout = QFormLayout(group)
        
        # انتخاب شیت
        self.sheet_combo = QComboBox()
        layout.addRow("📊 شیت:", self.sheet_combo)
        
        # نوع تراکنش
        self.transaction_combo = QComboBox()
        self.transaction_combo.currentIndexChanged.connect(self.on_transaction_changed)
        layout.addRow("🔖 نوع تراکنش:", self.transaction_combo)
        
        # Platform
        self.platform_combo = QComboBox()
        layout.addRow("🌐 Platform:", self.platform_combo)
        
        # Region
        self.region_combo = QComboBox()
        layout.addRow("📍 Region:", self.region_combo)
        
        # Department
        self.department_combo = QComboBox()
        layout.addRow("🏢 Department:", self.department_combo)
        
        return group
    
    def create_step2(self) -> QGroupBox:
        """مرحله 2: نگاشت ستون‌ها"""
        group = QGroupBox("2️⃣ نگاشت ستون‌های شیت به فیلدها")
        group.setStyleSheet("QGroupBox { font-weight: bold; }")
        layout = QVBoxLayout(group)
        
        info = QLabel("📌 برای هر فیلد، ستون مربوطه در شیت را انتخاب کنید:")
        info.setStyleSheet("color: #FF5722; padding: 5px;")
        layout.addWidget(info)
        
        # جدول نگاشت
        self.mapping_table = QTableWidget()
        self.mapping_table.setColumnCount(5)
        self.mapping_table.setHorizontalHeaderLabels([
            "فیلد", "برچسب", "نوع داده", "ستون شیت", "پیش‌نمایش"
        ])
        self.mapping_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.mapping_table)
        
        return group
    
    def create_step3(self) -> QGroupBox:
        """مرحله 3: Progress"""
        group = QGroupBox("3️⃣ وضعیت Import")
        layout = QVBoxLayout(group)
        
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        layout.addWidget(self.log_text)
        
        return group
    
    def load_initial_data(self):
        """بارگذاری داده اولیه"""
        # Sheets
        sheets = self.phase1_db.query(SheetConfig).all()
        for sheet in sheets:
            self.sheet_combo.addItem(sheet.sheet_name, sheet.id)
        
        # Transaction types
        schemas = self.db.query(TransactionSchema).filter_by(is_active=True).all()
        for schema in schemas:
            self.transaction_combo.addItem(schema.title_fa, schema.transaction_type)
        
        # Platforms
        platforms = self.db.query(Platform).all()
        for p in platforms:
            self.platform_combo.addItem(p.name, p.id)
        
        # Regions
        regions = self.db.query(Region).all()
        for r in regions:
            self.region_combo.addItem(r.name, r.id)
        
        # Departments
        departments = self.db.query(Department).all()
        for d in departments:
            self.department_combo.addItem(d.name, d.id)
    
    def on_transaction_changed(self):
        """تغییر نوع تراکنش"""
        transaction_type = self.transaction_combo.currentData()
        if not transaction_type:
            return
        
        # دریافت schema
        schema = self.db.query(TransactionSchema).filter_by(
            transaction_type=transaction_type,
            is_active=True
        ).first()
        
        if not schema:
            QMessageBox.warning(self, "هشدار", "Schema یافت نشد!")
            return
        
        self.selected_schema = schema
        self.selected_fields = schema.get_fields(self.db)
        
        # بروزرسانی جدول
        self.load_field_mappings()
    
    def load_field_mappings(self):
        """بارگذاری نگاشت فیلدها"""
        if not self.selected_fields:
            self.mapping_table.setRowCount(0)
            return
        
        # دریافت ستون‌های شیت
        sheet_id = self.sheet_combo.currentData()
        if not sheet_id:
            return
        
        sheet_config = self.phase1_db.query(SheetConfig).filter_by(id=sheet_id).first()
        if not sheet_config:
            return
        
        # فرض: ستون‌ها در data_json اولین رکورد موجود است
        sample_data = self.phase1_db.query(SalesData).filter_by(
            sheet_config_id=sheet_id
        ).first()
        
        available_columns = []
        if sample_data and hasattr(sample_data, 'data_json') and sample_data.data_json:
            available_columns = list(sample_data.data_json.keys())
        
        # پر کردن جدول
        self.mapping_table.setRowCount(len(self.selected_fields))
        
        for row, field in enumerate(self.selected_fields):
            # نام فیلد
            self.mapping_table.setItem(row, 0, QTableWidgetItem(field.name))
            
            # برچسب
            self.mapping_table.setItem(row, 1, QTableWidgetItem(field.label_fa))
            
            # نوع داده
            self.mapping_table.setItem(row, 2, QTableWidgetItem(field.data_type))
            
            # ComboBox برای انتخاب ستون
            column_combo = QComboBox()
            column_combo.addItem("-- انتخاب کنید --", None)
            for col in available_columns:
                column_combo.addItem(col, col)
            
            # Auto-match
            matched_col = self.auto_match_column(field.name, field.label_fa, available_columns)
            if matched_col:
                index = column_combo.findData(matched_col)
                if index >= 0:
                    column_combo.setCurrentIndex(index)
            
            self.mapping_table.setCellWidget(row, 3, column_combo)
            
            # پیش‌نمایش
            preview = ""
            if sample_data and matched_col:
                preview = str(sample_data.data_json.get(matched_col, ""))[:30]
            self.mapping_table.setItem(row, 4, QTableWidgetItem(preview))
    
    def auto_match_column(self, field_name: str, label_fa: str, columns: List[str]) -> Optional[str]:
        """تشخیص خودکار ستون"""
        # الگوهای متداول
        patterns = {
            "account_number": ["account", "اکانت", "شماره", "number"],
            "initial_balance": ["balance", "موجودی", "اولیه", "initial"],
            "purchase_price": ["price", "قیمت", "خرید", "cost"],
            "date": ["date", "تاریخ"],
            "customer": ["customer", "مشتری", "buyer"],
            "quantity": ["quantity", "تعداد", "qty"],
            "amount": ["amount", "مبلغ", "مقدار"],
        }
        
        field_patterns = patterns.get(field_name, [field_name, label_fa])
        
        for col in columns:
            col_lower = col.lower()
            for pattern in field_patterns:
                if pattern.lower() in col_lower:
                    return col
        
        return None
    
    def start_import(self):
        """شروع import"""
        # اعتبارسنجی
        if not self.selected_schema:
            QMessageBox.warning(self, "هشدار", "لطفاً نوع تراکنش را انتخاب کنید")
            return
        
        # جمع‌آوری mappings
        self.column_mappings = {}
        for row in range(self.mapping_table.rowCount()):
            field_name = self.mapping_table.item(row, 0).text()
            column_combo = self.mapping_table.cellWidget(row, 3)
            column_name = column_combo.currentData()
            
            if column_name:
                self.column_mappings[field_name] = column_name
        
        # تنظیمات
        config = {
            "sheet_config_id": self.sheet_combo.currentData(),
            "transaction_type": self.transaction_combo.currentData(),
            "field_mappings": self.column_mappings,
            "platform_id": self.platform_combo.currentData(),
            "region_id": self.region_combo.currentData(),
            "department_id": self.department_combo.currentData(),
        }
        
        # شروع Thread
        self.import_thread = DynamicImportThread(config)
        self.import_thread.progress.connect(self.progress_bar.setValue)
        self.import_thread.status.connect(self.log_text.append)
        self.import_thread.finished_signal.connect(self.on_import_finished)
        
        self.start_btn.setEnabled(False)
        self.import_thread.start()
    
    def on_import_finished(self, success: bool, message: str):
        """پایان import"""
        self.start_btn.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "موفق", "✅ Import با موفقیت انجام شد!")
        else:
            QMessageBox.critical(self, "خطا", f"❌ خطا در import:\n{message}")
    
    def closeEvent(self, event):
        """بستن دیالوگ"""
        self.db.close()
        self.phase1_db.close()
        event.accept()
