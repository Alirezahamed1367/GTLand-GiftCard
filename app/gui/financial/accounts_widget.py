"""
مدیریت آکانت‌ها - Accounts Management Widget
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton,
    QLineEdit, QComboBox, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from app.models.financial import FinancialSessionLocal, AccountInventory as Account, Department
from app.core.logger import app_logger
from sqlalchemy.orm import joinedload


class AccountsManagementWidget(QWidget):
    """
    ویجت مدیریت آکانت‌ها
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = app_logger
        self.init_ui()
        self.load_accounts()
    
    def init_ui(self):
        """راه‌اندازی رابط کاربری"""
        layout = QVBoxLayout(self)
        
        # عنوان
        title = QLabel("💳 مدیریت آکانت‌ها")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #2196F3; padding: 10px;")
        layout.addWidget(title)
        
        # فیلترها
        filter_layout = QHBoxLayout()
        
        # جستجو
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("جستجو (Label, کد کالا، ...)")
        self.search_input.textChanged.connect(self.filter_accounts)
        filter_layout.addWidget(self.search_input)
        
        # فیلتر دپارتمان
        self.dept_filter = QComboBox()
        self.dept_filter.addItem("همه دپارتمان‌ها", None)
        self.dept_filter.currentIndexChanged.connect(self.filter_accounts)
        filter_layout.addWidget(self.dept_filter)
        
        # فیلتر وضعیت
        self.status_filter = QComboBox()
        self.status_filter.addItems(["همه", "active", "depleted", "archived"])
        self.status_filter.currentIndexChanged.connect(self.filter_accounts)
        filter_layout.addWidget(self.status_filter)
        
        # دکمه بروزرسانی
        refresh_btn = QPushButton("بروزرسانی")
        refresh_btn.clicked.connect(self.load_accounts)
        filter_layout.addWidget(refresh_btn)
        
        layout.addLayout(filter_layout)
        
        # جدول آکانت‌ها
        self.table = QTableWidget()
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels([
            "ID", "دپارتمان", "Label", "کد کالا", "موجودی اولیه",
            "موجودی فعلی", "قیمت خرید", "مجموع فروش", "سود/زیان",
            "تعداد فروش", "وضعیت", "تاریخ خرید"
        ])
        
        # تنظیمات جدول
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        
        layout.addWidget(self.table)
        
        # آمار
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("font-size: 11pt; color: #666; padding: 10px;")
        layout.addWidget(self.stats_label)
    
    def load_accounts(self):
        """بارگذاری آکانت‌ها"""
        try:
            db = FinancialSessionLocal()
            
            # بارگذاری دپارتمان‌ها
            departments = db.query(Department).all()
            self.dept_filter.clear()
            self.dept_filter.addItem("همه دپارتمان‌ها", None)
            for dept in departments:
                self.dept_filter.addItem(dept.name, dept.id)
            
            # بارگذاری آکانت‌ها
            accounts = db.query(Account).options(joinedload(Account.department)).all()
            
            # تبدیل به dict
            self.all_accounts_data = []
            for acc in accounts:
                self.all_accounts_data.append({
                    'id': acc.id,
                    'department_code': acc.department.code if acc.department else "",
                    'label': acc.label,
                    'product_code': acc.product_code,
                    'initial_balance': float(acc.initial_balance),
                    'balance_unit': acc.balance_unit,
                    'current_balance': float(acc.current_balance),
                    'purchase_price_usdt': float(acc.purchase_price_usdt),
                    'total_sales_amount_usdt': float(acc.total_sales_amount_usdt),
                    'total_profit_usdt': float(acc.total_profit_usdt),
                    'total_sales_count': acc.total_sales_count,
                    'status': acc.status,
                    'purchase_date': str(acc.purchase_date),
                    'department_id': acc.department_id
                })
            
            db.close()
            self.display_accounts(self.all_accounts_data)
            
        except Exception as e:
            self.logger.error(f"خطا در بارگذاری آکانت‌ها: {str(e)}")
    
    def display_accounts(self, accounts):
        """نمایش آکانت‌ها"""
        self.table.setRowCount(len(accounts))
        
        for row, acc in enumerate(accounts):
            self.table.setItem(row, 0, QTableWidgetItem(str(acc['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(acc['department_code']))
            self.table.setItem(row, 2, QTableWidgetItem(acc['label']))
            self.table.setItem(row, 3, QTableWidgetItem(acc['product_code']))
            self.table.setItem(row, 4, QTableWidgetItem(f"{acc['initial_balance']:,.2f} {acc['balance_unit']}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{acc['current_balance']:,.2f} {acc['balance_unit']}"))
            self.table.setItem(row, 6, QTableWidgetItem(f"{acc['purchase_price_usdt']:,.2f} USDT"))
            self.table.setItem(row, 7, QTableWidgetItem(f"{acc['total_sales_amount_usdt']:,.2f} USDT"))
            
            profit_item = QTableWidgetItem(f"{acc['total_profit_usdt']:,.2f} USDT")
            if acc['total_profit_usdt'] >= 0:
                profit_item.setForeground(Qt.GlobalColor.darkGreen)
            else:
                profit_item.setForeground(Qt.GlobalColor.red)
            self.table.setItem(row, 8, profit_item)
            
            self.table.setItem(row, 9, QTableWidgetItem(str(acc['total_sales_count'])))
            self.table.setItem(row, 10, QTableWidgetItem(acc['status']))
            self.table.setItem(row, 11, QTableWidgetItem(acc['purchase_date']))
        
        # آمار
        total = len(accounts)
        active = len([a for a in accounts if a['status'] == 'active'])
        total_value = sum(a['purchase_price_usdt'] for a in accounts)
        self.stats_label.setText(
            f"کل: {total:,} آکانت | فعال: {active:,} | "
            f"ارزش کل: {total_value:,.2f} USDT"
        )
    
    def filter_accounts(self):
        """فیلتر آکانت‌ها"""
        if not hasattr(self, 'all_accounts_data'):
            return
        
        search_text = self.search_input.text().lower()
        dept_id = self.dept_filter.currentData()
        status = self.status_filter.currentText()
        
        filtered = self.all_accounts_data
        
        if search_text:
            filtered = [a for a in filtered if 
                       search_text in a['label'].lower() or 
                       search_text in a['product_code'].lower()]
        
        if dept_id:
            filtered = [a for a in filtered if a['department_id'] == dept_id]
        
        if status != "همه":
            filtered = [a for a in filtered if a['status'] == status]
        
        self.display_accounts(filtered)
