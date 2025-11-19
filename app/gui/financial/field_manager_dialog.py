"""
Field Manager Dialog - مدیریت فیلدهای داینامیک سیستم
==================================================================
این ماژول به کاربر اجازه می‌دهد:
1. فیلدهای سفارشی خود را تعریف کند
2. نوع داده و نقش هر فیلد را مشخص کند
3. فیلدها را به ستون‌های شیت متصل کند
4. بر اساس فیلدها، سیستم را پیکربندی کند
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox, QLineEdit,
    QGroupBox, QFormLayout, QMessageBox, QTabWidget,
    QTextEdit, QCheckBox, QSpinBox, QHeaderView, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from app.models.financial import FinancialSessionLocal, CustomField, FieldMapping
from typing import Dict, List, Optional
import json


class FieldDefinitionDialog(QDialog):
    """دیالوگ تعریف یک فیلد جدید"""
    
    def __init__(self, parent=None, field_data=None):
        super().__init__(parent)
        self.field_data = field_data
        self.is_edit = field_data is not None
        
        self.setWindowTitle("تعریف فیلد" if not self.is_edit else "ویرایش فیلد")
        self.setMinimumSize(500, 400)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        self.setup_ui()
        
        if self.is_edit:
            self.load_data()
    
    def setup_ui(self):
        """راه‌اندازی UI"""
        layout = QVBoxLayout(self)
        
        # عنوان
        title = QLabel("📝 مشخصات فیلد")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title.setStyleSheet("color: #2196F3; padding: 10px;")
        layout.addWidget(title)
        
        # فرم
        form = QFormLayout()
        
        # نام فیلد
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("مثال: account_number")
        form.addRow("🔤 نام فیلد (انگلیسی):", self.name_input)
        
        # نام فارسی
        self.label_fa_input = QLineEdit()
        self.label_fa_input.setPlaceholderText("مثال: شماره اکانت")
        form.addRow("🏷️ برچسب فارسی:", self.label_fa_input)
        
        # نوع داده
        self.data_type_combo = QComboBox()
        self.data_type_combo.addItems([
            "text - متن",
            "number - عدد صحیح",
            "decimal - اعشاری",
            "date - تاریخ",
            "datetime - تاریخ و زمان",
            "boolean - بله/خیر",
            "email - ایمیل",
            "phone - تلفن",
            "url - آدرس وب"
        ])
        form.addRow("📊 نوع داده:", self.data_type_combo)
        
        # نقش در سیستم
        self.role_combo = QComboBox()
        self.role_combo.addItems([
            "general - عمومی",
            "identifier - شناسه یکتا",
            "amount - مبلغ/مقدار",
            "price - قیمت",
            "quantity - تعداد",
            "date - تاریخ معامله",
            "customer - مشتری",
            "product - محصول/کالا",
            "description - توضیحات",
            "calculated - محاسبه شده"
        ])
        form.addRow("🎯 نقش:", self.role_combo)
        
        # گروه/دسته‌بندی
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "common - مشترک",
            "purchase - خاص خرید",
            "sale - خاص فروش",
            "silver - مربوط به سیلور",
            "financial - مالی",
            "inventory - موجودی"
        ])
        form.addRow("📂 دسته‌بندی:", self.category_combo)
        
        # الزامی بودن
        self.required_check = QCheckBox("این فیلد الزامی است")
        form.addRow("⚠️ الزامی:", self.required_check)
        
        # منحصر به فرد
        self.unique_check = QCheckBox("مقادیر این فیلد باید یکتا باشند")
        form.addRow("🔑 یکتا:", self.unique_check)
        
        # ترتیب نمایش
        self.order_spin = QSpinBox()
        self.order_spin.setRange(1, 1000)
        self.order_spin.setValue(100)
        form.addRow("🔢 ترتیب نمایش:", self.order_spin)
        
        # مقدار پیش‌فرض
        self.default_input = QLineEdit()
        self.default_input.setPlaceholderText("اختیاری")
        form.addRow("📝 مقدار پیش‌فرض:", self.default_input)
        
        # فرمول (برای فیلدهای محاسبه شده)
        self.formula_input = QTextEdit()
        self.formula_input.setMaximumHeight(80)
        self.formula_input.setPlaceholderText("مثال: {unit_price} * {quantity}")
        form.addRow("🧮 فرمول محاسبه:", self.formula_input)
        
        # توضیحات
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(60)
        form.addRow("📄 توضیحات:", self.description_input)
        
        layout.addLayout(form)
        
        # دکمه‌ها
        buttons = QHBoxLayout()
        
        save_btn = QPushButton("💾 ذخیره")
        save_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #45a049;
            }
        """)
        save_btn.clicked.connect(self.accept)
        buttons.addWidget(save_btn)
        
        cancel_btn = QPushButton("❌ انصراف")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)
        
        layout.addLayout(buttons)
    
    def load_data(self):
        """بارگذاری داده موجود"""
        if not self.field_data:
            return
        
        self.name_input.setText(self.field_data.get("name", ""))
        self.label_fa_input.setText(self.field_data.get("label_fa", ""))
        self.data_type_combo.setCurrentText(self.field_data.get("data_type", "text"))
        self.role_combo.setCurrentText(self.field_data.get("role", "general"))
        self.category_combo.setCurrentText(self.field_data.get("category", "common"))
        self.required_check.setChecked(self.field_data.get("is_required", False))
        self.unique_check.setChecked(self.field_data.get("is_unique", False))
        self.order_spin.setValue(self.field_data.get("display_order", 100))
        self.default_input.setText(self.field_data.get("default_value", ""))
        self.formula_input.setText(self.field_data.get("formula", ""))
        self.description_input.setText(self.field_data.get("description", ""))
    
    def get_data(self) -> Dict:
        """دریافت داده فیلد"""
        # استخراج نوع داده (قبل از -)
        data_type = self.data_type_combo.currentText().split(" - ")[0]
        role = self.role_combo.currentText().split(" - ")[0]
        category = self.category_combo.currentText().split(" - ")[0]
        
        return {
            "name": self.name_input.text().strip(),
            "label_fa": self.label_fa_input.text().strip(),
            "data_type": data_type,
            "role": role,
            "category": category,
            "is_required": self.required_check.isChecked(),
            "is_unique": self.unique_check.isChecked(),
            "display_order": self.order_spin.value(),
            "default_value": self.default_input.text().strip(),
            "formula": self.formula_input.toPlainText().strip(),
            "description": self.description_input.toPlainText().strip()
        }


class FieldManagerDialog(QDialog):
    """
    مدیر فیلدهای داینامیک
    """
    fields_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ مدیریت فیلدهای سیستم")
        self.setMinimumSize(1200, 700)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        self.db = FinancialSessionLocal()
        self.fields = []
        
        self.setup_ui()
        self.load_fields()
    
    def setup_ui(self):
        """راه‌اندازی UI"""
        layout = QVBoxLayout(self)
        
        # عنوان
        header = QLabel("⚙️ مدیریت فیلدهای داینامیک سیستم")
        header.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #2196F3, stop:1 #42A5F5);
            color: white;
            padding: 15px;
            border-radius: 8px;
        """)
        layout.addWidget(header)
        
        # توضیحات
        desc = QLabel("""
📝 در این بخش می‌توانید فیلدهای سفارشی خود را تعریف کنید.
برای هر نوع عملیات (خرید، فروش، سیلور) فیلدهای مخصوص خود را ایجاد کنید.
        """)
        desc.setStyleSheet("background: #E3F2FD; padding: 10px; border-radius: 5px; color: #1976D2;")
        layout.addWidget(desc)
        
        # تب‌ها
        tabs = QTabWidget()
        
        # تب فیلدها
        fields_tab = self.create_fields_tab()
        tabs.addTab(fields_tab, "📋 فیلدها")
        
        # تب پیش‌تنظیم‌ها
        presets_tab = self.create_presets_tab()
        tabs.addTab(presets_tab, "🎨 قالب‌های آماده")
        
        layout.addWidget(tabs)
        
        # دکمه‌ها
        buttons = QHBoxLayout()
        
        close_btn = QPushButton("بستن")
        close_btn.clicked.connect(self.accept)
        buttons.addWidget(close_btn)
        
        layout.addLayout(buttons)
    
    def create_fields_tab(self) -> QWidget:
        """تب فیلدها"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # دکمه‌های عملیات
        actions = QHBoxLayout()
        
        add_btn = QPushButton("➕ افزودن فیلد")
        add_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #45a049;
            }
        """)
        add_btn.clicked.connect(self.add_field)
        actions.addWidget(add_btn)
        
        edit_btn = QPushButton("✏️ ویرایش")
        edit_btn.clicked.connect(self.edit_field)
        actions.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️ حذف")
        delete_btn.setStyleSheet("""
            QPushButton {
                background: #F44336;
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background: #da190b;
            }
        """)
        delete_btn.clicked.connect(self.delete_field)
        actions.addWidget(delete_btn)
        
        actions.addStretch()
        
        refresh_btn = QPushButton("🔄 بروزرسانی")
        refresh_btn.clicked.connect(self.load_fields)
        actions.addWidget(refresh_btn)
        
        layout.addLayout(actions)
        
        # جدول فیلدها
        self.fields_table = QTableWidget()
        self.fields_table.setColumnCount(8)
        self.fields_table.setHorizontalHeaderLabels([
            "نام فیلد", "برچسب", "نوع داده", "نقش", "دسته", "الزامی", "ترتیب", "توضیحات"
        ])
        self.fields_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.fields_table.setAlternatingRowColors(True)
        layout.addWidget(self.fields_table)
        
        return widget
    
    def create_presets_tab(self) -> QWidget:
        """تب قالب‌های آماده"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        info = QLabel("🎨 با انتخاب یک قالب آماده، فیلدهای استاندارد به سیستم اضافه می‌شوند")
        info.setStyleSheet("background: #FFF3E0; padding: 10px; border-radius: 5px; color: #E65100;")
        layout.addWidget(info)
        
        # دکمه‌های قالب
        preset_buttons = QVBoxLayout()
        
        # قالب خرید اکانت
        purchase_btn = QPushButton("📦 قالب خرید اکانت (Account Number, Balance, Silver, Price...)")
        purchase_btn.setMinimumHeight(50)
        purchase_btn.setStyleSheet("text-align: left; padding: 10px;")
        purchase_btn.clicked.connect(lambda: self.apply_preset("purchase"))
        preset_buttons.addWidget(purchase_btn)
        
        # قالب فروش
        sale_btn = QPushButton("💰 قالب فروش (Customer, Used Amount, Sale Price, Profit...)")
        sale_btn.setMinimumHeight(50)
        sale_btn.setStyleSheet("text-align: left; padding: 10px;")
        sale_btn.clicked.connect(lambda: self.apply_preset("sale"))
        preset_buttons.addWidget(sale_btn)
        
        # قالب سیلور
        silver_btn = QPushButton("✨ قالب بونوس سیلور (Silver Amount, Initial, Used, Remaining...)")
        silver_btn.setMinimumHeight(50)
        silver_btn.setStyleSheet("text-align: left; padding: 10px;")
        silver_btn.clicked.connect(lambda: self.apply_preset("silver"))
        preset_buttons.addWidget(silver_btn)
        
        # قالب کامل
        full_btn = QPushButton("🚀 قالب کامل (همه فیلدهای بالا)")
        full_btn.setMinimumHeight(50)
        full_btn.setStyleSheet("""
            QPushButton {
                background: #2196F3;
                color: white;
                font-weight: bold;
                text-align: left;
                padding: 10px;
            }
        """)
        full_btn.clicked.connect(lambda: self.apply_preset("full"))
        preset_buttons.addWidget(full_btn)
        
        preset_buttons.addStretch()
        
        layout.addLayout(preset_buttons)
        
        return widget
    
    def load_fields(self):
        """بارگذاری فیلدها از دیتابیس"""
        # TODO: دریافت از دیتابیس
        # فعلاً از لیست داخلی استفاده می‌کنیم
        self.fields_table.setRowCount(len(self.fields))
        
        for row, field in enumerate(self.fields):
            self.fields_table.setItem(row, 0, QTableWidgetItem(field.get("name", "")))
            self.fields_table.setItem(row, 1, QTableWidgetItem(field.get("label_fa", "")))
            self.fields_table.setItem(row, 2, QTableWidgetItem(field.get("data_type", "")))
            self.fields_table.setItem(row, 3, QTableWidgetItem(field.get("role", "")))
            self.fields_table.setItem(row, 4, QTableWidgetItem(field.get("category", "")))
            
            required = "✅" if field.get("is_required") else "❌"
            self.fields_table.setItem(row, 5, QTableWidgetItem(required))
            
            self.fields_table.setItem(row, 6, QTableWidgetItem(str(field.get("display_order", 0))))
            self.fields_table.setItem(row, 7, QTableWidgetItem(field.get("description", "")))
    
    def add_field(self):
        """افزودن فیلد جدید"""
        dialog = FieldDefinitionDialog(self)
        if dialog.exec():
            field_data = dialog.get_data()
            
            # اعتبارسنجی
            if not field_data.get("name"):
                QMessageBox.warning(self, "خطا", "نام فیلد الزامی است!")
                return
            
            # افزودن به لیست
            self.fields.append(field_data)
            self.load_fields()
            self.fields_changed.emit()
            
            QMessageBox.information(self, "موفق", "✅ فیلد با موفقیت اضافه شد")
    
    def edit_field(self):
        """ویرایش فیلد"""
        current_row = self.fields_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "هشدار", "لطفاً یک فیلد را انتخاب کنید")
            return
        
        field_data = self.fields[current_row]
        dialog = FieldDefinitionDialog(self, field_data)
        if dialog.exec():
            updated_data = dialog.get_data()
            self.fields[current_row] = updated_data
            self.load_fields()
            self.fields_changed.emit()
    
    def delete_field(self):
        """حذف فیلد"""
        current_row = self.fields_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "هشدار", "لطفاً یک فیلد را انتخاب کنید")
            return
        
        reply = QMessageBox.question(
            self,
            "تأیید حذف",
            "آیا از حذف این فیلد اطمینان دارید؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            del self.fields[current_row]
            self.load_fields()
            self.fields_changed.emit()
    
    def apply_preset(self, preset_type: str):
        """اعمال قالب آماده"""
        presets = {
            "purchase": self.get_purchase_preset(),
            "sale": self.get_sale_preset(),
            "silver": self.get_silver_preset(),
            "full": self.get_full_preset()
        }
        
        preset_fields = presets.get(preset_type, [])
        
        reply = QMessageBox.question(
            self,
            "تأیید",
            f"آیا می‌خواهید {len(preset_fields)} فیلد قالب را اضافه کنید؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.fields.extend(preset_fields)
            self.load_fields()
            self.fields_changed.emit()
            QMessageBox.information(self, "موفق", f"✅ {len(preset_fields)} فیلد اضافه شد")
    
    def get_purchase_preset(self) -> List[Dict]:
        """قالب خرید"""
        return [
            {"name": "account_number", "label_fa": "شماره اکانت", "data_type": "text", "role": "identifier", "category": "purchase", "is_required": True, "is_unique": True, "display_order": 1, "default_value": "", "formula": "", "description": "شماره یکتای اکانت"},
            {"name": "initial_balance", "label_fa": "موجودی اولیه", "data_type": "decimal", "role": "amount", "category": "purchase", "is_required": True, "is_unique": False, "display_order": 2, "default_value": "0", "formula": "", "description": "موجودی اصلی اکانت"},
            {"name": "silver_bonus", "label_fa": "بونوس سیلور", "data_type": "decimal", "role": "amount", "category": "silver", "is_required": False, "is_unique": False, "display_order": 3, "default_value": "0", "formula": "", "description": "مقدار سیلور اضافی"},
            {"name": "purchase_price", "label_fa": "قیمت خرید", "data_type": "decimal", "role": "price", "category": "purchase", "is_required": True, "is_unique": False, "display_order": 4, "default_value": "0", "formula": "", "description": "قیمت خرید اکانت"},
            {"name": "purchase_date", "label_fa": "تاریخ خرید", "data_type": "date", "role": "date", "category": "purchase", "is_required": True, "is_unique": False, "display_order": 5, "default_value": "", "formula": "", "description": "تاریخ خرید"},
            {"name": "vendor", "label_fa": "فروشنده", "data_type": "text", "role": "general", "category": "purchase", "is_required": False, "is_unique": False, "display_order": 6, "default_value": "", "formula": "", "description": "نام فروشنده"},
        ]
    
    def get_sale_preset(self) -> List[Dict]:
        """قالب فروش"""
        return [
            {"name": "customer_name", "label_fa": "نام مشتری", "data_type": "text", "role": "customer", "category": "sale", "is_required": True, "is_unique": False, "display_order": 10, "default_value": "", "formula": "", "description": "نام خریدار"},
            {"name": "used_amount", "label_fa": "مقدار مصرفی", "data_type": "decimal", "role": "quantity", "category": "sale", "is_required": True, "is_unique": False, "display_order": 11, "default_value": "0", "formula": "", "description": "مقدار استفاده شده از اکانت"},
            {"name": "sale_price", "label_fa": "قیمت فروش", "data_type": "decimal", "role": "price", "category": "sale", "is_required": True, "is_unique": False, "display_order": 12, "default_value": "0", "formula": "", "description": "قیمت فروش"},
            {"name": "sale_date", "label_fa": "تاریخ فروش", "data_type": "date", "role": "date", "category": "sale", "is_required": True, "is_unique": False, "display_order": 13, "default_value": "", "formula": "", "description": "تاریخ فروش"},
            {"name": "profit", "label_fa": "سود", "data_type": "decimal", "role": "calculated", "category": "financial", "is_required": False, "is_unique": False, "display_order": 14, "default_value": "0", "formula": "{sale_price} - ({purchase_price} * {used_amount} / {initial_balance})", "description": "سود محاسبه شده"},
        ]
    
    def get_silver_preset(self) -> List[Dict]:
        """قالب سیلور"""
        return [
            {"name": "silver_initial", "label_fa": "سیلور اولیه", "data_type": "decimal", "role": "amount", "category": "silver", "is_required": False, "is_unique": False, "display_order": 20, "default_value": "0", "formula": "", "description": "مقدار سیلور در ابتدا"},
            {"name": "silver_used", "label_fa": "سیلور مصرفی", "data_type": "decimal", "role": "quantity", "category": "silver", "is_required": False, "is_unique": False, "display_order": 21, "default_value": "0", "formula": "", "description": "مقدار سیلور مصرف شده"},
            {"name": "silver_remaining", "label_fa": "سیلور باقیمانده", "data_type": "decimal", "role": "calculated", "category": "silver", "is_required": False, "is_unique": False, "display_order": 22, "default_value": "0", "formula": "{silver_initial} - {silver_used}", "description": "سیلور باقی‌مانده"},
        ]
    
    def get_full_preset(self) -> List[Dict]:
        """قالب کامل"""
        return self.get_purchase_preset() + self.get_sale_preset() + self.get_silver_preset()
    
    def get_all_fields(self) -> List[Dict]:
        """دریافت تمام فیلدها"""
        return self.fields
    
    def closeEvent(self, event):
        """بستن دیالوگ"""
        self.db.close()
        event.accept()
