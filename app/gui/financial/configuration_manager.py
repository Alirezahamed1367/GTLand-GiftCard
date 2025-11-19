"""
Configuration Manager UI - مدیریت تنظیمات مالی
این ماژول شامل UI کامل برای مدیریت تمام تنظیمات سیستم است
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFormLayout, QLineEdit, QComboBox, QTextEdit, QSpinBox,
    QCheckBox, QMessageBox, QGroupBox, QDialogButtonBox, QInputDialog,
    QDateEdit, QSplitter, QListWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from datetime import date

from app.models.financial import (
    UnitType, Department, Platform, Region, TransactionType,
    SKUPattern, CustomerCodePattern, CurrencyRate, CalculationFormula,
    FinancialSessionLocal
)


# ═══════════════════════════════════════════════════════════
#                   MAIN CONFIGURATION MANAGER
# ═══════════════════════════════════════════════════════════

class ConfigurationManager(QDialog):
    """
    مدیر تنظیمات مالی - دیالوگ اصلی
    """
    
    config_changed = pyqtSignal()  # سیگنال تغییر تنظیمات
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session = FinancialSessionLocal()
        self.setWindowTitle("⚙️ مدیریت تنظیمات مالی")
        self.setMinimumSize(1100, 600)
        self.resize(1300, 750)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        self.init_ui()
        
    def init_ui(self):
        """ایجاد رابط کاربری"""
        layout = QVBoxLayout(self)
        
        # عنوان
        header = QLabel("⚙️ تنظیمات سیستم مالی")
        header.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("padding: 15px; background: #2196F3; color: white; border-radius: 5px;")
        layout.addWidget(header)
        
        # تب‌ها
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                background: white;
                border-radius: 5px;
            }
            QTabBar::tab {
                background: #f5f5f5;
                color: #333;
                padding: 10px 20px;
                margin: 2px;
                border-radius: 5px;
                font-size: 11pt;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #2196F3;
                color: white;
            }
            QTabBar::tab:hover {
                background: #64B5F6;
                color: white;
            }
        """)
        
        # تب‌های مختلف
        self.tabs.addTab(self.create_units_tab(), "📏 واحدها")
        self.tabs.addTab(self.create_departments_tab(), "🏢 دپارتمان‌ها")
        self.tabs.addTab(self.create_platforms_tab(), "🎮 پلتفرم‌ها")
        self.tabs.addTab(self.create_regions_tab(), "🌍 ریجن‌ها")
        self.tabs.addTab(self.create_customers_tab(), "👥 مشتریان")
        self.tabs.addTab(self.create_transaction_types_tab(), "📊 نوع معاملات")
        self.tabs.addTab(self.create_sku_patterns_tab(), "🏷️ کد کالا")
        self.tabs.addTab(self.create_customer_patterns_tab(), "🔢 الگوی کد مشتری")
        self.tabs.addTab(self.create_currency_rates_tab(), "💱 نرخ ارز")
        self.tabs.addTab(self.create_formulas_tab(), "🧮 فرمول‌ها")
        
        layout.addWidget(self.tabs)
        
        # دکمه بستن
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(10, 10, 10, 10)
        buttons_layout.addStretch()
        
        close_btn = QPushButton("✅ بستن")
        close_btn.setStyleSheet(self.get_button_style("#4CAF50"))
        close_btn.setMinimumSize(150, 45)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
        
    def get_button_style(self, color):
        """استایل دکمه"""
        return f"""
            QPushButton {{
                background: {color};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 25px;
                font-size: 11pt;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {color}dd;
            }}
            QPushButton:pressed {{
                background: {color}aa;
            }}
        """
    
    def create_units_tab(self):
        """تب واحدهای اندازه‌گیری"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # دکمه‌ها
        buttons_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ افزودن واحد جدید")
        add_btn.setStyleSheet(self.get_button_style("#4CAF50"))
        add_btn.clicked.connect(self.add_unit)
        buttons_layout.addWidget(add_btn)
        
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
        # جدول
        self.units_table = QTableWidget()
        self.units_table.setColumnCount(7)
        self.units_table.setHorizontalHeaderLabels([
            "کد", "نام فارسی", "نام انگلیسی", "نماد", "دسته", "وضعیت", "عملیات"
        ])
        self.units_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.units_table.setAlternatingRowColors(True)
        self.units_table.setStyleSheet("""
            QTableWidget {
                background: white;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background: #f5f5f5;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.units_table)
        
        self.load_units()
        
        return widget
    
    def load_units(self):
        """بارگذاری واحدها"""
        try:
            units = self.session.query(UnitType).order_by(UnitType.display_order).all()
            self.units_table.setRowCount(len(units))
            
            for row, unit in enumerate(units):
                # کد
                self.units_table.setItem(row, 0, QTableWidgetItem(unit.unit_code))
                
                # نام فارسی
                self.units_table.setItem(row, 1, QTableWidgetItem(unit.unit_name_fa))
                
                # نام انگلیسی
                self.units_table.setItem(row, 2, QTableWidgetItem(unit.unit_name_en or "-"))
                
                # نماد
                self.units_table.setItem(row, 3, QTableWidgetItem(unit.unit_symbol or "-"))
                
                # دسته
                self.units_table.setItem(row, 4, QTableWidgetItem(unit.unit_category or "-"))
                
                # وضعیت
                status_item = QTableWidgetItem("✅ فعال" if unit.is_active else "❌ غیرفعال")
                status_item.setForeground(QColor("#4CAF50" if unit.is_active else "#F44336"))
                self.units_table.setItem(row, 5, status_item)
                
                # عملیات
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(5, 2, 5, 2)
                
                edit_btn = QPushButton("✏️")
                edit_btn.setToolTip("ویرایش")
                edit_btn.setStyleSheet(self.get_button_style("#FF9800"))
                edit_btn.clicked.connect(lambda checked, u=unit: self.edit_unit(u))
                actions_layout.addWidget(edit_btn)
                
                delete_btn = QPushButton("🗑️")
                delete_btn.setToolTip("حذف")
                delete_btn.setStyleSheet(self.get_button_style("#F44336"))
                delete_btn.clicked.connect(lambda checked, u=unit: self.delete_unit(u))
                actions_layout.addWidget(delete_btn)
                
                self.units_table.setCellWidget(row, 6, actions_widget)
                
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"❌ خطا در بارگذاری واحدها:\n{str(e)}")
    
    def add_unit(self):
        """افزودن واحد جدید"""
        dialog = UnitDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                unit = UnitType(
                    unit_code=dialog.code_input.text().strip().upper(),
                    unit_name_fa=dialog.name_fa_input.text().strip(),
                    unit_name_en=dialog.name_en_input.text().strip(),
                    unit_symbol=dialog.symbol_input.text().strip(),
                    unit_category=dialog.category_combo.currentText(),
                    is_active=dialog.active_check.isChecked(),
                    display_order=dialog.order_spin.value(),
                    notes=dialog.notes_input.toPlainText().strip()
                )
                
                self.session.add(unit)
                self.session.commit()
                
                QMessageBox.information(self, "موفق", f"✅ واحد '{unit.unit_name_fa}' با موفقیت اضافه شد")
                self.load_units()
                self.config_changed.emit()
                
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "خطا", f"❌ خطا در افزودن واحد:\n{str(e)}")
    
    def edit_unit(self, unit):
        """ویرایش واحد"""
        dialog = UnitDialog(self, unit)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                unit.unit_code = dialog.code_input.text().strip().upper()
                unit.unit_name_fa = dialog.name_fa_input.text().strip()
                unit.unit_name_en = dialog.name_en_input.text().strip()
                unit.unit_symbol = dialog.symbol_input.text().strip()
                unit.unit_category = dialog.category_combo.currentText()
                unit.is_active = dialog.active_check.isChecked()
                unit.display_order = dialog.order_spin.value()
                unit.notes = dialog.notes_input.toPlainText().strip()
                
                self.session.commit()
                
                QMessageBox.information(self, "موفق", f"✅ واحد '{unit.unit_name_fa}' با موفقیت ویرایش شد")
                self.load_units()
                self.config_changed.emit()
                
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "خطا", f"❌ خطا در ویرایش واحد:\n{str(e)}")
    
    def delete_unit(self, unit):
        """حذف واحد"""
        reply = QMessageBox.question(
            self,
            "تأیید حذف",
            f"⚠️ آیا مطمئن هستید که می‌خواهید واحد '{unit.unit_name_fa}' را حذف کنید؟\n\n"
            f"⚠️ توجه: اگر این واحد در جایی استفاده شده باشد، حذف امکان‌پذیر نیست.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.session.delete(unit)
                self.session.commit()
                
                QMessageBox.information(self, "موفق", f"✅ واحد '{unit.unit_name_fa}' با موفقیت حذف شد")
                self.load_units()
                self.config_changed.emit()
                
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(
                    self,
                    "خطا",
                    f"❌ خطا در حذف واحد:\n{str(e)}\n\n"
                    f"💡 احتمالاً این واحد در جایی استفاده شده است."
                )
    
    def create_departments_tab(self):
        """تب دپارتمان‌ها"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # دکمه‌ها
        buttons_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ افزودن دپارتمان جدید")
        add_btn.setStyleSheet(self.get_button_style("#4CAF50"))
        add_btn.clicked.connect(self.add_department)
        buttons_layout.addWidget(add_btn)
        
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
        # جدول
        self.departments_table = QTableWidget()
        self.departments_table.setColumnCount(5)
        self.departments_table.setHorizontalHeaderLabels([
            "کد", "نام فارسی", "نام انگلیسی", "وضعیت", "عملیات"
        ])
        self.departments_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.departments_table.setAlternatingRowColors(True)
        self.departments_table.setStyleSheet("""
            QTableWidget {
                background: white;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            QHeaderView::section {
                background: #f5f5f5;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.departments_table)
        
        self.load_departments()
        
        return widget
    
    def load_departments(self):
        """بارگذاری دپارتمان‌ها"""
        try:
            departments = self.session.query(Department).order_by(Department.department_code).all()
            self.departments_table.setRowCount(len(departments))
            
            for row, dept in enumerate(departments):
                self.departments_table.setItem(row, 0, QTableWidgetItem(dept.department_code))
                self.departments_table.setItem(row, 1, QTableWidgetItem(dept.department_name_fa))
                self.departments_table.setItem(row, 2, QTableWidgetItem(dept.department_name_en or "-"))
                
                status_item = QTableWidgetItem("✅ فعال" if dept.is_active else "❌ غیرفعال")
                status_item.setForeground(QColor("#4CAF50" if dept.is_active else "#F44336"))
                self.departments_table.setItem(row, 3, status_item)
                
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(5, 2, 5, 2)
                
                edit_btn = QPushButton("✏️")
                edit_btn.setToolTip("ویرایش")
                edit_btn.setStyleSheet(self.get_button_style("#FF9800"))
                edit_btn.clicked.connect(lambda checked, d=dept: self.edit_department(d))
                actions_layout.addWidget(edit_btn)
                
                delete_btn = QPushButton("🗑️")
                delete_btn.setToolTip("حذف")
                delete_btn.setStyleSheet(self.get_button_style("#F44336"))
                delete_btn.clicked.connect(lambda checked, d=dept: self.delete_department(d))
                actions_layout.addWidget(delete_btn)
                
                self.departments_table.setCellWidget(row, 4, actions_widget)
                
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"❌ خطا در بارگذاری دپارتمان‌ها:\n{str(e)}")
    
    def add_department(self):
        """افزودن دپارتمان جدید"""
        dialog = DepartmentDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                dept = Department(
                    department_code=dialog.code_input.text().strip().upper(),
                    department_name_fa=dialog.name_fa_input.text().strip(),
                    department_name_en=dialog.name_en_input.text().strip(),
                    is_active=dialog.active_check.isChecked(),
                    notes=dialog.notes_input.toPlainText().strip()
                )
                
                self.session.add(dept)
                self.session.commit()
                
                QMessageBox.information(self, "موفق", f"✅ دپارتمان '{dept.department_name_fa}' با موفقیت اضافه شد")
                self.load_departments()
                self.config_changed.emit()
                
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "خطا", f"❌ خطا در افزودن دپارتمان:\n{str(e)}")
    
    def edit_department(self, dept):
        """ویرایش دپارتمان"""
        dialog = DepartmentDialog(self, dept)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                dept.department_code = dialog.code_input.text().strip().upper()
                dept.department_name_fa = dialog.name_fa_input.text().strip()
                dept.department_name_en = dialog.name_en_input.text().strip()
                dept.is_active = dialog.active_check.isChecked()
                dept.notes = dialog.notes_input.toPlainText().strip()
                
                self.session.commit()
                
                QMessageBox.information(self, "موفق", f"✅ دپارتمان '{dept.department_name_fa}' با موفقیت ویرایش شد")
                self.load_departments()
                self.config_changed.emit()
                
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "خطا", f"❌ خطا در ویرایش دپارتمان:\n{str(e)}")
    
    def delete_department(self, dept):
        """حذف دپارتمان"""
        reply = QMessageBox.question(
            self,
            "تأیید حذف",
            f"⚠️ آیا مطمئن هستید که می‌خواهید دپارتمان '{dept.department_name_fa}' را حذف کنید؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.session.delete(dept)
                self.session.commit()
                
                QMessageBox.information(self, "موفق", f"✅ دپارتمان '{dept.department_name_fa}' با موفقیت حذف شد")
                self.load_departments()
                self.config_changed.emit()
                
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "خطا", f"❌ خطا در حذف دپارتمان:\n{str(e)}")
    
    def create_platforms_tab(self):
        """تب پلتفرم‌ها"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # هدر
        header_layout = QHBoxLayout()
        title = QLabel("🎮 پلتفرم‌ها")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        add_btn = QPushButton("➕ افزودن پلتفرم")
        add_btn.setStyleSheet(self.get_button_style("#4CAF50"))
        add_btn.clicked.connect(self.add_platform)
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        # جدول
        self.platforms_table = QTableWidget()
        self.platforms_table.setColumnCount(5)
        self.platforms_table.setHorizontalHeaderLabels(["کد", "نام فارسی", "نام انگلیسی", "وضعیت", "عملیات"])
        self.platforms_table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.platforms_table.setAlternatingRowColors(True)
        self.platforms_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.platforms_table.horizontalHeader().setStretchLastSection(True)
        self.platforms_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.platforms_table)
        
        return widget
    
    def create_regions_tab(self):
        """تب ریجن‌ها"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        header_layout = QHBoxLayout()
        title = QLabel("🌍 ریجن‌ها")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        add_btn = QPushButton("➕ افزودن ریجن")
        add_btn.setStyleSheet(self.get_button_style("#4CAF50"))
        add_btn.clicked.connect(self.add_region)
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        self.regions_table = QTableWidget()
        self.regions_table.setColumnCount(5)
        self.regions_table.setHorizontalHeaderLabels(["کد", "نام فارسی", "نام انگلیسی", "وضعیت", "عملیات"])
        self.regions_table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.regions_table.setAlternatingRowColors(True)
        self.regions_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.regions_table.horizontalHeader().setStretchLastSection(True)
        self.regions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.regions_table)
        
        return widget
    
    def create_transaction_types_tab(self):
        """تب نوع معاملات"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        header_layout = QHBoxLayout()
        title = QLabel("📊 نوع معاملات")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        add_btn = QPushButton("➕ افزودن نوع معامله")
        add_btn.setStyleSheet(self.get_button_style("#4CAF50"))
        add_btn.clicked.connect(self.add_transaction_type)
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        self.transaction_types_table = QTableWidget()
        self.transaction_types_table.setColumnCount(6)
        self.transaction_types_table.setHorizontalHeaderLabels(["کد", "نام فارسی", "نام انگلیسی", "تأثیر", "وضعیت", "عملیات"])
        self.transaction_types_table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.transaction_types_table.setAlternatingRowColors(True)
        self.transaction_types_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.transaction_types_table.horizontalHeader().setStretchLastSection(True)
        self.transaction_types_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.transaction_types_table)
        
        return widget
    
    def create_sku_patterns_tab(self):
        """تب الگوی کد کالا"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        header_layout = QHBoxLayout()
        title = QLabel("🏷️ الگوی کد کالا")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        add_btn = QPushButton("➕ افزودن الگو")
        add_btn.setStyleSheet(self.get_button_style("#4CAF50"))
        add_btn.clicked.connect(self.add_sku_pattern)
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        self.sku_patterns_table = QTableWidget()
        self.sku_patterns_table.setColumnCount(5)
        self.sku_patterns_table.setHorizontalHeaderLabels(["نام", "الگو", "مثال", "وضعیت", "عملیات"])
        self.sku_patterns_table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.sku_patterns_table.setAlternatingRowColors(True)
        self.sku_patterns_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.sku_patterns_table.horizontalHeader().setStretchLastSection(True)
        self.sku_patterns_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.sku_patterns_table)
        
        return widget
    
    def create_customer_patterns_tab(self):
        """تب الگوی کد مشتری"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        header_layout = QHBoxLayout()
        title = QLabel("👤 الگوی کد مشتری")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        add_btn = QPushButton("➕ افزودن الگو")
        add_btn.setStyleSheet(self.get_button_style("#4CAF50"))
        add_btn.clicked.connect(self.add_customer_pattern)
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        self.customer_patterns_table = QTableWidget()
        self.customer_patterns_table.setColumnCount(5)
        self.customer_patterns_table.setHorizontalHeaderLabels(["نام", "الگو", "مثال", "وضعیت", "عملیات"])
        self.customer_patterns_table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.customer_patterns_table.setAlternatingRowColors(True)
        self.customer_patterns_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.customer_patterns_table.horizontalHeader().setStretchLastSection(True)
        self.customer_patterns_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.customer_patterns_table)
        
        return widget
    
    def create_currency_rates_tab(self):
        """تب نرخ ارز"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        header_layout = QHBoxLayout()
        title = QLabel("💱 نرخ ارز")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        add_btn = QPushButton("➕ افزودن نرخ")
        add_btn.setStyleSheet(self.get_button_style("#4CAF50"))
        add_btn.clicked.connect(self.add_currency_rate)
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        self.currency_rates_table = QTableWidget()
        self.currency_rates_table.setColumnCount(6)
        self.currency_rates_table.setHorizontalHeaderLabels(["ارز مبدأ", "ارز مقصد", "نرخ", "تاریخ", "وضعیت", "عملیات"])
        self.currency_rates_table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.currency_rates_table.setAlternatingRowColors(True)
        self.currency_rates_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.currency_rates_table.horizontalHeader().setStretchLastSection(True)
        self.currency_rates_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.currency_rates_table)
        
        return widget
    
    def create_formulas_tab(self):
        """تب فرمول‌ها"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        header_layout = QHBoxLayout()
        title = QLabel("🧮 فرمول‌ها")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        add_btn = QPushButton("➕ افزودن فرمول")
        add_btn.setStyleSheet(self.get_button_style("#4CAF50"))
        add_btn.clicked.connect(self.add_formula)
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        self.formulas_table = QTableWidget()
        self.formulas_table.setColumnCount(5)
        self.formulas_table.setHorizontalHeaderLabels(["نام", "کد", "فرمول", "وضعیت", "عملیات"])
        self.formulas_table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.formulas_table.setAlternatingRowColors(True)
        self.formulas_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.formulas_table.horizontalHeader().setStretchLastSection(True)
        self.formulas_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.formulas_table)
        
        return widget
    
    # ═══════════ متدهای پلتفرم‌ها ═══════════
    
    def load_platforms(self):
        """بارگذاری پلتفرم‌ها"""
        try:
            from app.models.financial import Platform
            platforms = self.session.query(Platform).order_by(Platform.platform_code).all()
            
            self.platforms_table.setRowCount(len(platforms))
            
            for row, platform in enumerate(platforms):
                self.platforms_table.setItem(row, 0, QTableWidgetItem(platform.platform_code))
                self.platforms_table.setItem(row, 1, QTableWidgetItem(platform.platform_name_fa))
                self.platforms_table.setItem(row, 2, QTableWidgetItem(platform.platform_name_en or ""))
                self.platforms_table.setItem(row, 3, QTableWidgetItem("✅ فعال" if platform.is_active else "❌ غیرفعال"))
                
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(5, 2, 5, 2)
                
                edit_btn = QPushButton("✏️")
                edit_btn.setToolTip("ویرایش")
                edit_btn.setStyleSheet(self.get_button_style("#FF9800"))
                edit_btn.clicked.connect(lambda checked, p=platform: self.edit_platform(p))
                actions_layout.addWidget(edit_btn)
                
                delete_btn = QPushButton("🗑️")
                delete_btn.setToolTip("حذف")
                delete_btn.setStyleSheet(self.get_button_style("#F44336"))
                delete_btn.clicked.connect(lambda checked, p=platform: self.delete_platform(p))
                actions_layout.addWidget(delete_btn)
                
                self.platforms_table.setCellWidget(row, 4, actions_widget)
                
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"❌ خطا در بارگذاری پلتفرم‌ها:\n{str(e)}")
    
    def add_platform(self):
        """افزودن پلتفرم جدید"""
        from app.models.financial import Platform
        from PyQt6.QtWidgets import QLineEdit, QCheckBox, QTextEdit, QFormLayout, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("➕ افزودن پلتفرم")
        dialog.setMinimumWidth(500)
        dialog.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        
        code_input = QLineEdit()
        code_input.setPlaceholderText("مثال: COD_MOBILE")
        form.addRow("کد پلتفرم*:", code_input)
        
        name_fa_input = QLineEdit()
        name_fa_input.setPlaceholderText("مثال: کالاف موبایل")
        form.addRow("نام فارسی*:", name_fa_input)
        
        name_en_input = QLineEdit()
        name_en_input.setPlaceholderText("مثال: Call of Duty Mobile")
        form.addRow("نام انگلیسی:", name_en_input)
        
        active_check = QCheckBox("فعال")
        active_check.setChecked(True)
        form.addRow("وضعیت:", active_check)
        
        notes_input = QTextEdit()
        notes_input.setMaximumHeight(80)
        form.addRow("یادداشت:", notes_input)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if not code_input.text().strip() or not name_fa_input.text().strip():
                QMessageBox.warning(self, "خطا", "⚠️ لطفاً کد و نام فارسی را وارد کنید")
                return
            
            try:
                platform = Platform(
                    platform_code=code_input.text().strip().upper(),
                    platform_name_fa=name_fa_input.text().strip(),
                    platform_name_en=name_en_input.text().strip(),
                    is_active=active_check.isChecked(),
                    notes=notes_input.toPlainText().strip()
                )
                
                self.session.add(platform)
                self.session.commit()
                
                QMessageBox.information(self, "موفق", f"✅ پلتفرم '{platform.platform_name_fa}' با موفقیت اضافه شد")
                self.load_platforms()
                self.config_changed.emit()
                
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "خطا", f"❌ خطا در افزودن پلتفرم:\n{str(e)}")
    
    def edit_platform(self, platform):
        """ویرایش پلتفرم"""
        from PyQt6.QtWidgets import QLineEdit, QCheckBox, QTextEdit, QFormLayout, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("✏️ ویرایش پلتفرم")
        dialog.setMinimumWidth(500)
        dialog.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        
        code_input = QLineEdit(platform.platform_code)
        form.addRow("کد پلتفرم*:", code_input)
        
        name_fa_input = QLineEdit(platform.platform_name_fa)
        form.addRow("نام فارسی*:", name_fa_input)
        
        name_en_input = QLineEdit(platform.platform_name_en or "")
        form.addRow("نام انگلیسی:", name_en_input)
        
        active_check = QCheckBox("فعال")
        active_check.setChecked(platform.is_active)
        form.addRow("وضعیت:", active_check)
        
        notes_input = QTextEdit()
        notes_input.setPlainText(platform.notes or "")
        notes_input.setMaximumHeight(80)
        form.addRow("یادداشت:", notes_input)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if not code_input.text().strip() or not name_fa_input.text().strip():
                QMessageBox.warning(self, "خطا", "⚠️ لطفاً کد و نام فارسی را وارد کنید")
                return
            
            try:
                platform.platform_code = code_input.text().strip().upper()
                platform.platform_name_fa = name_fa_input.text().strip()
                platform.platform_name_en = name_en_input.text().strip()
                platform.is_active = active_check.isChecked()
                platform.notes = notes_input.toPlainText().strip()
                
                self.session.commit()
                
                QMessageBox.information(self, "موفق", f"✅ پلتفرم '{platform.platform_name_fa}' با موفقیت ویرایش شد")
                self.load_platforms()
                self.config_changed.emit()
                
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "خطا", f"❌ خطا در ویرایش پلتفرم:\n{str(e)}")
    
    def delete_platform(self, platform):
        """حذف پلتفرم"""
        reply = QMessageBox.question(
            self,
            "تأیید حذف",
            f"⚠️ آیا مطمئن هستید که می‌خواهید پلتفرم '{platform.platform_name_fa}' را حذف کنید؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.session.delete(platform)
                self.session.commit()
                
                QMessageBox.information(self, "موفق", f"✅ پلتفرم '{platform.platform_name_fa}' با موفقیت حذف شد")
                self.load_platforms()
                self.config_changed.emit()
                
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "خطا", f"❌ خطا در حذف پلتفرم:\n{str(e)}")
    
    # ═══════════ متدهای ریجن‌ها ═══════════
    
    def load_regions(self):
        """بارگذاری ریجن‌ها"""
        try:
            from app.models.financial import Region
            regions = self.session.query(Region).order_by(Region.region_code).all()
            
            self.regions_table.setRowCount(len(regions))
            
            for row, region in enumerate(regions):
                self.regions_table.setItem(row, 0, QTableWidgetItem(region.region_code))
                self.regions_table.setItem(row, 1, QTableWidgetItem(region.region_name_fa))
                self.regions_table.setItem(row, 2, QTableWidgetItem(region.region_name_en or ""))
                self.regions_table.setItem(row, 3, QTableWidgetItem("✅ فعال" if region.is_active else "❌ غیرفعال"))
                
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(5, 2, 5, 2)
                
                edit_btn = QPushButton("✏️")
                edit_btn.setToolTip("ویرایش")
                edit_btn.setStyleSheet(self.get_button_style("#FF9800"))
                edit_btn.clicked.connect(lambda checked, r=region: self.edit_region(r))
                actions_layout.addWidget(edit_btn)
                
                delete_btn = QPushButton("🗑️")
                delete_btn.setToolTip("حذف")
                delete_btn.setStyleSheet(self.get_button_style("#F44336"))
                delete_btn.clicked.connect(lambda checked, r=region: self.delete_region(r))
                actions_layout.addWidget(delete_btn)
                
                self.regions_table.setCellWidget(row, 4, actions_widget)
                
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"❌ خطا در بارگذاری ریجن‌ها:\n{str(e)}")
    
    def add_region(self):
        """افزودن ریجن جدید"""
        from app.models.financial import Region
        from PyQt6.QtWidgets import QLineEdit, QCheckBox, QTextEdit, QFormLayout, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("➕ افزودن ریجن")
        dialog.setMinimumWidth(500)
        dialog.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        
        code_input = QLineEdit()
        code_input.setPlaceholderText("مثال: US")
        form.addRow("کد ریجن*:", code_input)
        
        name_fa_input = QLineEdit()
        name_fa_input.setPlaceholderText("مثال: آمریکا")
        form.addRow("نام فارسی*:", name_fa_input)
        
        name_en_input = QLineEdit()
        name_en_input.setPlaceholderText("مثال: United States")
        form.addRow("نام انگلیسی:", name_en_input)
        
        active_check = QCheckBox("فعال")
        active_check.setChecked(True)
        form.addRow("وضعیت:", active_check)
        
        notes_input = QTextEdit()
        notes_input.setMaximumHeight(80)
        form.addRow("یادداشت:", notes_input)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if not code_input.text().strip() or not name_fa_input.text().strip():
                QMessageBox.warning(self, "خطا", "⚠️ لطفاً کد و نام فارسی را وارد کنید")
                return
            
            try:
                region = Region(
                    region_code=code_input.text().strip().upper(),
                    region_name_fa=name_fa_input.text().strip(),
                    region_name_en=name_en_input.text().strip(),
                    is_active=active_check.isChecked(),
                    notes=notes_input.toPlainText().strip()
                )
                
                self.session.add(region)
                self.session.commit()
                
                QMessageBox.information(self, "موفق", f"✅ ریجن '{region.region_name_fa}' با موفقیت اضافه شد")
                self.load_regions()
                self.config_changed.emit()
                
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "خطا", f"❌ خطا در افزودن ریجن:\n{str(e)}")
    
    def edit_region(self, region):
        """ویرایش ریجن"""
        from PyQt6.QtWidgets import QLineEdit, QCheckBox, QTextEdit, QFormLayout, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("✏️ ویرایش ریجن")
        dialog.setMinimumWidth(500)
        dialog.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        
        code_input = QLineEdit(region.region_code)
        form.addRow("کد ریجن*:", code_input)
        
        name_fa_input = QLineEdit(region.region_name_fa)
        form.addRow("نام فارسی*:", name_fa_input)
        
        name_en_input = QLineEdit(region.region_name_en or "")
        form.addRow("نام انگلیسی:", name_en_input)
        
        active_check = QCheckBox("فعال")
        active_check.setChecked(region.is_active)
        form.addRow("وضعیت:", active_check)
        
        notes_input = QTextEdit()
        notes_input.setPlainText(region.notes or "")
        notes_input.setMaximumHeight(80)
        form.addRow("یادداشت:", notes_input)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if not code_input.text().strip() or not name_fa_input.text().strip():
                QMessageBox.warning(self, "خطا", "⚠️ لطفاً کد و نام فارسی را وارد کنید")
                return
            
            try:
                region.region_code = code_input.text().strip().upper()
                region.region_name_fa = name_fa_input.text().strip()
                region.region_name_en = name_en_input.text().strip()
                region.is_active = active_check.isChecked()
                region.notes = notes_input.toPlainText().strip()
                
                self.session.commit()
                
                QMessageBox.information(self, "موفق", f"✅ ریجن '{region.region_name_fa}' با موفقیت ویرایش شد")
                self.load_regions()
                self.config_changed.emit()
                
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "خطا", f"❌ خطا در ویرایش ریجن:\n{str(e)}")
    
    def delete_region(self, region):
        """حذف ریجن"""
        reply = QMessageBox.question(
            self,
            "تأیید حذف",
            f"⚠️ آیا مطمئن هستید که می‌خواهید ریجن '{region.region_name_fa}' را حذف کنید؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.session.delete(region)
                self.session.commit()
                
                QMessageBox.information(self, "موفق", f"✅ ریجن '{region.region_name_fa}' با موفقیت حذف شد")
                self.load_regions()
                self.config_changed.emit()
                
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "خطا", f"❌ خطا در حذف ریجن:\n{str(e)}")
    
    # ═══════════ متدهای مشتریان ═══════════
    
    def create_customers_tab(self):
        """تب مشتریان"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        header_layout = QHBoxLayout()
        title = QLabel("👥 مشتریان")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        add_btn = QPushButton("➕ افزودن مشتری")
        add_btn.setStyleSheet(self.get_button_style("#4CAF50"))
        add_btn.clicked.connect(self.add_customer)
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        self.customers_table = QTableWidget()
        self.customers_table.setColumnCount(4)
        self.customers_table.setHorizontalHeaderLabels(["کد مشتری", "نام", "وضعیت", "عملیات"])
        self.customers_table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.customers_table.setAlternatingRowColors(True)
        self.customers_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.customers_table.horizontalHeader().setStretchLastSection(True)
        self.customers_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.customers_table)
        
        return widget
    
    def load_customers(self):
        """بارگذاری مشتریان"""
        try:
            from app.models.financial import Customer
            customers = self.session.query(Customer).order_by(Customer.customer_code).all()
            
            self.customers_table.setRowCount(len(customers))
            
            for row, customer in enumerate(customers):
                self.customers_table.setItem(row, 0, QTableWidgetItem(customer.customer_code))
                self.customers_table.setItem(row, 1, QTableWidgetItem(customer.customer_name or ""))
                self.customers_table.setItem(row, 2, QTableWidgetItem("✅ فعال" if customer.is_active else "❌ غیرفعال"))
                
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(5, 2, 5, 2)
                
                edit_btn = QPushButton("✏️")
                edit_btn.setToolTip("ویرایش")
                edit_btn.setStyleSheet(self.get_button_style("#FF9800"))
                edit_btn.clicked.connect(lambda checked, c=customer: self.edit_customer(c))
                actions_layout.addWidget(edit_btn)
                
                delete_btn = QPushButton("🗑️")
                delete_btn.setToolTip("حذف")
                delete_btn.setStyleSheet(self.get_button_style("#F44336"))
                delete_btn.clicked.connect(lambda checked, c=customer: self.delete_customer(c))
                actions_layout.addWidget(delete_btn)
                
                self.customers_table.setCellWidget(row, 3, actions_widget)
                
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"❌ خطا در بارگذاری مشتریان:\n{str(e)}")
    
    def add_customer(self):
        """افزودن مشتری جدید"""
        from app.models.financial import Customer
        from PyQt6.QtWidgets import QLineEdit, QCheckBox, QTextEdit, QFormLayout, QDialogButtonBox
        from decimal import Decimal
        
        dialog = QDialog(self)
        dialog.setWindowTitle("➕ افزودن مشتری")
        dialog.setMinimumWidth(500)
        dialog.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        
        code_input = QLineEdit()
        code_input.setPlaceholderText("مثال: CUST-001")
        form.addRow("کد مشتری*:", code_input)
        
        name_input = QLineEdit()
        name_input.setPlaceholderText("نام مشتری")
        form.addRow("نام مشتری*:", name_input)
        
        active_check = QCheckBox("فعال")
        active_check.setChecked(True)
        form.addRow("وضعیت:", active_check)
        
        notes_input = QTextEdit()
        notes_input.setMaximumHeight(60)
        notes_input.setPlaceholderText("یادداشت...")
        form.addRow("یادداشت:", notes_input)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if not code_input.text().strip() or not name_input.text().strip():
                QMessageBox.warning(self, "خطا", "⚠️ لطفاً کد مشتری و نام را وارد کنید")
                return
            
            try:
                customer = Customer(
                    customer_code=code_input.text().strip(),
                    customer_name=name_input.text().strip(),
                    balance=0,
                    is_active=active_check.isChecked(),
                    notes=notes_input.toPlainText().strip()
                )
                
                self.session.add(customer)
                self.session.commit()
                
                QMessageBox.information(self, "موفق", f"✅ مشتری '{customer.customer_name}' با موفقیت اضافه شد")
                self.load_customers()
                self.config_changed.emit()
                
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "خطا", f"❌ خطا در افزودن مشتری:\n{str(e)}")
    
    def edit_customer(self, customer):
        """ویرایش مشتری"""
        from PyQt6.QtWidgets import QLineEdit, QCheckBox, QTextEdit, QFormLayout, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("✏️ ویرایش مشتری")
        dialog.setMinimumWidth(500)
        dialog.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        
        code_input = QLineEdit(customer.customer_code)
        form.addRow("کد مشتری*:", code_input)
        
        name_input = QLineEdit(customer.customer_name or "")
        form.addRow("نام مشتری*:", name_input)
        
        active_check = QCheckBox("فعال")
        active_check.setChecked(customer.is_active)
        form.addRow("وضعیت:", active_check)
        
        notes_input = QTextEdit()
        notes_input.setPlainText(customer.notes or "")
        notes_input.setMaximumHeight(60)
        form.addRow("یادداشت:", notes_input)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if not code_input.text().strip() or not name_input.text().strip():
                QMessageBox.warning(self, "خطا", "⚠️ لطفاً کد مشتری و نام را وارد کنید")
                return
            
            try:
                customer.customer_code = code_input.text().strip()
                customer.customer_name = name_input.text().strip()
                customer.is_active = active_check.isChecked()
                customer.notes = notes_input.toPlainText().strip()
                
                self.session.commit()
                
                QMessageBox.information(self, "موفق", f"✅ مشتری '{customer.customer_name}' با موفقیت ویرایش شد")
                self.load_customers()
                self.config_changed.emit()
                
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "خطا", f"❌ خطا در ویرایش مشتری:\n{str(e)}")
    
    def delete_customer(self, customer):
        """حذف مشتری"""
        reply = QMessageBox.question(
            self,
            "تأیید حذف",
            f"⚠️ آیا مطمئن هستید که می‌خواهید مشتری '{customer.customer_name}' را حذف کنید؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.session.delete(customer)
                self.session.commit()
                
                QMessageBox.information(self, "موفق", f"✅ مشتری '{customer.customer_name}' با موفقیت حذف شد")
                self.load_customers()
                self.config_changed.emit()
                
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "خطا", f"❌ خطا در حذف مشتری:\n{str(e)}")
    
    # ═══════════ متدهای نوع معاملات ═══════════
    
    def load_transaction_types(self):
        try:
            from app.models.financial import TransactionType
            items = self.session.query(TransactionType).order_by(TransactionType.type_code).all()
            self.transaction_types_table.setRowCount(len(items))
            for row, item in enumerate(items):
                self.transaction_types_table.setItem(row, 0, QTableWidgetItem(item.type_code))
                self.transaction_types_table.setItem(row, 1, QTableWidgetItem(item.type_name_fa))
                self.transaction_types_table.setItem(row, 2, QTableWidgetItem(item.type_name_en or ""))
                self.transaction_types_table.setItem(row, 3, QTableWidgetItem(item.affects_inventory or ""))
                self.transaction_types_table.setItem(row, 4, QTableWidgetItem("✅" if item.is_active else "❌"))
        except Exception as e:
            QMessageBox.warning(self, "خطا", f"⚠️ خطا در بارگذاری نوع معاملات:\n{str(e)}")
    
    def add_transaction_type(self):
        """افزودن نوع معامله جدید"""
        from app.models.financial import TransactionType
        from PyQt6.QtWidgets import QLineEdit, QCheckBox, QTextEdit, QFormLayout, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("➕ افزودن نوع معامله")
        dialog.setMinimumWidth(500)
        dialog.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        
        code_input = QLineEdit()
        code_input.setPlaceholderText("مثال: PURCHASE")
        form.addRow("کد نوع معامله*:", code_input)
        
        name_fa_input = QLineEdit()
        name_fa_input.setPlaceholderText("مثال: خرید")
        form.addRow("نام فارسی*:", name_fa_input)
        
        name_en_input = QLineEdit()
        name_en_input.setPlaceholderText("مثال: Purchase")
        form.addRow("نام انگلیسی:", name_en_input)
        
        effect_combo = QComboBox()
        effect_combo.addItems(["increase", "decrease", "neutral"])
        form.addRow("تأثیر:", effect_combo)
        
        active_check = QCheckBox("فعال")
        active_check.setChecked(True)
        form.addRow("وضعیت:", active_check)
        
        notes_input = QTextEdit()
        notes_input.setMaximumHeight(80)
        form.addRow("یادداشت:", notes_input)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if not code_input.text().strip() or not name_fa_input.text().strip():
                QMessageBox.warning(self, "خطا", "⚠️ لطفاً کد و نام فارسی را وارد کنید")
                return
            
            try:
                item = TransactionType(
                    type_code=code_input.text().strip().upper(),
                    type_name_fa=name_fa_input.text().strip(),
                    type_name_en=name_en_input.text().strip(),
                    affects_inventory=effect_combo.currentText(),
                    is_active=active_check.isChecked(),
                    notes=notes_input.toPlainText().strip()
                )
                
                self.session.add(item)
                self.session.commit()
                
                QMessageBox.information(self, "موفق", f"✅ نوع معامله '{item.type_name_fa}' با موفقیت اضافه شد")
                self.load_transaction_types()
                self.config_changed.emit()
                
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "خطا", f"❌ خطا در افزودن نوع معامله:\n{str(e)}")
    
    def load_sku_patterns(self):
        try:
            from app.models.financial import SKUPattern
            items = self.session.query(SKUPattern).all()
            self.sku_patterns_table.setRowCount(len(items))
            for row, item in enumerate(items):
                self.sku_patterns_table.setItem(row, 0, QTableWidgetItem(item.pattern_name))
                self.sku_patterns_table.setItem(row, 1, QTableWidgetItem(item.pattern_format))
                self.sku_patterns_table.setItem(row, 2, QTableWidgetItem(item.pattern_example or ""))
                self.sku_patterns_table.setItem(row, 3, QTableWidgetItem("✅" if item.is_active else "❌"))
        except: pass
    
    def add_sku_pattern(self):
        """افزودن الگوی کد کالا"""
        from app.models.financial import SKUPattern
        from PyQt6.QtWidgets import QLineEdit, QCheckBox, QTextEdit, QFormLayout, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("➕ افزودن الگوی کد کالا")
        dialog.setMinimumWidth(600)
        dialog.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        
        name_input = QLineEdit()
        name_input.setPlaceholderText("مثال: الگوی استاندارد")
        form.addRow("نام الگو*:", name_input)
        
        pattern_input = QLineEdit()
        pattern_input.setPlaceholderText("مثال: {DEPT}-{YEAR}-{SEQ:5}")
        form.addRow("الگو*:", pattern_input)
        
        example_input = QLineEdit()
        example_input.setPlaceholderText("مثال: GC-2025-00001")
        form.addRow("مثال خروجی:", example_input)
        
        active_check = QCheckBox("فعال")
        active_check.setChecked(True)
        form.addRow("وضعیت:", active_check)
        
        notes_input = QTextEdit()
        notes_input.setMaximumHeight(80)
        notes_input.setPlaceholderText("متغیرها: {YEAR}, {MONTH}, {DAY}, {DEPT}, {SEQ:n}, {RANDOM:n}")
        form.addRow("یادداشت:", notes_input)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if not name_input.text().strip() or not pattern_input.text().strip():
                QMessageBox.warning(self, "خطا", "⚠️ لطفاً نام و الگو را وارد کنید")
                return
            
            try:
                item = SKUPattern(
                    pattern_name=name_input.text().strip(),
                    pattern_format=pattern_input.text().strip(),
                    pattern_example=example_input.text().strip(),
                    is_active=active_check.isChecked(),
                    notes=notes_input.toPlainText().strip()
                )
                
                self.session.add(item)
                self.session.commit()
                
                QMessageBox.information(self, "موفق", f"✅ الگوی کد کالا '{item.pattern_name}' با موفقیت اضافه شد")
                self.load_sku_patterns()
                self.config_changed.emit()
                
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "خطا", f"❌ خطا در افزودن الگوی کد کالا:\n{str(e)}")
    
    def load_customer_patterns(self):
        try:
            from app.models.financial import CustomerCodePattern
            items = self.session.query(CustomerCodePattern).all()
            self.customer_patterns_table.setRowCount(len(items))
            for row, item in enumerate(items):
                self.customer_patterns_table.setItem(row, 0, QTableWidgetItem(item.pattern_name))
                self.customer_patterns_table.setItem(row, 1, QTableWidgetItem(item.pattern_template))
                self.customer_patterns_table.setItem(row, 2, QTableWidgetItem(item.example_output or ""))
                self.customer_patterns_table.setItem(row, 3, QTableWidgetItem("✅" if item.is_active else "❌"))
        except: pass
    
    def add_customer_pattern(self):
        """افزودن الگوی کد مشتری"""
        from app.models.financial import CustomerCodePattern
        from PyQt6.QtWidgets import QLineEdit, QCheckBox, QTextEdit, QFormLayout, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("➕ افزودن الگوی کد مشتری")
        dialog.setMinimumWidth(600)
        dialog.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        
        name_input = QLineEdit()
        name_input.setPlaceholderText("مثال: الگوی مشتری استاندارد")
        form.addRow("نام الگو*:", name_input)
        
        pattern_input = QLineEdit()
        pattern_input.setPlaceholderText("مثال: CUST-{YEAR}-{SEQ:4}")
        form.addRow("الگو*:", pattern_input)
        
        example_input = QLineEdit()
        example_input.setPlaceholderText("مثال: CUST-2025-0001")
        form.addRow("مثال خروجی:", example_input)
        
        active_check = QCheckBox("فعال")
        active_check.setChecked(True)
        form.addRow("وضعیت:", active_check)
        
        notes_input = QTextEdit()
        notes_input.setMaximumHeight(80)
        notes_input.setPlaceholderText("متغیرها: {YEAR}, {MONTH}, {DAY}, {SEQ:n}, {RANDOM:n}")
        form.addRow("یادداشت:", notes_input)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if not name_input.text().strip() or not pattern_input.text().strip():
                QMessageBox.warning(self, "خطا", "⚠️ لطفاً نام و الگو را وارد کنید")
                return
            
            try:
                item = CustomerCodePattern(
                    pattern_name=name_input.text().strip(),
                    pattern_template=pattern_input.text().strip(),
                    example_output=example_input.text().strip(),
                    is_active=active_check.isChecked(),
                    notes=notes_input.toPlainText().strip()
                )
                
                self.session.add(item)
                self.session.commit()
                
                QMessageBox.information(self, "موفق", f"✅ الگوی کد مشتری '{item.pattern_name}' با موفقیت اضافه شد")
                self.load_customer_patterns()
                self.config_changed.emit()
                
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "خطا", f"❌ خطا در افزودن الگوی کد مشتری:\n{str(e)}")
    
    def load_currency_rates(self):
        try:
            from app.models.financial import CurrencyRate
            items = self.session.query(CurrencyRate).all()
            self.currency_rates_table.setRowCount(len(items))
            for row, item in enumerate(items):
                self.currency_rates_table.setItem(row, 0, QTableWidgetItem(item.from_currency))
                self.currency_rates_table.setItem(row, 1, QTableWidgetItem(item.to_currency))
                self.currency_rates_table.setItem(row, 2, QTableWidgetItem(str(item.rate)))
                self.currency_rates_table.setItem(row, 3, QTableWidgetItem(str(item.effective_date)))
                self.currency_rates_table.setItem(row, 4, QTableWidgetItem("✅" if item.is_active else "❌"))
        except: pass
    
    def add_currency_rate(self):
        """افزودن نرخ ارز جدید"""
        from app.models.financial import CurrencyRate
        from PyQt6.QtWidgets import QLineEdit, QCheckBox, QTextEdit, QFormLayout, QDialogButtonBox, QDateEdit
        from decimal import Decimal
        
        dialog = QDialog(self)
        dialog.setWindowTitle("➕ افزودن نرخ ارز")
        dialog.setMinimumWidth(500)
        dialog.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        
        from_currency_input = QLineEdit()
        from_currency_input.setPlaceholderText("مثال: USDT")
        form.addRow("ارز مبدأ*:", from_currency_input)
        
        to_currency_input = QLineEdit()
        to_currency_input.setPlaceholderText("مثال: IRT")
        form.addRow("ارز مقصد*:", to_currency_input)
        
        rate_input = QLineEdit()
        rate_input.setPlaceholderText("مثال: 110000")
        form.addRow("نرخ*:", rate_input)
        
        date_input = QDateEdit()
        date_input.setDate(date.today())
        date_input.setCalendarPopup(True)
        form.addRow("تاریخ اعتبار:", date_input)
        
        active_check = QCheckBox("فعال")
        active_check.setChecked(True)
        form.addRow("وضعیت:", active_check)
        
        notes_input = QTextEdit()
        notes_input.setMaximumHeight(80)
        form.addRow("یادداشت:", notes_input)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if not from_currency_input.text().strip() or not to_currency_input.text().strip() or not rate_input.text().strip():
                QMessageBox.warning(self, "خطا", "⚠️ لطفاً ارز مبدأ، مقصد و نرخ را وارد کنید")
                return
            
            try:
                rate_value = Decimal(rate_input.text().strip())
                
                item = CurrencyRate(
                    from_currency=from_currency_input.text().strip().upper(),
                    to_currency=to_currency_input.text().strip().upper(),
                    rate=rate_value,
                    effective_date=date_input.date().toPyDate(),
                    is_active=active_check.isChecked(),
                    notes=notes_input.toPlainText().strip()
                )
                
                self.session.add(item)
                self.session.commit()
                
                QMessageBox.information(self, "موفق", f"✅ نرخ ارز '{item.from_currency}/{item.to_currency}' با موفقیت اضافه شد")
                self.load_currency_rates()
                self.config_changed.emit()
                
            except ValueError:
                QMessageBox.warning(self, "خطا", "⚠️ نرخ باید عدد باشد")
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "خطا", f"❌ خطا در افزودن نرخ ارز:\n{str(e)}")
    
    def load_formulas(self):
        try:
            from app.models.financial import CalculationFormula
            items = self.session.query(CalculationFormula).all()
            self.formulas_table.setRowCount(len(items))
            for row, item in enumerate(items):
                self.formulas_table.setItem(row, 0, QTableWidgetItem(item.formula_name))
                self.formulas_table.setItem(row, 1, QTableWidgetItem(item.formula_code))
                self.formulas_table.setItem(row, 2, QTableWidgetItem(item.formula_expression[:50] + "..."))
                self.formulas_table.setItem(row, 3, QTableWidgetItem("✅" if item.is_active else "❌"))
        except: pass
    
    def add_formula(self):
        """افزودن فرمول جدید"""
        from app.models.financial import CalculationFormula
        from PyQt6.QtWidgets import (QLineEdit, QCheckBox, QTextEdit, QFormLayout, 
                                      QDialogButtonBox, QListWidget, QLabel, QSplitter)
        
        dialog = QDialog(self)
        dialog.setWindowTitle("➕ افزودن فرمول")
        dialog.setMinimumWidth(800)
        dialog.setMinimumHeight(500)
        dialog.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        main_layout = QVBoxLayout(dialog)
        
        # بخش فرم اطلاعات
        form = QFormLayout()
        
        name_input = QLineEdit()
        name_input.setPlaceholderText("مثال: محاسبه سود")
        form.addRow("نام فرمول*:", name_input)
        
        code_input = QLineEdit()
        code_input.setPlaceholderText("مثال: PROFIT_CALC")
        form.addRow("کد فرمول*:", code_input)
        
        main_layout.addLayout(form)
        
        # بخش فرمول و متغیرها
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # سمت راست: فرمول
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.addWidget(QLabel("عبارت فرمول*:"))
        
        expression_input = QTextEdit()
        expression_input.setPlaceholderText("کلیک کنید روی متغیرها برای افزودن...")
        right_layout.addWidget(expression_input)
        
        # یادداشت
        right_layout.addWidget(QLabel("توضیحات:"))
        description_input = QTextEdit()
        description_input.setMaximumHeight(60)
        right_layout.addWidget(description_input)
        
        active_check = QCheckBox("فعال")
        active_check.setChecked(True)
        right_layout.addWidget(active_check)
        
        splitter.addWidget(right_widget)
        
        # سمت چپ: لیست متغیرها
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addWidget(QLabel("💡 متغیرهای قابل استفاده (کلیک کنید):"))
        
        variables_list = QListWidget()
        variables_list.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        variables = [
            "sale_price - قیمت فروش",
            "purchase_price - قیمت خرید",
            "quantity - تعداد",
            "total_amount - مبلغ کل",
            "discount - تخفیف",
            "tax - مالیات",
            "commission - کمیسیون",
            "silver_weight - وزن سیلور",
            "gold_weight - وزن طلا",
            "exchange_rate - نرخ ارز",
            "bonus_amount - مبلغ بونوس",
            "payment_amount - مبلغ پرداخت"
        ]
        variables_list.addItems(variables)
        
        def insert_variable():
            if variables_list.currentItem():
                var_full = variables_list.currentItem().text()
                var_name = var_full.split(" - ")[0]  # فقط نام متغیر
                cursor = expression_input.textCursor()
                cursor.insertText(var_name)
                expression_input.setFocus()
        
        variables_list.itemDoubleClicked.connect(insert_variable)
        left_layout.addWidget(variables_list)
        
        # راهنما
        help_label = QLabel("💡 عملگرها: + - * / ( )")
        help_label.setStyleSheet("color: gray; font-size: 10px;")
        left_layout.addWidget(help_label)
        
        splitter.addWidget(left_widget)
        splitter.setSizes([500, 300])
        
        main_layout.addWidget(splitter)
        
        # دکمه‌ها
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        main_layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if not name_input.text().strip() or not code_input.text().strip() or not expression_input.toPlainText().strip():
                QMessageBox.warning(self, "خطا", "⚠️ لطفاً نام، کد و عبارت فرمول را وارد کنید")
                return
            
            try:
                item = CalculationFormula(
                    formula_name=name_input.text().strip(),
                    formula_code=code_input.text().strip().upper(),
                    formula_expression=expression_input.toPlainText().strip(),
                    is_active=active_check.isChecked(),
                    description=description_input.toPlainText().strip()
                )
                
                self.session.add(item)
                self.session.commit()
                
                QMessageBox.information(self, "موفق", f"✅ فرمول '{item.formula_name}' با موفقیت اضافه شد")
                self.load_formulas()
                self.config_changed.emit()
                
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "خطا", f"❌ خطا در افزودن فرمول:\n{str(e)}")
    
    def refresh_all(self):
        """بروزرسانی همه تب‌ها"""
        try:
            self.load_units()
            self.load_departments()
            self.load_platforms()
            self.load_regions()
            self.load_customers()
            self.load_transaction_types()
            self.load_sku_patterns()
            self.load_customer_patterns()
            self.load_currency_rates()
            self.load_formulas()
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"❌ خطا در بروزرسانی:\n{str(e)}")
    
    def closeEvent(self, event):
        """بستن پنجره"""
        self.session.close()
        event.accept()


# ═══════════════════════════════════════════════════════════
#                   DIALOG CLASSES
# ═══════════════════════════════════════════════════════════

class UnitDialog(QDialog):
    """دیالوگ افزودن/ویرایش واحد"""
    
    def __init__(self, parent=None, unit=None):
        super().__init__(parent)
        self.unit = unit
        self.setWindowTitle("✏️ ویرایش واحد" if unit else "➕ افزودن واحد")
        self.setMinimumWidth(500)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        self.init_ui()
        
        if unit:
            self.load_unit_data()
    
    def init_ui(self):
        """ایجاد رابط کاربری"""
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        # کد
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("مثال: CP")
        form_layout.addRow("کد واحد*:", self.code_input)
        
        # نام فارسی
        self.name_fa_input = QLineEdit()
        self.name_fa_input.setPlaceholderText("مثال: سی پی کالاف")
        form_layout.addRow("نام فارسی*:", self.name_fa_input)
        
        # نام انگلیسی
        self.name_en_input = QLineEdit()
        self.name_en_input.setPlaceholderText("مثال: COD Points")
        form_layout.addRow("نام انگلیسی:", self.name_en_input)
        
        # نماد
        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("مثال: CP یا $")
        form_layout.addRow("نماد:", self.symbol_input)
        
        # دسته
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "currency",
            "game_item",
            "bonus",
            "service"
        ])
        form_layout.addRow("دسته:", self.category_combo)
        
        # ترتیب نمایش
        self.order_spin = QSpinBox()
        self.order_spin.setRange(0, 999)
        form_layout.addRow("ترتیب نمایش:", self.order_spin)
        
        # فعال
        self.active_check = QCheckBox("فعال")
        self.active_check.setChecked(True)
        form_layout.addRow("وضعیت:", self.active_check)
        
        # یادداشت
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setPlaceholderText("یادداشت...")
        form_layout.addRow("یادداشت:", self.notes_input)
        
        layout.addLayout(form_layout)
        
        # دکمه‌ها
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def load_unit_data(self):
        """بارگذاری داده‌های واحد"""
        self.code_input.setText(self.unit.unit_code)
        self.name_fa_input.setText(self.unit.unit_name_fa)
        self.name_en_input.setText(self.unit.unit_name_en or "")
        self.symbol_input.setText(self.unit.unit_symbol or "")
        
        index = self.category_combo.findText(self.unit.unit_category or "currency")
        if index >= 0:
            self.category_combo.setCurrentIndex(index)
        
        self.order_spin.setValue(self.unit.display_order)
        self.active_check.setChecked(self.unit.is_active)
        self.notes_input.setPlainText(self.unit.notes or "")
    
    def validate_and_accept(self):
        """اعتبارسنجی و قبول"""
        if not self.code_input.text().strip():
            QMessageBox.warning(self, "خطا", "⚠️ لطفاً کد واحد را وارد کنید")
            return
        
        if not self.name_fa_input.text().strip():
            QMessageBox.warning(self, "خطا", "⚠️ لطفاً نام فارسی را وارد کنید")
            return
        
        self.accept()


class DepartmentDialog(QDialog):
    """دیالوگ افزودن/ویرایش دپارتمان"""
    
    def __init__(self, parent=None, department=None):
        super().__init__(parent)
        self.department = department
        self.setWindowTitle("✏️ ویرایش دپارتمان" if department else "➕ افزودن دپارتمان")
        self.setMinimumWidth(500)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        self.init_ui()
        
        if department:
            self.load_department_data()
    
    def init_ui(self):
        """ایجاد رابط کاربری"""
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        # کد
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("مثال: GC")
        form_layout.addRow("کد دپارتمان*:", self.code_input)
        
        # نام فارسی
        self.name_fa_input = QLineEdit()
        self.name_fa_input.setPlaceholderText("مثال: گیفت کارت")
        form_layout.addRow("نام فارسی*:", self.name_fa_input)
        
        # نام انگلیسی
        self.name_en_input = QLineEdit()
        self.name_en_input.setPlaceholderText("مثال: Gift Card")
        form_layout.addRow("نام انگلیسی:", self.name_en_input)
        
        # فعال
        self.active_check = QCheckBox("فعال")
        self.active_check.setChecked(True)
        form_layout.addRow("وضعیت:", self.active_check)
        
        # یادداشت
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        form_layout.addRow("یادداشت:", self.notes_input)
        
        layout.addLayout(form_layout)
        
        # دکمه‌ها
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def load_department_data(self):
        """بارگذاری داده‌های دپارتمان"""
        self.code_input.setText(self.department.department_code)
        self.name_fa_input.setText(self.department.department_name_fa)
        self.name_en_input.setText(self.department.department_name_en or "")
        self.active_check.setChecked(self.department.is_active)
        self.notes_input.setPlainText(self.department.notes or "")
    
    def validate_and_accept(self):
        """اعتبارسنجی و قبول"""
        if not self.code_input.text().strip():
            QMessageBox.warning(self, "خطا", "⚠️ لطفاً کد دپارتمان را وارد کنید")
            return
        
        if not self.name_fa_input.text().strip():
            QMessageBox.warning(self, "خطا", "⚠️ لطفاً نام فارسی را وارد کنید")
            return
        
        self.accept()
