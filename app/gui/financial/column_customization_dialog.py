"""
دیالوگ شخصی‌سازی ستون‌ها و فرمول‌ها
=======================================
کاربر می‌تواند:
1. ستون‌های نمایشی را انتخاب کند
2. ترتیب ستون‌ها را تغییر دهد
3. ستون محاسباتی با فرمول تعریف کند
4. تنظیمات را ذخیره کند
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QLineEdit, QTextEdit, QGroupBox, QMessageBox,
    QListWidgetItem, QCheckBox, QComboBox, QSpinBox
)
from PyQt6.QtCore import Qt
from typing import Dict, List
import json


class ColumnCustomizationDialog(QDialog):
    """
    دیالوگ شخصی‌سازی ستون‌ها
    """
    
    # ستون‌های پیش‌فرض موجود
    AVAILABLE_COLUMNS = {
        'label': 'Label (کد آکانت)',
        'email': 'Email',
        'supplier': 'تأمین‌کننده',
        'gold_purchased': 'خرید (Gold)',
        'purchase_rate': 'نرخ خرید',
        'purchase_cost': 'هزینه خرید',
        'total_sold': 'جمع فروش',
        'total_revenue': 'درآمد کل',
        'total_profit': 'سود/زیان',
        'profit_pct': 'درصد سود',
        'remaining_gold': 'موجودی Gold',
        'remaining_silver': 'موجودی Silver'
    }
    
    def __init__(self, current_config: Dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ شخصی‌سازی ستون‌ها و فرمول‌ها")
        self.resize(900, 600)
        
        self.current_config = current_config or self._get_default_config()
        self.custom_formulas = self.current_config.get('custom_formulas', [])
        
        self.init_ui()
        self.load_config()
    
    def _get_default_config(self):
        """تنظیمات پیش‌فرض"""
        return {
            'visible_columns': list(self.AVAILABLE_COLUMNS.keys()),
            'column_order': list(self.AVAILABLE_COLUMNS.keys()),
            'custom_formulas': [],
            'show_platforms': True,
            'platform_columns': ['roblox', 'apple', 'steam']
        }
    
    def init_ui(self):
        """ساخت رابط کاربری"""
        layout = QVBoxLayout(self)
        
        # ═══ بخش 1: انتخاب ستون‌های پایه ═══
        columns_group = QGroupBox("📋 ستون‌های پایه")
        columns_layout = QHBoxLayout()
        
        # لیست ستون‌های موجود
        available_layout = QVBoxLayout()
        available_layout.addWidget(QLabel("ستون‌های موجود:"))
        self.available_list = QListWidget()
        for col_id, col_name in self.AVAILABLE_COLUMNS.items():
            item = QListWidgetItem(col_name)
            item.setData(Qt.ItemDataRole.UserRole, col_id)
            item.setCheckState(Qt.CheckState.Checked)
            self.available_list.addItem(item)
        available_layout.addWidget(self.available_list)
        columns_layout.addLayout(available_layout)
        
        # دکمه‌های مدیریت
        buttons_layout = QVBoxLayout()
        buttons_layout.addStretch()
        
        select_all_btn = QPushButton("✅ انتخاب همه")
        select_all_btn.clicked.connect(self.select_all_columns)
        buttons_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("❌ حذف همه")
        deselect_all_btn.clicked.connect(self.deselect_all_columns)
        buttons_layout.addWidget(deselect_all_btn)
        
        buttons_layout.addStretch()
        
        move_up_btn = QPushButton("⬆️ بالا")
        move_up_btn.clicked.connect(self.move_column_up)
        buttons_layout.addWidget(move_up_btn)
        
        move_down_btn = QPushButton("⬇️ پایین")
        move_down_btn.clicked.connect(self.move_column_down)
        buttons_layout.addWidget(move_down_btn)
        
        buttons_layout.addStretch()
        columns_layout.addLayout(buttons_layout)
        
        columns_group.setLayout(columns_layout)
        layout.addWidget(columns_group)
        
        # ═══ بخش 2: تنظیمات Platform ها ═══
        platform_group = QGroupBox("🎮 ستون‌های Platform")
        platform_layout = QVBoxLayout()
        
        self.show_platforms_check = QCheckBox("نمایش ستون‌های فروش به تفکیک Platform")
        self.show_platforms_check.setChecked(True)
        platform_layout.addWidget(self.show_platforms_check)
        
        platform_info = QLabel("💡 ستون‌های Platform به صورت خودکار از داده‌ها استخراج می‌شوند")
        platform_info.setStyleSheet("color: #666; font-size: 10pt;")
        platform_layout.addWidget(platform_info)
        
        platform_group.setLayout(platform_layout)
        layout.addWidget(platform_group)
        
        # ═══ بخش 3: فرمول‌های سفارشی ═══
        formula_group = QGroupBox("🧮 ستون‌های محاسباتی (فرمول)")
        formula_layout = QVBoxLayout()
        
        # لیست فرمول‌های موجود
        self.formula_list = QListWidget()
        formula_layout.addWidget(QLabel("فرمول‌های تعریف شده:"))
        formula_layout.addWidget(self.formula_list)
        
        # دکمه‌های مدیریت فرمول
        formula_buttons = QHBoxLayout()
        
        add_formula_btn = QPushButton("➕ افزودن فرمول")
        add_formula_btn.clicked.connect(self.add_formula)
        formula_buttons.addWidget(add_formula_btn)
        
        edit_formula_btn = QPushButton("✏️ ویرایش")
        edit_formula_btn.clicked.connect(self.edit_formula)
        formula_buttons.addWidget(edit_formula_btn)
        
        remove_formula_btn = QPushButton("🗑️ حذف")
        remove_formula_btn.clicked.connect(self.remove_formula)
        formula_buttons.addWidget(remove_formula_btn)
        
        formula_layout.addLayout(formula_buttons)
        
        # راهنما
        help_text = QLabel(
            "💡 متغیرهای قابل استفاده در فرمول:\n"
            "• {gold_purchased}, {purchase_rate}, {purchase_cost}\n"
            "• {total_sold}, {total_revenue}, {total_profit}\n"
            "• {remaining_gold}, {remaining_silver}\n\n"
            "مثال: سود به ازای هر Gold → {total_profit} / {gold_purchased}"
        )
        help_text.setStyleSheet("""
            background: #E8F5E9;
            border: 1px solid #4CAF50;
            border-radius: 5px;
            padding: 10px;
            font-size: 10pt;
        """)
        help_text.setWordWrap(True)
        formula_layout.addWidget(help_text)
        
        formula_group.setLayout(formula_layout)
        layout.addWidget(formula_group)
        
        # ═══ دکمه‌های نهایی ═══
        final_buttons = QHBoxLayout()
        
        save_btn = QPushButton("💾 ذخیره تنظیمات")
        save_btn.clicked.connect(self.save_config)
        save_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                padding: 8px 15px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background: #45a049;
            }
        """)
        final_buttons.addWidget(save_btn)
        
        reset_btn = QPushButton("🔄 بازگردانی به پیش‌فرض")
        reset_btn.clicked.connect(self.reset_to_default)
        final_buttons.addWidget(reset_btn)
        
        cancel_btn = QPushButton("❌ انصراف")
        cancel_btn.clicked.connect(self.reject)
        final_buttons.addWidget(cancel_btn)
        
        layout.addLayout(final_buttons)
    
    def load_config(self):
        """بارگذاری تنظیمات فعلی"""
        visible_columns = self.current_config.get('visible_columns', [])
        
        # علامت‌گذاری ستون‌های انتخاب شده
        for i in range(self.available_list.count()):
            item = self.available_list.item(i)
            col_id = item.data(Qt.ItemDataRole.UserRole)
            if col_id in visible_columns:
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)
        
        # Platform ها
        self.show_platforms_check.setChecked(
            self.current_config.get('show_platforms', True)
        )
        
        # فرمول‌ها
        self.update_formula_list()
    
    def update_formula_list(self):
        """بروزرسانی لیست فرمول‌ها"""
        self.formula_list.clear()
        for formula in self.custom_formulas:
            self.formula_list.addItem(
                f"{formula['name']}: {formula['formula']}"
            )
    
    def select_all_columns(self):
        """انتخاب همه ستون‌ها"""
        for i in range(self.available_list.count()):
            self.available_list.item(i).setCheckState(Qt.CheckState.Checked)
    
    def deselect_all_columns(self):
        """حذف انتخاب همه ستون‌ها"""
        for i in range(self.available_list.count()):
            self.available_list.item(i).setCheckState(Qt.CheckState.Unchecked)
    
    def move_column_up(self):
        """جابجایی ستون به بالا"""
        current_row = self.available_list.currentRow()
        if current_row > 0:
            item = self.available_list.takeItem(current_row)
            self.available_list.insertItem(current_row - 1, item)
            self.available_list.setCurrentRow(current_row - 1)
    
    def move_column_down(self):
        """جابجایی ستون به پایین"""
        current_row = self.available_list.currentRow()
        if current_row < self.available_list.count() - 1:
            item = self.available_list.takeItem(current_row)
            self.available_list.insertItem(current_row + 1, item)
            self.available_list.setCurrentRow(current_row + 1)
    
    def add_formula(self):
        """افزودن فرمول جدید"""
        dialog = FormulaEditorDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            formula_data = dialog.get_formula()
            self.custom_formulas.append(formula_data)
            self.update_formula_list()
    
    def edit_formula(self):
        """ویرایش فرمول"""
        current_row = self.formula_list.currentRow()
        if current_row >= 0:
            formula_data = self.custom_formulas[current_row]
            dialog = FormulaEditorDialog(formula_data, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.custom_formulas[current_row] = dialog.get_formula()
                self.update_formula_list()
    
    def remove_formula(self):
        """حذف فرمول"""
        current_row = self.formula_list.currentRow()
        if current_row >= 0:
            reply = QMessageBox.question(
                self, "تأیید حذف",
                "آیا از حذف این فرمول مطمئن هستید؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                del self.custom_formulas[current_row]
                self.update_formula_list()
    
    def reset_to_default(self):
        """بازگردانی به پیش‌فرض"""
        reply = QMessageBox.question(
            self, "بازگردانی به پیش‌فرض",
            "تمام تنظیمات شخصی حذف و به پیش‌فرض بازگردانده می‌شود. ادامه؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.current_config = self._get_default_config()
            self.custom_formulas = []
            self.load_config()
    
    def save_config(self):
        """ذخیره تنظیمات"""
        # دریافت ستون‌های انتخاب شده
        visible_columns = []
        column_order = []
        
        for i in range(self.available_list.count()):
            item = self.available_list.item(i)
            col_id = item.data(Qt.ItemDataRole.UserRole)
            column_order.append(col_id)
            if item.checkState() == Qt.CheckState.Checked:
                visible_columns.append(col_id)
        
        # ساخت config جدید
        self.current_config = {
            'visible_columns': visible_columns,
            'column_order': column_order,
            'custom_formulas': self.custom_formulas,
            'show_platforms': self.show_platforms_check.isChecked(),
            'platform_columns': []  # خودکار از داده استخراج می‌شود
        }
        
        # ذخیره در فایل
        try:
            with open('data/financial/grid_config.json', 'w', encoding='utf-8') as f:
                json.dump(self.current_config, f, ensure_ascii=False, indent=2)
            
            QMessageBox.information(
                self, "موفقیت",
                "✅ تنظیمات با موفقیت ذخیره شد!\n\n"
                "برای اعمال تغییرات، گزارش را مجدداً باز کنید."
            )
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self, "خطا",
                f"خطا در ذخیره تنظیمات:\n{str(e)}"
            )
    
    def get_config(self):
        """دریافت تنظیمات"""
        return self.current_config


class FormulaEditorDialog(QDialog):
    """
    دیالوگ ویرایشگر فرمول
    """
    
    def __init__(self, formula_data: Dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🧮 ویرایشگر فرمول")
        self.resize(600, 400)
        
        self.formula_data = formula_data or {
            'name': '',
            'formula': '',
            'format': 'number'  # number, currency, percent
        }
        
        self.init_ui()
        self.load_formula()
    
    def init_ui(self):
        """ساخت رابط کاربری"""
        layout = QVBoxLayout(self)
        
        # نام ستون
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("نام ستون:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("مثال: سود به ازای هر Gold")
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # فرمول
        formula_header = QHBoxLayout()
        formula_header.addWidget(QLabel("فرمول محاسباتی:"))
        formula_header.addStretch()
        
        clear_btn = QPushButton("🗑️ پاک کردن")
        clear_btn.clicked.connect(lambda: self.formula_input.clear())
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #FFEBEE;
                border: 1px solid #F44336;
                border-radius: 3px;
                padding: 3px 8px;
                font-size: 9pt;
            }
            QPushButton:hover {
                background: #FFCDD2;
            }
        """)
        formula_header.addWidget(clear_btn)
        
        example_btn = QPushButton("💡 مثال")
        example_btn.clicked.connect(self.insert_example)
        example_btn.setStyleSheet("""
            QPushButton {
                background: #E8F5E9;
                border: 1px solid #4CAF50;
                border-radius: 3px;
                padding: 3px 8px;
                font-size: 9pt;
            }
            QPushButton:hover {
                background: #C8E6C9;
            }
        """)
        formula_header.addWidget(example_btn)
        
        layout.addLayout(formula_header)
        
        self.formula_input = QTextEdit()
        self.formula_input.setPlaceholderText(
            "روی متغیرها یا عملگرها کلیک کنید...\n\n"
            "مثال: {total_profit} / {gold_purchased}"
        )
        self.formula_input.setMaximumHeight(100)
        layout.addWidget(self.formula_input)
        
        # فرمت نمایش
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("فرمت نمایش:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems([
            "عدد (1234.56)",
            "مبلغ (1,234 تومان)",
            "درصد (12.5%)"
        ])
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        layout.addLayout(format_layout)
        
        # راهنمای متغیرها با دکمه‌های کلیک‌پذیر
        help_group = QGroupBox("📋 متغیرهای قابل استفاده (کلیک کنید)")
        help_layout = QVBoxLayout()
        
        # توضیح
        info_label = QLabel("💡 روی هر متغیر کلیک کنید تا به فرمول اضافه شود:")
        info_label.setStyleSheet("color: #1976D2; font-weight: bold; padding: 5px;")
        help_layout.addWidget(info_label)
        
        # متغیرها به صورت دکمه
        variables = [
            ('label', 'کد آکانت'),
            ('gold_purchased', 'مقدار خرید Gold'),
            ('purchase_rate', 'نرخ خرید'),
            ('purchase_cost', 'هزینه خرید'),
            ('total_sold', 'جمع فروش'),
            ('total_revenue', 'درآمد کل'),
            ('total_profit', 'سود کل'),
            ('profit_pct', 'درصد سود'),
            ('remaining_gold', 'موجودی Gold'),
            ('remaining_silver', 'موجودی Silver')
        ]
        
        # Grid برای دکمه‌های متغیرها
        from PyQt6.QtWidgets import QGridLayout
        variables_grid = QGridLayout()
        variables_grid.setSpacing(5)
        
        for idx, (var_key, var_desc) in enumerate(variables):
            btn = QPushButton(f"{{{var_key}}}")
            btn.setToolTip(var_desc)
            btn.clicked.connect(lambda checked, v=var_key: self.insert_variable(v))
            btn.setStyleSheet("""
                QPushButton {
                    background: #E3F2FD;
                    border: 1px solid #2196F3;
                    border-radius: 5px;
                    padding: 5px 10px;
                    font-family: 'Courier New', monospace;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #BBDEFB;
                    border: 2px solid #1976D2;
                }
                QPushButton:pressed {
                    background: #90CAF9;
                }
            """)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            # 2 ستون در هر سطر
            row = idx // 2
            col = idx % 2
            variables_grid.addWidget(btn, row, col)
        
        help_layout.addLayout(variables_grid)
        
        # عملگرها
        operators_layout = QHBoxLayout()
        operators_layout.addWidget(QLabel("🧮 عملگرها:"))
        
        operators = ['+', '-', '*', '/', '(', ')']
        for op in operators:
            op_btn = QPushButton(op)
            op_btn.clicked.connect(lambda checked, o=op: self.insert_operator(o))
            op_btn.setStyleSheet("""
                QPushButton {
                    background: #FFF3E0;
                    border: 1px solid #FF9800;
                    border-radius: 5px;
                    padding: 5px 15px;
                    font-weight: bold;
                    font-size: 14pt;
                }
                QPushButton:hover {
                    background: #FFE0B2;
                }
            """)
            op_btn.setFixedWidth(40)
            op_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            operators_layout.addWidget(op_btn)
        
        operators_layout.addStretch()
        help_layout.addLayout(operators_layout)
        
        help_group.setLayout(help_layout)
        layout.addWidget(help_group)
        
        # دکمه‌ها
        buttons = QHBoxLayout()
        
        save_btn = QPushButton("💾 ذخیره")
        save_btn.clicked.connect(self.save_formula)
        save_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                padding: 8px 15px;
                font-weight: bold;
                border-radius: 5px;
            }
        """)
        buttons.addWidget(save_btn)
        
        cancel_btn = QPushButton("❌ انصراف")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)
        
        layout.addLayout(buttons)
    
    def insert_variable(self, variable: str):
        """درج متغیر در فرمول"""
        cursor = self.formula_input.textCursor()
        cursor.insertText(f"{{{variable}}}")
        self.formula_input.setFocus()
    
    def insert_operator(self, operator: str):
        """درج عملگر در فرمول"""
        cursor = self.formula_input.textCursor()
        # اضافه کردن فاصله قبل و بعد عملگر (به جز پرانتز)
        if operator in ['(', ')']:
            cursor.insertText(operator)
        else:
            cursor.insertText(f" {operator} ")
        self.formula_input.setFocus()
    
    def insert_example(self):
        """درج یک فرمول نمونه"""
        from PyQt6.QtWidgets import QMenu
        
        menu = QMenu(self)
        
        examples = [
            ("سود به ازای هر Gold", "{total_profit} / {gold_purchased}"),
            ("مارجین سود (درصد)", "({total_revenue} - {purchase_cost}) / {total_revenue} * 100"),
            ("قیمت فروش متوسط", "{total_revenue} / {total_sold}"),
            ("سود خالص (با کسر 10% کمیسیون)", "{total_profit} * 0.9"),
            ("نسبت فروش به خرید", "{total_sold} / {gold_purchased} * 100"),
            ("درآمد بعد از کسر هزینه", "{total_revenue} - {purchase_cost}")
        ]
        
        for name, formula in examples:
            action = menu.addAction(f"💡 {name}")
            action.triggered.connect(lambda checked, f=formula: self.formula_input.setPlainText(f))
        
        # نمایش منو در محل دکمه
        menu.exec(self.sender().mapToGlobal(self.sender().rect().bottomLeft()))
    
    def load_formula(self):
        """بارگذاری فرمول"""
        self.name_input.setText(self.formula_data.get('name', ''))
        self.formula_input.setPlainText(self.formula_data.get('formula', ''))
        
        format_map = {
            'number': 0,
            'currency': 1,
            'percent': 2
        }
        self.format_combo.setCurrentIndex(
            format_map.get(self.formula_data.get('format', 'number'), 0)
        )
    
    def save_formula(self):
        """ذخیره فرمول"""
        name = self.name_input.text().strip()
        formula = self.formula_input.toPlainText().strip()
        
        if not name:
            QMessageBox.warning(self, "خطا", "نام ستون را وارد کنید")
            return
        
        if not formula:
            QMessageBox.warning(self, "خطا", "فرمول را وارد کنید")
            return
        
        # اعتبارسنجی فرمول
        if not self.validate_formula(formula):
            QMessageBox.warning(
                self, "خطای فرمول",
                "فرمول نامعتبر است!\n\n"
                "از متغیرهای معتبر و عملگرهای ریاضی استفاده کنید."
            )
            return
        
        format_map = ['number', 'currency', 'percent']
        
        self.formula_data = {
            'name': name,
            'formula': formula,
            'format': format_map[self.format_combo.currentIndex()]
        }
        
        self.accept()
    
    def validate_formula(self, formula: str) -> bool:
        """اعتبارسنجی فرمول"""
        valid_variables = [
            'label', 'gold_purchased', 'purchase_rate', 'purchase_cost',
            'total_sold', 'total_revenue', 'total_profit', 'profit_pct',
            'remaining_gold', 'remaining_silver'
        ]
        
        # بررسی ساده - چک می‌کنیم که فقط متغیرهای معتبر و عملگرها استفاده شده
        import re
        
        # استخراج متغیرها
        variables = re.findall(r'\{(\w+)\}', formula)
        
        # چک کردن اینکه همه متغیرها معتبر هستند
        for var in variables:
            if var not in valid_variables:
                return False
        
        return True
    
    def get_formula(self):
        """دریافت فرمول"""
        return self.formula_data
