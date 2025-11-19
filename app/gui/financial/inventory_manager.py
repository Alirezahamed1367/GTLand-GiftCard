"""
Inventory Manager - مدیریت موجودی انبار
=========================================
این ماژول مدیریت کامل موجودی انبار را انجام می‌دهد:
- ثبت خرید و افزایش موجودی
- ثبت فروش و کاهش موجودی
- گزارش موجودی فعلی
- تاریخچه تراکنش‌ها
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QGroupBox,
    QComboBox, QHeaderView, QTabWidget, QWidget, QSplitter,
    QTextEdit, QLineEdit, QFormLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from app.models.financial import (
    AccountInventory, Purchase, Sale, Platform, Region, Department,
    FinancialSessionLocal
)
from sqlalchemy import func, desc
from decimal import Decimal
from datetime import datetime
from typing import Optional


class InventoryManager(QDialog):
    """
    مدیر موجودی انبار
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📦 مدیریت موجودی انبار")
        self.setMinimumSize(1200, 800)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        self.db = FinancialSessionLocal()
        
        self.setup_ui()
        self.load_inventory()
    
    def setup_ui(self):
        """ایجاد رابط کاربری"""
        layout = QVBoxLayout(self)
        
        # عنوان
        title = QLabel("📦 مدیریت موجودی انبار")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #1976D2; padding: 15px; background: #E3F2FD; border-radius: 5px;")
        layout.addWidget(title)
        
        # فیلترها
        filters_group = self.create_filters()
        layout.addWidget(filters_group)
        
        # Tabs
        tabs = QTabWidget()
        
        # تب موجودی فعلی
        inventory_tab = self.create_inventory_tab()
        tabs.addTab(inventory_tab, "📊 موجودی فعلی")
        
        # تب خریدها
        purchases_tab = self.create_purchases_tab()
        tabs.addTab(purchases_tab, "🛒 تاریخچه خرید")
        
        # تب فروش‌ها
        sales_tab = self.create_sales_tab()
        tabs.addTab(sales_tab, "💰 تاریخچه فروش")
        
        # تب آمار
        stats_tab = self.create_stats_tab()
        tabs.addTab(stats_tab, "📈 آمار و گزارشات")
        
        layout.addWidget(tabs)
        
        # دکمه‌ها
        buttons = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 بروزرسانی")
        refresh_btn.clicked.connect(self.refresh_all)
        buttons.addWidget(refresh_btn)
        
        close_btn = QPushButton("بستن")
        close_btn.clicked.connect(self.close)
        buttons.addWidget(close_btn)
        
        layout.addLayout(buttons)
    
    def create_filters(self) -> QGroupBox:
        """بخش فیلترها"""
        group = QGroupBox("🔍 فیلترها")
        layout = QHBoxLayout()
        
        # پلتفرم
        layout.addWidget(QLabel("پلتفرم:"))
        self.platform_filter = QComboBox()
        self.platform_filter.addItem("همه", None)
        platforms = self.db.query(Platform).filter_by(is_active=True).all()
        for p in platforms:
            self.platform_filter.addItem(p.platform_name_fa, p.platform_id)
        self.platform_filter.currentIndexChanged.connect(self.load_inventory)
        layout.addWidget(self.platform_filter)
        
        # ریجن
        layout.addWidget(QLabel("ریجن:"))
        self.region_filter = QComboBox()
        self.region_filter.addItem("همه", None)
        regions = self.db.query(Region).filter_by(is_active=True).all()
        for r in regions:
            self.region_filter.addItem(r.region_name_fa, r.region_id)
        self.region_filter.currentIndexChanged.connect(self.load_inventory)
        layout.addWidget(self.region_filter)
        
        # دپارتمان
        layout.addWidget(QLabel("دپارتمان:"))
        self.department_filter = QComboBox()
        self.department_filter.addItem("همه", None)
        departments = self.db.query(Department).filter_by(is_active=True).all()
        for d in departments:
            self.department_filter.addItem(d.department_name_fa, d.department_id)
        self.department_filter.currentIndexChanged.connect(self.load_inventory)
        layout.addWidget(self.department_filter)
        
        layout.addStretch()
        group.setLayout(layout)
        return group
    
    def create_inventory_tab(self) -> QWidget:
        """تب موجودی فعلی"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # جدول موجودی
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(8)
        self.inventory_table.setHorizontalHeaderLabels([
            "شناسه", "پلتفرم", "ریجن", "دپارتمان",
            "کالا", "موجودی", "قیمت میانگین", "ارزش کل"
        ])
        self.inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.inventory_table)
        
        return widget
    
    def create_purchases_tab(self) -> QWidget:
        """تب خریدها"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.purchases_table = QTableWidget()
        self.purchases_table.setColumnCount(8)
        self.purchases_table.setHorizontalHeaderLabels([
            "شناسه", "تاریخ", "پلتفرم", "کالا",
            "تعداد", "قیمت واحد", "مبلغ کل", "یادداشت"
        ])
        self.purchases_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.purchases_table)
        
        return widget
    
    def create_sales_tab(self) -> QWidget:
        """تب فروش‌ها"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(9)
        self.sales_table.setHorizontalHeaderLabels([
            "شناسه", "تاریخ", "پلتفرم", "مشتری",
            "کالا", "تعداد", "قیمت واحد", "مبلغ کل", "یادداشت"
        ])
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.sales_table)
        
        return widget
    
    def create_stats_tab(self) -> QWidget:
        """تب آمار"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # کارت‌های آماری
        cards = QHBoxLayout()
        
        self.total_purchases_card = self.create_stat_card("کل خریدها", "0", "#4CAF50")
        cards.addWidget(self.total_purchases_card)
        
        self.total_sales_card = self.create_stat_card("کل فروش‌ها", "0", "#2196F3")
        cards.addWidget(self.total_sales_card)
        
        self.total_inventory_card = self.create_stat_card("ارزش موجودی", "0", "#FF9800")
        cards.addWidget(self.total_inventory_card)
        
        self.profit_card = self.create_stat_card("سود خالص", "0", "#9C27B0")
        cards.addWidget(self.profit_card)
        
        layout.addLayout(cards)
        
        # جزئیات بیشتر
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        layout.addWidget(self.stats_text)
        
        return widget
    
    def create_stat_card(self, title: str, value: str, color: str) -> QGroupBox:
        """ایجاد کارت آماری"""
        card = QGroupBox()
        card.setStyleSheet(f"""
            QGroupBox {{
                background: {color};
                border-radius: 10px;
                padding: 20px;
            }}
        """)
        
        layout = QVBoxLayout()
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: white; font-size: 14px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)
        
        card.setLayout(layout)
        return card
    
    def load_inventory(self):
        """بارگذاری موجودی"""
        try:
            query = self.db.query(AccountInventory)
            
            # اعمال فیلترها
            platform_id = self.platform_filter.currentData()
            if platform_id:
                query = query.filter_by(platform_id=platform_id)
            
            region_id = self.region_filter.currentData()
            if region_id:
                query = query.filter_by(region_id=region_id)
            
            department_id = self.department_filter.currentData()
            if department_id:
                query = query.filter_by(department_id=department_id)
            
            items = query.all()
            
            self.inventory_table.setRowCount(len(items))
            
            for row, item in enumerate(items):
                self.inventory_table.setItem(row, 0, QTableWidgetItem(str(item.inventory_id)))
                self.inventory_table.setItem(row, 1, QTableWidgetItem(
                    item.platform.platform_name_fa if item.platform else "-"
                ))
                self.inventory_table.setItem(row, 2, QTableWidgetItem(
                    item.region.region_name_fa if item.region else "-"
                ))
                self.inventory_table.setItem(row, 3, QTableWidgetItem(
                    item.department.department_name_fa if item.department else "-"
                ))
                self.inventory_table.setItem(row, 4, QTableWidgetItem(item.item_description or "-"))
                self.inventory_table.setItem(row, 5, QTableWidgetItem(f"{item.current_quantity:,.2f}"))
                self.inventory_table.setItem(row, 6, QTableWidgetItem(f"{item.average_cost:,.2f}"))
                
                total_value = item.current_quantity * item.average_cost
                self.inventory_table.setItem(row, 7, QTableWidgetItem(f"{total_value:,.2f}"))
        
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"❌ خطا در بارگذاری موجودی:\n{str(e)}")
    
    def load_purchases(self):
        """بارگذاری خریدها"""
        try:
            query = self.db.query(Purchase).order_by(desc(Purchase.transaction_date))
            
            # اعمال فیلترها
            platform_id = self.platform_filter.currentData()
            if platform_id:
                query = query.filter_by(platform_id=platform_id)
            
            region_id = self.region_filter.currentData()
            if region_id:
                query = query.filter_by(region_id=region_id)
            
            department_id = self.department_filter.currentData()
            if department_id:
                query = query.filter_by(department_id=department_id)
            
            purchases = query.limit(100).all()
            
            self.purchases_table.setRowCount(len(purchases))
            
            for row, p in enumerate(purchases):
                self.purchases_table.setItem(row, 0, QTableWidgetItem(str(p.purchase_id)))
                self.purchases_table.setItem(row, 1, QTableWidgetItem(
                    p.transaction_date.strftime("%Y-%m-%d") if p.transaction_date else "-"
                ))
                self.purchases_table.setItem(row, 2, QTableWidgetItem(
                    p.platform.platform_name_fa if p.platform else "-"
                ))
                self.purchases_table.setItem(row, 3, QTableWidgetItem(p.item_description or "-"))
                self.purchases_table.setItem(row, 4, QTableWidgetItem(f"{p.quantity:,.2f}"))
                self.purchases_table.setItem(row, 5, QTableWidgetItem(f"{p.unit_price:,.2f}"))
                self.purchases_table.setItem(row, 6, QTableWidgetItem(f"{p.total_amount:,.2f}"))
                self.purchases_table.setItem(row, 7, QTableWidgetItem(p.notes or "-"))
        
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"❌ خطا در بارگذاری خریدها:\n{str(e)}")
    
    def load_sales(self):
        """بارگذاری فروش‌ها"""
        try:
            query = self.db.query(Sale).order_by(desc(Sale.transaction_date))
            
            # اعمال فیلترها
            platform_id = self.platform_filter.currentData()
            if platform_id:
                query = query.filter_by(platform_id=platform_id)
            
            region_id = self.region_filter.currentData()
            if region_id:
                query = query.filter_by(region_id=region_id)
            
            department_id = self.department_filter.currentData()
            if department_id:
                query = query.filter_by(department_id=department_id)
            
            sales = query.limit(100).all()
            
            self.sales_table.setRowCount(len(sales))
            
            for row, s in enumerate(sales):
                self.sales_table.setItem(row, 0, QTableWidgetItem(str(s.sale_id)))
                self.sales_table.setItem(row, 1, QTableWidgetItem(
                    s.transaction_date.strftime("%Y-%m-%d") if s.transaction_date else "-"
                ))
                self.sales_table.setItem(row, 2, QTableWidgetItem(
                    s.platform.platform_name_fa if s.platform else "-"
                ))
                self.sales_table.setItem(row, 3, QTableWidgetItem(
                    s.customer.customer_name if s.customer else "-"
                ))
                self.sales_table.setItem(row, 4, QTableWidgetItem(s.item_description or "-"))
                self.sales_table.setItem(row, 5, QTableWidgetItem(f"{s.quantity:,.2f}"))
                self.sales_table.setItem(row, 6, QTableWidgetItem(f"{s.unit_price:,.2f}"))
                self.sales_table.setItem(row, 7, QTableWidgetItem(f"{s.total_amount:,.2f}"))
                self.sales_table.setItem(row, 8, QTableWidgetItem(s.notes or "-"))
        
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"❌ خطا در بارگذاری فروش‌ها:\n{str(e)}")
    
    def load_stats(self):
        """بارگذاری آمار"""
        try:
            # محاسبه آمار
            total_purchases = self.db.query(func.sum(Purchase.total_amount)).scalar() or 0
            total_sales = self.db.query(func.sum(Sale.total_amount)).scalar() or 0
            
            # ارزش موجودی
            inventory_items = self.db.query(AccountInventory).all()
            total_inventory_value = sum(
                item.current_quantity * item.average_cost for item in inventory_items
            )
            
            profit = total_sales - total_purchases
            
            # بروزرسانی کارت‌ها
            self.update_stat_card(self.total_purchases_card, f"${total_purchases:,.2f}")
            self.update_stat_card(self.total_sales_card, f"${total_sales:,.2f}")
            self.update_stat_card(self.total_inventory_card, f"${total_inventory_value:,.2f}")
            self.update_stat_card(self.profit_card, f"${profit:,.2f}")
            
            # جزئیات
            details = f"""
📊 گزارش کامل آماری

💰 مالی:
  • کل خریدها: ${total_purchases:,.2f}
  • کل فروش‌ها: ${total_sales:,.2f}
  • سود خالص: ${profit:,.2f}
  • حاشیه سود: {(profit/total_sales*100) if total_sales > 0 else 0:.2f}%

📦 موجودی:
  • تعداد اقلام: {len(inventory_items)}
  • ارزش کل: ${total_inventory_value:,.2f}

📈 تراکنش‌ها:
  • تعداد خریدها: {self.db.query(Purchase).count()}
  • تعداد فروش‌ها: {self.db.query(Sale).count()}
"""
            self.stats_text.setText(details)
        
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"❌ خطا در بارگذاری آمار:\n{str(e)}")
    
    def update_stat_card(self, card: QGroupBox, value: str):
        """بروزرسانی کارت آماری"""
        value_label = card.findChild(QLabel, "value")
        if value_label:
            value_label.setText(value)
    
    def refresh_all(self):
        """بروزرسانی همه"""
        self.load_inventory()
        self.load_purchases()
        self.load_sales()
        self.load_stats()
    
    def showEvent(self, event):
        """هنگام نمایش"""
        super().showEvent(event)
        self.refresh_all()
    
    def closeEvent(self, event):
        """بستن دیالوگ"""
        self.db.close()
        event.accept()
