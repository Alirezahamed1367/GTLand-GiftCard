"""
دیالوگ ساخت Formula برای تبدیل داده‌ها
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QLineEdit, QTextEdit,
    QGroupBox, QRadioButton, QButtonGroup, QSpinBox,
    QCheckBox, QMessageBox, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import json


class FormulaBuilderDialog(QDialog):
    """
    دیالوگ ساخت Formula برای تبدیل داده‌ها
    
    قابلیت‌ها:
    - Merge چند ستون
    - Trim/Strip متن
    - تبدیل حروف (بزرگ/کوچک)
    - Replace متن
    - فرمول‌های ریاضی (جمع، ضرب، تقسیم)
    - فرمول‌های تاریخ
    - فرمول‌های شرطی (IF)
    """
    
    def __init__(self, parent=None, current_mapping=None):
        super().__init__(parent)
        self.current_mapping = current_mapping or {}
        self.formula_parts = []
        
        self.setWindowTitle("⚡ Formula Builder")
        self.resize(800, 600)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        self.init_ui()
    
    def init_ui(self):
        """راه‌اندازی رابط کاربری"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # عنوان
        title = QLabel("⚡ ساخت Formula برای تبدیل داده")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #FF9800; padding: 10px;")
        layout.addWidget(title)
        
        # اطلاعات ستون فعلی
        if self.current_mapping:
            info = f"📊 ستون: {self.current_mapping.get('source_column')} از Sheet: {self.current_mapping.get('source_sheet')}"
            info_label = QLabel(info)
            info_label.setStyleSheet("background: #E3F2FD; padding: 8px; border-radius: 5px;")
            layout.addWidget(info_label)
        
        # انواع Formula
        formula_types_group = QGroupBox("🔧 نوع عملیات")
        formula_types_layout = QVBoxLayout(formula_types_group)
        
        self.formula_type_combo = QComboBox()
        self.formula_type_combo.setMinimumHeight(40)
        self.formula_type_combo.addItems([
            "🔗 Merge - ادغام چند ستون",
            "✂️ Trim - حذف فاصله‌های اضافی",
            "🔤 Upper/Lower - تبدیل حروف",
            "🔄 Replace - جایگزینی متن",
            "➕ Math - عملیات ریاضی",
            "📅 Date Format - قالب‌بندی تاریخ",
            "❓ IF Condition - شرط",
            "📏 Substring - برش متن",
            "🔢 Number Format - قالب‌بندی عدد",
            "🗑️ Remove Duplicates - حذف تکراری"
        ])
        self.formula_type_combo.setStyleSheet("""
            QComboBox {
                font-size: 11pt;
                padding: 8px;
                border: 2px solid #FF9800;
                border-radius: 5px;
            }
        """)
        self.formula_type_combo.currentIndexChanged.connect(self.on_type_changed)
        formula_types_layout.addWidget(self.formula_type_combo)
        
        layout.addWidget(formula_types_group)
        
        # پنل تنظیمات (بسته به نوع Formula)
        self.settings_stack = QVBoxLayout()
        layout.addLayout(self.settings_stack)
        
        # پیش‌نمایش Formula
        preview_group = QGroupBox("👁️ پیش‌نمایش Formula")
        preview_layout = QVBoxLayout(preview_group)
        
        self.formula_preview = QTextEdit()
        self.formula_preview.setMaximumHeight(100)
        self.formula_preview.setReadOnly(True)
        self.formula_preview.setStyleSheet("""
            QTextEdit {
                background: #F5F5F5;
                font-family: 'Courier New';
                font-size: 10pt;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        preview_layout.addWidget(self.formula_preview)
        
        layout.addWidget(preview_group)
        
        # دکمه‌ها
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        cancel_btn = QPushButton("❌ انصراف")
        cancel_btn.setMinimumHeight(45)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                font-size: 12pt;
                font-weight: bold;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("✅ ذخیره Formula")
        save_btn.setMinimumHeight(45)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 12pt;
                font-weight: bold;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        save_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(save_btn)
        
        layout.addLayout(buttons_layout)
        
        # بارگذاری اولیه
        self.on_type_changed(0)
    
    def clear_settings_stack(self):
        """پاک کردن پنل تنظیمات"""
        while self.settings_stack.count():
            item = self.settings_stack.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def on_type_changed(self, index):
        """تغییر نوع Formula"""
        self.clear_settings_stack()
        
        if index == 0:  # Merge
            self.create_merge_settings()
        elif index == 1:  # Trim
            self.create_trim_settings()
        elif index == 2:  # Upper/Lower
            self.create_case_settings()
        elif index == 3:  # Replace
            self.create_replace_settings()
        elif index == 4:  # Math
            self.create_math_settings()
        elif index == 5:  # Date Format
            self.create_date_settings()
        elif index == 6:  # IF Condition
            self.create_if_settings()
        elif index == 7:  # Substring
            self.create_substring_settings()
        elif index == 8:  # Number Format
            self.create_number_format_settings()
        elif index == 9:  # Remove Duplicates
            self.create_remove_duplicates_settings()
    
    def create_merge_settings(self):
        """تنظیمات Merge"""
        group = QGroupBox("🔗 ادغام چند ستون")
        layout = QVBoxLayout(group)
        
        label = QLabel("ستون‌هایی که می‌خواهید ادغام کنید (با Enter جدا کنید):")
        layout.addWidget(label)
        
        self.merge_columns = QTextEdit()
        self.merge_columns.setMaximumHeight(80)
        self.merge_columns.setPlaceholderText("مثال:\nکد کالا\nنام کالا\nواحد")
        self.merge_columns.textChanged.connect(self.update_preview)
        layout.addWidget(self.merge_columns)
        
        sep_layout = QHBoxLayout()
        sep_layout.addWidget(QLabel("جداکننده:"))
        self.merge_separator = QLineEdit(" - ")
        self.merge_separator.setMaximumWidth(150)
        self.merge_separator.textChanged.connect(self.update_preview)
        sep_layout.addWidget(self.merge_separator)
        sep_layout.addStretch()
        layout.addLayout(sep_layout)
        
        self.settings_stack.addWidget(group)
        self.update_preview()
    
    def create_trim_settings(self):
        """تنظیمات Trim"""
        group = QGroupBox("✂️ حذف فاصله‌های اضافی")
        layout = QVBoxLayout(group)
        
        self.trim_type = QComboBox()
        self.trim_type.addItems([
            "هر دو طرف (Trim)",
            "سمت راست (RTrim)",
            "سمت چپ (LTrim)",
            "تمام فاصله‌های اضافی (Strip All)"
        ])
        self.trim_type.currentIndexChanged.connect(self.update_preview)
        layout.addWidget(self.trim_type)
        
        self.settings_stack.addWidget(group)
        self.update_preview()
    
    def create_case_settings(self):
        """تنظیمات Upper/Lower"""
        group = QGroupBox("🔤 تبدیل حروف")
        layout = QVBoxLayout(group)
        
        self.case_type = QComboBox()
        self.case_type.addItems([
            "حروف بزرگ (UPPER)",
            "حروف کوچک (lower)",
            "حرف اول بزرگ (Title Case)"
        ])
        self.case_type.currentIndexChanged.connect(self.update_preview)
        layout.addWidget(self.case_type)
        
        self.settings_stack.addWidget(group)
        self.update_preview()
    
    def create_replace_settings(self):
        """تنظیمات Replace"""
        group = QGroupBox("🔄 جایگزینی متن")
        layout = QVBoxLayout(group)
        
        find_layout = QHBoxLayout()
        find_layout.addWidget(QLabel("پیدا کن:"))
        self.replace_find = QLineEdit()
        self.replace_find.textChanged.connect(self.update_preview)
        find_layout.addWidget(self.replace_find)
        layout.addLayout(find_layout)
        
        replace_layout = QHBoxLayout()
        replace_layout.addWidget(QLabel("جایگزین کن با:"))
        self.replace_with = QLineEdit()
        self.replace_with.textChanged.connect(self.update_preview)
        replace_layout.addWidget(self.replace_with)
        layout.addLayout(replace_layout)
        
        self.settings_stack.addWidget(group)
        self.update_preview()
    
    def create_math_settings(self):
        """تنظیمات ریاضی"""
        group = QGroupBox("➕ عملیات ریاضی")
        layout = QVBoxLayout(group)
        
        self.math_operation = QComboBox()
        self.math_operation.addItems([
            "جمع (+)",
            "تفریق (-)",
            "ضرب (×)",
            "تقسیم (÷)",
            "درصد (%)",
            "توان (^)"
        ])
        self.math_operation.currentIndexChanged.connect(self.update_preview)
        layout.addWidget(self.math_operation)
        
        value_layout = QHBoxLayout()
        value_layout.addWidget(QLabel("مقدار:"))
        self.math_value = QLineEdit("0")
        self.math_value.textChanged.connect(self.update_preview)
        value_layout.addWidget(self.math_value)
        layout.addLayout(value_layout)
        
        self.settings_stack.addWidget(group)
        self.update_preview()
    
    def create_date_settings(self):
        """تنظیمات تاریخ"""
        group = QGroupBox("📅 قالب‌بندی تاریخ")
        layout = QVBoxLayout(group)
        
        self.date_format = QComboBox()
        self.date_format.addItems([
            "YYYY/MM/DD",
            "DD/MM/YYYY",
            "YYYY-MM-DD",
            "تاریخ شمسی",
            "فقط سال (YYYY)",
            "فقط ماه (MM)",
            "فقط روز (DD)"
        ])
        self.date_format.currentIndexChanged.connect(self.update_preview)
        layout.addWidget(self.date_format)
        
        self.settings_stack.addWidget(group)
        self.update_preview()
    
    def create_if_settings(self):
        """تنظیمات IF"""
        group = QGroupBox("❓ شرط IF")
        layout = QVBoxLayout(group)
        
        # شرط
        condition_layout = QHBoxLayout()
        self.if_condition = QComboBox()
        self.if_condition.addItems(["برابر با", "بزرگتر از", "کوچکتر از", "شامل", "خالی است"])
        self.if_condition.currentIndexChanged.connect(self.update_preview)
        condition_layout.addWidget(self.if_condition)
        
        self.if_value = QLineEdit()
        self.if_value.setPlaceholderText("مقدار مقایسه")
        self.if_value.textChanged.connect(self.update_preview)
        condition_layout.addWidget(self.if_value)
        layout.addLayout(condition_layout)
        
        # اگر درست بود
        true_layout = QHBoxLayout()
        true_layout.addWidget(QLabel("اگر درست:"))
        self.if_true = QLineEdit()
        self.if_true.textChanged.connect(self.update_preview)
        true_layout.addWidget(self.if_true)
        layout.addLayout(true_layout)
        
        # اگر غلط بود
        false_layout = QHBoxLayout()
        false_layout.addWidget(QLabel("اگر غلط:"))
        self.if_false = QLineEdit()
        self.if_false.textChanged.connect(self.update_preview)
        false_layout.addWidget(self.if_false)
        layout.addLayout(false_layout)
        
        self.settings_stack.addWidget(group)
        self.update_preview()
    
    def create_substring_settings(self):
        """تنظیمات Substring"""
        group = QGroupBox("📏 برش متن")
        layout = QVBoxLayout(group)
        
        start_layout = QHBoxLayout()
        start_layout.addWidget(QLabel("از کاراکتر:"))
        self.substring_start = QSpinBox()
        self.substring_start.setMinimum(0)
        self.substring_start.setValue(0)
        self.substring_start.valueChanged.connect(self.update_preview)
        start_layout.addWidget(self.substring_start)
        start_layout.addStretch()
        layout.addLayout(start_layout)
        
        length_layout = QHBoxLayout()
        length_layout.addWidget(QLabel("تعداد کاراکتر:"))
        self.substring_length = QSpinBox()
        self.substring_length.setMinimum(-1)
        self.substring_length.setValue(-1)
        self.substring_length.setSpecialValueText("تا انتها")
        self.substring_length.valueChanged.connect(self.update_preview)
        length_layout.addWidget(self.substring_length)
        length_layout.addStretch()
        layout.addLayout(length_layout)
        
        self.settings_stack.addWidget(group)
        self.update_preview()
    
    def create_number_format_settings(self):
        """تنظیمات قالب‌بندی عدد"""
        group = QGroupBox("🔢 قالب‌بندی عدد")
        layout = QVBoxLayout(group)
        
        self.number_format_type = QComboBox()
        self.number_format_type.addItems([
            "جدا کننده هزار (1,000)",
            "اعشار ثابت (2 رقم)",
            "درصد (%)",
            "پول (تومان)",
            "علمی (1.5e+3)"
        ])
        self.number_format_type.currentIndexChanged.connect(self.update_preview)
        layout.addWidget(self.number_format_type)
        
        self.settings_stack.addWidget(group)
        self.update_preview()
    
    def create_remove_duplicates_settings(self):
        """تنظیمات حذف تکراری"""
        group = QGroupBox("🗑️ حذف رکوردهای تکراری")
        layout = QVBoxLayout(group)
        
        # توضیحات
        info = QLabel("""
        ⚠️ این عملیات تمام رکوردهای تکراری را حذف می‌کند.
        
        📌 نحوه کار:
        • بر اساس ستون‌های کلیدی که انتخاب می‌کنید، تکراری‌ها شناسایی می‌شوند
        • فقط اولین رکورد از هر مجموعه تکراری نگه داشته می‌شود
        • سایر رکوردهای تکراری به اکسل نهایی منتقل نمی‌شوند
        
        🔑 ستون‌های کلیدی برای شناسایی تکراری:
        """)
        info.setWordWrap(True)
        info.setStyleSheet("""
            background-color: #FFF3E0;
            padding: 10px;
            border-radius: 5px;
            border-left: 4px solid #FF9800;
        """)
        layout.addWidget(info)
        
        # انتخاب ستون‌های کلیدی
        columns_label = QLabel("ستون‌هایی که باید برای شناسایی تکراری بررسی شوند:")
        layout.addWidget(columns_label)
        
        self.duplicate_key_columns = QTextEdit()
        self.duplicate_key_columns.setMaximumHeight(100)
        self.duplicate_key_columns.setPlaceholderText("مثال:\nکد کالا\nتاریخ\nشماره فاکتور\n\n(هر ستون در یک خط)")
        self.duplicate_key_columns.textChanged.connect(self.update_preview)
        layout.addWidget(self.duplicate_key_columns)
        
        # گزینه: حفظ اولین یا آخرین
        keep_layout = QHBoxLayout()
        keep_layout.addWidget(QLabel("کدام رکورد نگه داشته شود:"))
        
        self.keep_first_radio = QRadioButton("اولین رکورد")
        self.keep_first_radio.setChecked(True)
        self.keep_first_radio.toggled.connect(self.update_preview)
        keep_layout.addWidget(self.keep_first_radio)
        
        self.keep_last_radio = QRadioButton("آخرین رکورد")
        self.keep_last_radio.toggled.connect(self.update_preview)
        keep_layout.addWidget(self.keep_last_radio)
        
        keep_layout.addStretch()
        layout.addLayout(keep_layout)
        
        self.settings_stack.addWidget(group)
        self.update_preview()
    
    def update_preview(self):
        """به‌روزرسانی پیش‌نمایش Formula"""
        formula_type = self.formula_type_combo.currentIndex()
        preview = ""
        
        try:
            if formula_type == 0:  # Merge
                cols = self.merge_columns.toPlainText().strip().split('\n')
                sep = self.merge_separator.text()
                preview = f"MERGE({', '.join(cols)}, separator='{sep}')"
            
            elif formula_type == 1:  # Trim
                trim_type = self.trim_type.currentIndex()
                types = ["TRIM", "RTRIM", "LTRIM", "STRIP_ALL"]
                preview = f"{types[trim_type]}(value)"
            
            elif formula_type == 2:  # Upper/Lower
                case_type = self.case_type.currentIndex()
                types = ["UPPER", "LOWER", "TITLE"]
                preview = f"{types[case_type]}(value)"
            
            elif formula_type == 3:  # Replace
                find = self.replace_find.text()
                replace = self.replace_with.text()
                preview = f"REPLACE(value, '{find}', '{replace}')"
            
            elif formula_type == 4:  # Math
                op = self.math_operation.currentIndex()
                ops = ["+", "-", "*", "/", "%", "**"]
                value = self.math_value.text()
                preview = f"value {ops[op]} {value}"
            
            elif formula_type == 5:  # Date
                fmt = self.date_format.currentText()
                preview = f"DATE_FORMAT(value, '{fmt}')"
            
            elif formula_type == 6:  # IF
                condition = self.if_condition.currentText()
                value = self.if_value.text()
                true_val = self.if_true.text()
                false_val = self.if_false.text()
                preview = f"IF(value {condition} '{value}', '{true_val}', '{false_val}')"
            
            elif formula_type == 7:  # Substring
                start = self.substring_start.value()
                length = self.substring_length.value()
                if length == -1:
                    preview = f"SUBSTRING(value, {start})"
                else:
                    preview = f"SUBSTRING(value, {start}, {length})"
            
            elif formula_type == 8:  # Number Format
                fmt_type = self.number_format_type.currentIndex()
                fmts = ["NUMBER_FORMAT", "DECIMAL_2", "PERCENT", "CURRENCY", "SCIENTIFIC"]
                preview = f"{fmts[fmt_type]}(value)"
            
            elif formula_type == 9:  # Remove Duplicates
                key_cols = self.duplicate_key_columns.toPlainText().strip().split('\n')
                key_cols = [col.strip() for col in key_cols if col.strip()]
                keep = "first" if self.keep_first_radio.isChecked() else "last"
                if key_cols:
                    preview = f"REMOVE_DUPLICATES(keys=[{', '.join(key_cols)}], keep='{keep}')"
                else:
                    preview = "REMOVE_DUPLICATES(keys=[همه ستون‌ها], keep='first')"
            
            self.formula_preview.setText(preview)
        
        except Exception as e:
            self.formula_preview.setText(f"خطا: {str(e)}")
    
    def get_formula(self):
        """دریافت Formula ساخته شده"""
        return self.formula_preview.toPlainText()
