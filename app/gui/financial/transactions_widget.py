"""
مدیریت معاملات - Transactions Widget
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton,
    QLineEdit, QDateEdit, QHeaderView
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

from app.models.financial import FinancialSessionLocal, Sale as Transaction
from app.core.logger import app_logger


class TransactionsWidget(QWidget):
    """ویجت مدیریت معاملات"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = app_logger
        self.init_ui()
        self.load_transactions()
    
    def init_ui(self):
        """راه‌اندازی رابط کاربری"""
        layout = QVBoxLayout(self)
        
        title = QLabel("🛒 معاملات")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #2196F3; padding: 10px;")
        layout.addWidget(title)
        
        # فیلترها
        filter_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 جستجو...")
        filter_layout.addWidget(self.search_input)
        
        refresh_btn = QPushButton("🔄 بروزرسانی")
        refresh_btn.clicked.connect(self.load_transactions)
        filter_layout.addWidget(refresh_btn)
        
        layout.addLayout(filter_layout)
        
        # جدول
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "کد معامله", "تاریخ", "آکانت", "مشتری",
            "محصول", "مقدار", "ریت", "قیمت", "سود", "وضعیت"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        self.stats_label = QLabel()
        layout.addWidget(self.stats_label)
    
    def load_transactions(self):
        """بارگذاری معاملات"""
        try:
            db = FinancialSessionLocal()
            transactions = db.query(Transaction).order_by(Transaction.transaction_date.desc()).limit(100).all()
            db.close()
            
            self.table.setRowCount(len(transactions))
            for row, t in enumerate(transactions):
                self.table.setItem(row, 0, QTableWidgetItem(t.transaction_code))
                self.table.setItem(row, 1, QTableWidgetItem(str(t.transaction_date)))
                self.table.setItem(row, 2, QTableWidgetItem(t.account.label if t.account else ""))
                self.table.setItem(row, 3, QTableWidgetItem(t.customer.name if t.customer else ""))
                self.table.setItem(row, 4, QTableWidgetItem(t.product_type))
                self.table.setItem(row, 5, QTableWidgetItem(f"{t.amount_sold:,.2f}"))
                self.table.setItem(row, 6, QTableWidgetItem(f"{t.sale_rate:,.2f}"))
                self.table.setItem(row, 7, QTableWidgetItem(f"{t.sale_price_usdt:,.2f} USDT"))
                
                profit_item = QTableWidgetItem(f"{t.profit_usdt:,.2f}")
                profit_item.setForeground(Qt.GlobalColor.darkGreen if t.profit_usdt >= 0 else Qt.GlobalColor.red)
                self.table.setItem(row, 8, profit_item)
                
                self.table.setItem(row, 9, QTableWidgetItem(t.status))
            
            self.stats_label.setText(f"تعداد: {len(transactions):,} معامله (100 آخرین)")
            
        except Exception as e:
            self.logger.error(f"خطا در بارگذاری معاملات: {str(e)}")
