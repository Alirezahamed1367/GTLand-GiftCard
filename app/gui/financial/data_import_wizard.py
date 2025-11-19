"""
Data Import Wizard - ویزارد وارد کردن داده از Phase 1 به Phase 2
=========================================================================
این ماژول به کاربر کمک می‌کند داده‌های استخراج شده از Google Sheets را
به سیستم مالی (Phase 2) منتقل کند
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QMessageBox,
    QGroupBox, QFormLayout, QCheckBox, QProgressBar, QTextEdit,
    QSplitter, QWidget, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QColor

from app.models import SessionLocal, SheetConfig, SalesData
from app.models.financial import (
    TransactionType, Platform, Region, Department,
    Purchase, Sale, AccountInventory, Customer,
    FinancialSessionLocal
)
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional


class DataImportThread(QThread):
    """Thread برای import داده‌ها"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
    
    def run(self):
        try:
            result = self.import_data()
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
    
    def import_data(self) -> dict:
        """واردکردن داده‌ها"""
        phase1_db = SessionLocal()
        phase2_db = FinancialSessionLocal()
        
        stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0
        }
        
        try:
            # دریافت داده‌ها از Phase 1
            sheet_id = self.config["sheet_id"]
            records = phase1_db.query(SalesData).filter_by(
                sheet_config_id=sheet_id
            ).all()
            
            stats["total"] = len(records)
            self.progress.emit(0, f"📊 در حال پردازش {stats['total']} رکورد...")
            
            transaction_type = self.config["transaction_type"]
            column_mapping = self.config["column_mapping"]
            
            for i, record in enumerate(records):
                try:
                    if transaction_type == "purchase":
                        self.import_purchase(phase2_db, record, column_mapping)
                    elif transaction_type == "sale":
                        self.import_sale(phase2_db, record, column_mapping)
                    
                    stats["success"] += 1
                except Exception as e:
                    stats["failed"] += 1
                    print(f"Error importing record {record.id}: {e}")
                
                # بروزرسانی پیشرفت
                progress = int((i + 1) / stats["total"] * 100)
                self.progress.emit(progress, f"پردازش: {i+1}/{stats['total']}")
            
            phase2_db.commit()
            
        finally:
            phase1_db.close()
            phase2_db.close()
        
        return stats
    
    def import_purchase(self, db, record: SalesData, mapping: Dict):
        """وارد کردن خرید"""
        data = record.data or {}
        
        purchase = Purchase(
            transaction_date=self.get_date(data, mapping.get("date")),
            platform_id=self.config.get("platform_id"),
            region_id=self.config.get("region_id"),
            department_id=self.config.get("department_id"),
            item_description=data.get(mapping.get("description", "")),
            quantity=self.get_decimal(data, mapping.get("quantity")),
            unit_price=self.get_decimal(data, mapping.get("unit_price")),
            total_amount=self.get_decimal(data, mapping.get("total_amount")),
            currency="USD",
            notes=f"Imported from Sheet: {record.sheet_config_id}"
        )
        
        db.add(purchase)
    
    def import_sale(self, db, record: SalesData, mapping: Dict):
        """وارد کردن فروش"""
        data = record.data or {}
        
        sale = Sale(
            transaction_date=self.get_date(data, mapping.get("date")),
            platform_id=self.config.get("platform_id"),
            region_id=self.config.get("region_id"),
            department_id=self.config.get("department_id"),
            customer_id=self.config.get("customer_id"),
            item_description=data.get(mapping.get("description", "")),
            quantity=self.get_decimal(data, mapping.get("quantity")),
            unit_price=self.get_decimal(data, mapping.get("unit_price")),
            total_amount=self.get_decimal(data, mapping.get("total_amount")),
            currency="USD",
            notes=f"Imported from Sheet: {record.sheet_config_id}"
        )
        
        db.add(sale)
    
    def get_decimal(self, data: dict, key: Optional[str]) -> Decimal:
        """تبدیل به Decimal"""
        if not key or key not in data:
            return Decimal("0")
        try:
            return Decimal(str(data[key]))
        except:
            return Decimal("0")
    
    def get_date(self, data: dict, key: Optional[str]) -> datetime:
        """تبدیل به تاریخ"""
        if not key or key not in data:
            return datetime.now()
        try:
            return datetime.fromisoformat(data[key])
        except:
            return datetime.now()


class DataImportWizard(QDialog):
    """
    ویزارد وارد کردن داده از Phase 1 به Phase 2
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔄 ورود داده از شیت‌ها به سیستم مالی")
        self.setMinimumSize(1000, 700)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        self.phase1_db = SessionLocal()
        self.phase2_db = FinancialSessionLocal()
        
        self.selected_sheet = None
        self.column_mapping = {}
        
        self.setup_ui()
        self.load_sheets()
    
    def setup_ui(self):
        """ایجاد رابط کاربری"""
        layout = QVBoxLayout(self)
        
        # عنوان
        title = QLabel("📊 انتقال داده از شیت‌های استخراج شده به سیستم مالی")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2196F3; padding: 10px; background: #E3F2FD; border-radius: 5px;")
        layout.addWidget(title)
        
        # مرحله 1: انتخاب شیت
        sheet_group = self.create_sheet_selection()
        layout.addWidget(sheet_group)
        
        # مرحله 2: تنظیمات import
        settings_group = self.create_import_settings()
        layout.addWidget(settings_group)
        
        # مرحله 3: نگاشت ستون‌ها
        mapping_group = self.create_column_mapping()
        layout.addWidget(mapping_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # لاگ
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        layout.addWidget(QLabel("📋 لاگ عملیات:"))
        layout.addWidget(self.log_text)
        
        # دکمه‌ها
        buttons = QHBoxLayout()
        
        self.import_btn = QPushButton("🚀 شروع Import")
        self.import_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #45a049;
            }
        """)
        self.import_btn.clicked.connect(self.start_import)
        buttons.addWidget(self.import_btn)
        
        close_btn = QPushButton("بستن")
        close_btn.clicked.connect(self.close)
        buttons.addWidget(close_btn)
        
        layout.addLayout(buttons)
    
    def create_sheet_selection(self) -> QGroupBox:
        """بخش انتخاب شیت"""
        group = QGroupBox("1️⃣ انتخاب شیت")
        layout = QFormLayout()
        
        self.sheet_combo = QComboBox()
        self.sheet_combo.currentIndexChanged.connect(self.on_sheet_changed)
        layout.addRow("شیت:", self.sheet_combo)
        
        self.records_label = QLabel("تعداد رکوردها: 0")
        layout.addRow("", self.records_label)
        
        group.setLayout(layout)
        return group
    
    def create_import_settings(self) -> QGroupBox:
        """بخش تنظیمات import"""
        group = QGroupBox("2️⃣ تنظیمات")
        layout = QFormLayout()
        
        # نوع معامله
        self.transaction_type_combo = QComboBox()
        self.transaction_type_combo.addItems([
            "خرید (Purchase)",
            "فروش (Sale)"
        ])
        layout.addRow("نوع معامله:", self.transaction_type_combo)
        
        # پلتفرم
        self.platform_combo = QComboBox()
        self.load_platforms()
        layout.addRow("پلتفرم:", self.platform_combo)
        
        # ریجن
        self.region_combo = QComboBox()
        self.load_regions()
        layout.addRow("ریجن:", self.region_combo)
        
        # دپارتمان
        self.department_combo = QComboBox()
        self.load_departments()
        layout.addRow("دپارتمان:", self.department_combo)
        
        group.setLayout(layout)
        return group
    
    def create_column_mapping(self) -> QGroupBox:
        """بخش نگاشت ستون‌ها"""
        group = QGroupBox("3️⃣ نگاشت ستون‌ها")
        layout = QVBoxLayout()
        
        info = QLabel("💡 برای هر فیلد، ستون مربوطه از شیت را انتخاب کنید:")
        info.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(info)
        
        # جدول نگاشت
        self.mapping_table = QTableWidget()
        self.mapping_table.setColumnCount(3)
        self.mapping_table.setHorizontalHeaderLabels([
            "فیلد سیستم", "ستون شیت", "پیش‌نمایش نمونه"
        ])
        self.mapping_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.mapping_table)
        
        group.setLayout(layout)
        return group
    
    def load_sheets(self):
        """بارگذاری لیست شیت‌ها"""
        sheets = self.phase1_db.query(SheetConfig).filter_by(is_active=True).all()
        
        self.sheet_combo.clear()
        for sheet in sheets:
            record_count = self.phase1_db.query(SalesData).filter_by(
                sheet_config_id=sheet.id
            ).count()
            self.sheet_combo.addItem(
                f"{sheet.name} ({record_count} رکورد)",
                sheet.id
            )
    
    def load_platforms(self):
        """بارگذاری پلتفرم‌ها"""
        platforms = self.phase2_db.query(Platform).filter_by(is_active=True).all()
        self.platform_combo.clear()
        for p in platforms:
            self.platform_combo.addItem(p.platform_name_fa, p.platform_id)
    
    def load_regions(self):
        """بارگذاری ریجن‌ها"""
        regions = self.phase2_db.query(Region).filter_by(is_active=True).all()
        self.region_combo.clear()
        for r in regions:
            self.region_combo.addItem(r.region_name_fa, r.region_id)
    
    def load_departments(self):
        """بارگذاری دپارتمان‌ها"""
        departments = self.phase2_db.query(Department).filter_by(is_active=True).all()
        self.department_combo.clear()
        for d in departments:
            self.department_combo.addItem(d.department_name_fa, d.department_id)
    
    def on_sheet_changed(self, index):
        """تغییر شیت انتخاب شده"""
        if index < 0:
            return
        
        sheet_id = self.sheet_combo.currentData()
        self.selected_sheet = self.phase1_db.query(SheetConfig).get(sheet_id)
        
        if self.selected_sheet:
            # نمایش تعداد رکوردها
            count = self.phase1_db.query(SalesData).filter_by(
                sheet_config_id=sheet_id
            ).count()
            self.records_label.setText(f"تعداد رکوردها: {count}")
            
            # بارگذاری ستون‌ها برای نگاشت
            self.load_column_mappings()
    
    def load_column_mappings(self):
        """بارگذاری نگاشت ستون‌ها"""
        if not self.selected_sheet:
            return
        
        # فیلدهای مورد نیاز
        required_fields = [
            ("date", "تاریخ معامله"),
            ("description", "شرح کالا"),
            ("quantity", "تعداد"),
            ("unit_price", "قیمت واحد"),
            ("total_amount", "مبلغ کل"),
        ]
        
        # دریافت ستون‌های موجود در شیت
        sample_record = self.phase1_db.query(SalesData).filter_by(
            sheet_config_id=self.selected_sheet.id
        ).first()
        
        available_columns = []
        if sample_record and sample_record.data:
            available_columns = list(sample_record.data.keys())
        
        # پر کردن جدول
        self.mapping_table.setRowCount(len(required_fields))
        
        for row, (field_key, field_name) in enumerate(required_fields):
            # نام فیلد
            self.mapping_table.setItem(row, 0, QTableWidgetItem(field_name))
            
            # ComboBox برای انتخاب ستون
            combo = QComboBox()
            combo.addItem("-- انتخاب کنید --", None)
            for col in available_columns:
                combo.addItem(col, col)
            
            # تلاش برای تشخیص خودکار
            auto_match = self.auto_match_column(field_key, available_columns)
            if auto_match:
                combo.setCurrentText(auto_match)
            
            combo.setProperty("field_key", field_key)
            combo.currentTextChanged.connect(self.update_preview)
            self.mapping_table.setCellWidget(row, 1, combo)
            
            # پیش‌نمایش
            self.mapping_table.setItem(row, 2, QTableWidgetItem(""))
        
        self.update_preview()
    
    def auto_match_column(self, field_key: str, columns: List[str]) -> Optional[str]:
        """تشخیص خودکار ستون مناسب"""
        patterns = {
            "date": ["date", "تاریخ", "زمان"],
            "description": ["desc", "توضیح", "شرح", "item"],
            "quantity": ["qty", "quantity", "تعداد", "count"],
            "unit_price": ["price", "قیمت", "rate", "نرخ"],
            "total_amount": ["total", "amount", "مبلغ", "جمع"]
        }
        
        for col in columns:
            col_lower = col.lower()
            if field_key in patterns:
                for pattern in patterns[field_key]:
                    if pattern in col_lower:
                        return col
        return None
    
    def update_preview(self):
        """بروزرسانی پیش‌نمایش"""
        if not self.selected_sheet:
            return
        
        sample_record = self.phase1_db.query(SalesData).filter_by(
            sheet_config_id=self.selected_sheet.id
        ).first()
        
        if not sample_record or not sample_record.data:
            return
        
        for row in range(self.mapping_table.rowCount()):
            combo = self.mapping_table.cellWidget(row, 1)
            if combo and combo.currentData():
                column_name = combo.currentData()
                value = sample_record.data.get(column_name, "")
                self.mapping_table.setItem(row, 2, QTableWidgetItem(str(value)[:50]))
    
    def start_import(self):
        """شروع import"""
        if not self.selected_sheet:
            QMessageBox.warning(self, "خطا", "⚠️ لطفاً یک شیت انتخاب کنید")
            return
        
        # جمع‌آوری نگاشت ستون‌ها
        column_mapping = {}
        for row in range(self.mapping_table.rowCount()):
            combo = self.mapping_table.cellWidget(row, 1)
            if combo:
                field_key = combo.property("field_key")
                column_name = combo.currentData()
                if column_name:
                    column_mapping[field_key] = column_name
        
        if not column_mapping:
            QMessageBox.warning(self, "خطا", "⚠️ لطفاً حداقل یک ستون را نگاشت دهید")
            return
        
        # آماده‌سازی تنظیمات
        transaction_type = "purchase" if "خرید" in self.transaction_type_combo.currentText() else "sale"
        
        config = {
            "sheet_id": self.selected_sheet.id,
            "transaction_type": transaction_type,
            "platform_id": self.platform_combo.currentData(),
            "region_id": self.region_combo.currentData(),
            "department_id": self.department_combo.currentData(),
            "column_mapping": column_mapping
        }
        
        # شروع thread
        self.log("🚀 شروع import...")
        self.progress_bar.setVisible(True)
        self.import_btn.setEnabled(False)
        
        self.import_thread = DataImportThread(config)
        self.import_thread.progress.connect(self.on_progress)
        self.import_thread.finished.connect(self.on_finished)
        self.import_thread.error.connect(self.on_error)
        self.import_thread.start()
    
    def on_progress(self, value: int, message: str):
        """بروزرسانی پیشرفت"""
        self.progress_bar.setValue(value)
        self.log(message)
    
    def on_finished(self, stats: dict):
        """پایان import"""
        self.progress_bar.setVisible(False)
        self.import_btn.setEnabled(True)
        
        message = f"""
✅ Import با موفقیت انجام شد!

📊 آمار:
  • کل رکوردها: {stats['total']}
  • موفق: {stats['success']}
  • ناموفق: {stats['failed']}
  • رد شده: {stats['skipped']}
"""
        self.log(message)
        QMessageBox.information(self, "موفق", message)
    
    def on_error(self, error: str):
        """خطا در import"""
        self.progress_bar.setVisible(False)
        self.import_btn.setEnabled(False)
        
        self.log(f"❌ خطا: {error}")
        QMessageBox.critical(self, "خطا", f"❌ خطا در import:\n{error}")
    
    def log(self, message: str):
        """نوشتن لاگ"""
        self.log_text.append(message)
    
    def closeEvent(self, event):
        """بستن دیالوگ"""
        self.phase1_db.close()
        self.phase2_db.close()
        event.accept()
