"""
پنجره اصلی سیستم مالی - Financial Window
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from app.core.logger import app_logger
from app.gui.financial.dashboard_widget import FinancialDashboardWidget
from app.gui.financial.accounts_widget import AccountsManagementWidget
from app.gui.financial.transactions_widget import TransactionsWidget
from app.gui.financial.customers_widget import CustomersWidget
from app.gui.financial.reports_widget import FinancialReportsWidget
from app.utils.ui_constants import COLOR_PRIMARY, FONT_SIZE_TITLE


class FinancialWindow(QMainWindow):
    """
    پنجره اصلی سیستم مالی
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = app_logger
        self.init_ui()
    
    def init_ui(self):
        """راه‌اندازی رابط کاربری"""
        self.setWindowTitle("GT-Land Financial - سیستم مالی")
        self.setGeometry(100, 100, 1400, 900)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        # ویجت مرکزی
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # لی‌اوت اصلی
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # عنوان
        title_label = QLabel("💰 سیستم مالی GT-Land")
        title_font = QFont("Segoe UI", FONT_SIZE_TITLE, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"color: {COLOR_PRIMARY}; padding: 15px;")
        main_layout.addWidget(title_label)
        
        # تب‌ها
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #e0e0e0;
                border-radius: 5px;
                background: white;
            }
            QTabBar::tab {
                background: #f5f5f5;
                border: 1px solid #e0e0e0;
                padding: 12px 25px;
                margin: 2px;
                border-radius: 5px;
                font-size: 11pt;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #4CAF50;
                color: white;
            }
            QTabBar::tab:hover {
                background: #81C784;
            }
        """)
        
        # تب داشبورد
        self.dashboard_widget = FinancialDashboardWidget()
        self.tabs.addTab(self.dashboard_widget, "📊 داشبورد")
        
        # تب آکانت‌ها
        self.accounts_widget = AccountsManagementWidget()
        self.tabs.addTab(self.accounts_widget, "💳 آکانت‌ها")
        
        # تب معاملات
        self.transactions_widget = TransactionsWidget()
        self.tabs.addTab(self.transactions_widget, "🛒 معاملات")
        
        # تب مشتریان
        self.customers_widget = CustomersWidget()
        self.tabs.addTab(self.customers_widget, "👥 مشتریان")
        
        # تب گزارشات
        self.reports_widget = FinancialReportsWidget()
        self.tabs.addTab(self.reports_widget, "📈 گزارشات")
        
        main_layout.addWidget(self.tabs)
        
        # نوار وضعیت
        self.statusBar().showMessage("✅ سیستم مالی آماده")
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background: #f5f5f5;
                color: #333;
                font-size: 10pt;
                padding: 5px;
            }
        """)
    
    def refresh_all(self):
        """بروزرسانی همه تب‌ها"""
        self.dashboard_widget.load_data()
        self.accounts_widget.load_accounts()
        self.transactions_widget.load_transactions()
        self.customers_widget.load_customers()
        self.reports_widget.load_reports()
