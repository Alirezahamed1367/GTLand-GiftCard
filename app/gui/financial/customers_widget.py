"""
مدیریت مشتریان - Customers Widget
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton,
    QLineEdit, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from app.models.financial import FinancialSessionLocal, Customer
from app.core.logger import app_logger


class CustomersWidget(QWidget):
    """ویجت مدیریت مشتریان"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = app_logger
        self.init_ui()
        self.load_customers()
    
    def init_ui(self):
        """راه‌اندازی رابط کاربری"""
        layout = QVBoxLayout(self)
        
        title = QLabel("👥 مشتریان")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #2196F3; padding: 10px;")
        layout.addWidget(title)
        
        # فیلترها
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 جستجو...")
        self.search_input.textChanged.connect(self.filter_customers)
        filter_layout.addWidget(self.search_input)
        
        refresh_btn = QPushButton("🔄 بروزرسانی")
        refresh_btn.clicked.connect(self.load_customers)
        filter_layout.addWidget(refresh_btn)
        layout.addLayout(filter_layout)
        
        # جدول
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "کد مشتری", "نام", "نوع", "تعداد خرید",
            "مجموع خرید", "مانده حساب", "آخرین خرید", "وضعیت"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        self.stats_label = QLabel()
        layout.addWidget(self.stats_label)
    
    def load_customers(self):
        """بارگذاری مشتریان"""
        try:
            db = FinancialSessionLocal()
            self.all_customers = db.query(Customer).all()
            db.close()
            
            self.display_customers(self.all_customers)
            
        except Exception as e:
            self.logger.error(f"خطا در بارگذاری مشتریان: {str(e)}")
    
    def display_customers(self, customers):
        """نمایش مشتریان"""
        self.table.setRowCount(len(customers))
        for row, c in enumerate(customers):
            self.table.setItem(row, 0, QTableWidgetItem(c.customer_code))
            self.table.setItem(row, 1, QTableWidgetItem(c.name))
            self.table.setItem(row, 2, QTableWidgetItem(c.customer_type))
            self.table.setItem(row, 3, QTableWidgetItem(str(c.total_purchases_count)))
            self.table.setItem(row, 4, QTableWidgetItem(f"{c.total_purchases_usdt:,.2f} USDT"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{c.account_balance_usdt:,.2f} USDT"))
            self.table.setItem(row, 6, QTableWidgetItem(str(c.last_purchase_at) if c.last_purchase_at else "-"))
            self.table.setItem(row, 7, QTableWidgetItem("فعال" if c.is_active else "غیرفعال"))
        
        self.stats_label.setText(f"تعداد: {len(customers):,} مشتری")
    
    def filter_customers(self):
        """فیلتر مشتریان"""
        if not hasattr(self, 'all_customers'):
            return
        search_text = self.search_input.text().lower()
        filtered = [c for c in self.all_customers if search_text in c.name.lower()]
        self.display_customers(filtered)
