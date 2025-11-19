"""
داشبورد مالی - Financial Dashboard Widget
نمایش خلاصه آمار و اطلاعات کلیدی
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QGridLayout, QPushButton
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from decimal import Decimal

from app.models.financial import (
    FinancialSessionLocal, 
    Department, 
    AccountInventory,  # به جای Account
    Customer, 
    Sale,  # به جای Transaction
    Purchase
)
from app.core.financial import FinancialCalculator
from app.core.logger import app_logger


class StatCard(QFrame):
    """کارت نمایش آمار"""
    
    def __init__(self, title, value, subtitle="", color="#2196F3"):
        super().__init__()
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setStyleSheet(f"""
            QFrame {{
                background: white;
                border-left: 5px solid {color};
                border-radius: 8px;
                padding: 15px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        
        # عنوان
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12pt; color: #666; font-weight: bold;")
        layout.addWidget(title_label)
        
        # مقدار
        value_label = QLabel(str(value))
        value_label.setStyleSheet(f"font-size: 24pt; color: {color}; font-weight: bold;")
        layout.addWidget(value_label)
        
        # زیرنویس
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet("font-size: 10pt; color: #999;")
            layout.addWidget(subtitle_label)


class FinancialDashboardWidget(QWidget):
    """
    ویجت داشبورد مالی
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = app_logger
        self.calculator = FinancialCalculator()
        self.init_ui()
        self.load_data()
        
        # بروزرسانی خودکار هر 30 ثانیه
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_data)
        self.timer.start(30000)
    
    def init_ui(self):
        """راه‌اندازی رابط کاربری"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # عنوان
        title = QLabel("📊 داشبورد مالی")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #2196F3; padding: 10px;")
        layout.addWidget(title)
        
        # کارت‌های آمار
        self.stats_grid = QGridLayout()
        self.stats_grid.setSpacing(15)
        layout.addLayout(self.stats_grid)
        
        # دکمه بروزرسانی
        refresh_btn = QPushButton("🔄 بروزرسانی")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #45a049;
            }
        """)
        refresh_btn.clicked.connect(self.load_data)
        layout.addWidget(refresh_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout.addStretch()
    
    def load_data(self):
        """بارگذاری داده‌ها"""
        try:
            db = FinancialSessionLocal()
            
            # تعداد آکانت‌ها
            total_accounts = db.query(Account).count()
            active_accounts = db.query(Account).filter_by(status='active').count()
            
            # تعداد مشتریان
            total_customers = db.query(Customer).count()
            
            # تعداد معاملات
            total_transactions = db.query(Transaction).count()
            
            # مجموع فروش
            total_sales = db.query(Transaction).filter_by(status='completed').all()
            total_sales_usdt = sum(t.sale_price_usdt for t in total_sales)
            
            # مجموع خرید آکانت‌ها
            accounts = db.query(Account).all()
            total_purchase = sum(a.purchase_price_usdt for a in accounts)
            
            # سود کل
            total_profit = total_sales_usdt - total_purchase
            
            db.close()
            
            # پاک کردن کارت‌های قبلی
            for i in reversed(range(self.stats_grid.count())):
                self.stats_grid.itemAt(i).widget().setParent(None)
            
            # کارت‌های جدید
            row, col = 0, 0
            
            # آکانت‌ها
            card = StatCard(
                "آکانت‌ها",
                f"{total_accounts:,}",
                f"فعال: {active_accounts:,}",
                "#2196F3"
            )
            self.stats_grid.addWidget(card, row, col)
            col += 1
            
            # مشتریان
            card = StatCard(
                "مشتریان",
                f"{total_customers:,}",
                "کل مشتریان",
                "#FF9800"
            )
            self.stats_grid.addWidget(card, row, col)
            col += 1
            
            # معاملات
            card = StatCard(
                "معاملات",
                f"{total_transactions:,}",
                "کل معاملات",
                "#9C27B0"
            )
            self.stats_grid.addWidget(card, row, col)
            
            # ردیف دوم
            row, col = 1, 0
            
            # مجموع فروش
            card = StatCard(
                "مجموع فروش",
                f"{total_sales_usdt:,.2f} USDT",
                f"{total_sales_usdt * 110000:,.0f} تومان",
                "#4CAF50"
            )
            self.stats_grid.addWidget(card, row, col)
            col += 1
            
            # مجموع خرید
            card = StatCard(
                "مجموع خرید",
                f"{total_purchase:,.2f} USDT",
                "هزینه آکانت‌ها",
                "#F44336"
            )
            self.stats_grid.addWidget(card, row, col)
            col += 1
            
            # سود کل
            profit_color = "#4CAF50" if total_profit >= 0 else "#F44336"
            card = StatCard(
                "سود کل",
                f"{total_profit:,.2f} USDT",
                f"حاشیه: {(total_profit/total_purchase*100):.1f}%" if total_purchase > 0 else "",
                profit_color
            )
            self.stats_grid.addWidget(card, row, col)
            
            self.logger.info("داشبورد مالی بروزرسانی شد")
            
        except Exception as e:
            self.logger.error(f"خطا در بارگذاری داشبورد: {str(e)}")
