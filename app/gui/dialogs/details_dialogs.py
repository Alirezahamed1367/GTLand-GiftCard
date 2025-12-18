"""
Dialogs برای نمایش جزئیات خرید و فروش
Purchase Details & Sales Details Dialogs
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QLabel, QPushButton, QHeaderView,
    QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime
from typing import List

from app.models.financial import Account, AccountGold, AccountSilver, Sale
from app.models.financial import get_financial_session


class PurchaseDetailsDialog(QDialog):
    """
    دیالوگ جزئیات خریدهای یک آکانت
    
    نمایش:
    - تمام خریدهای Gold
    - تمام بونوس‌های Silver
    - جمع کل و میانگین نرخ
    """
    
    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        self.label = label
        self.session: Session = get_financial_session()
        self.account: Account = None
        
        self.setWindowTitle(f"📦 جزئیات خرید - {label}")
        self.setMinimumSize(900, 600)
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """ساخت رابط کاربری"""
        layout = QVBoxLayout(self)
        
        # === Header ===
        header = QLabel(f"📦 جزئیات خرید برای آکانت: {self.label}")
        header.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # === Account Info ===
        self.info_group = QGroupBox("اطلاعات آکانت")
        info_layout = QGridLayout()
        
        self.lbl_email = QLabel()
        self.lbl_supplier = QLabel()
        self.lbl_status = QLabel()
        
        info_layout.addWidget(QLabel("📧 Email:"), 0, 0)
        info_layout.addWidget(self.lbl_email, 0, 1)
        info_layout.addWidget(QLabel("🏪 Supplier:"), 0, 2)
        info_layout.addWidget(self.lbl_supplier, 0, 3)
        info_layout.addWidget(QLabel("📊 Status:"), 1, 0)
        info_layout.addWidget(self.lbl_status, 1, 1, 1, 3)
        
        self.info_group.setLayout(info_layout)
        layout.addWidget(self.info_group)
        
        # === Gold Purchases Table ===
        gold_label = QLabel("🪙 خریدهای Gold")
        gold_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        layout.addWidget(gold_label)
        
        self.gold_table = QTableWidget()
        self.gold_table.setColumnCount(5)
        self.gold_table.setHorizontalHeaderLabels([
            "تاریخ خرید", "مقدار Gold", "نرخ خرید", "هزینه کل", "سود پرسنل"
        ])
        self.gold_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.gold_table.setAlternatingRowColors(True)
        self.gold_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.gold_table)
        
        # === Silver Bonuses Table ===
        silver_label = QLabel("⭐ بونوس‌های Silver")
        silver_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        layout.addWidget(silver_label)
        
        self.silver_table = QTableWidget()
        self.silver_table.setColumnCount(2)
        self.silver_table.setHorizontalHeaderLabels([
            "تاریخ دریافت", "مقدار Silver (رایگان)"
        ])
        self.silver_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.silver_table.setAlternatingRowColors(True)
        self.silver_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.silver_table)
        
        # === Summary ===
        self.summary_group = QGroupBox("📊 خلاصه")
        summary_layout = QGridLayout()
        
        self.lbl_total_gold = QLabel()
        self.lbl_total_cost = QLabel()
        self.lbl_avg_rate = QLabel()
        self.lbl_total_silver = QLabel()
        
        summary_layout.addWidget(QLabel("💰 کل Gold خریداری شده:"), 0, 0)
        summary_layout.addWidget(self.lbl_total_gold, 0, 1)
        summary_layout.addWidget(QLabel("💵 کل هزینه:"), 0, 2)
        summary_layout.addWidget(self.lbl_total_cost, 0, 3)
        summary_layout.addWidget(QLabel("📈 میانگین نرخ:"), 1, 0)
        summary_layout.addWidget(self.lbl_avg_rate, 1, 1)
        summary_layout.addWidget(QLabel("⭐ کل Silver بونوس:"), 1, 2)
        summary_layout.addWidget(self.lbl_total_silver, 1, 3)
        
        self.summary_group.setLayout(summary_layout)
        layout.addWidget(self.summary_group)
        
        # === Buttons ===
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_close = QPushButton("بستن")
        btn_close.clicked.connect(self.close)
        btn_layout.addWidget(btn_close)
        
        layout.addLayout(btn_layout)
    
    def load_data(self):
        """بارگذاری داده‌ها از دیتابیس"""
        # بارگذاری Account
        self.account = self.session.query(Account).filter_by(label=self.label).first()
        
        if not self.account:
            self.lbl_email.setText("❌ آکانت یافت نشد")
            return
        
        # === Account Info ===
        self.lbl_email.setText(self.account.email or "N/A")
        self.lbl_supplier.setText(self.account.supplier or "N/A")
        self.lbl_status.setText(self.account.status or "N/A")
        
        # === Gold Purchases ===
        gold_purchases = self.session.query(AccountGold).filter_by(label=self.label).all()
        self.gold_table.setRowCount(len(gold_purchases))
        
        total_gold = Decimal('0')
        total_cost = Decimal('0')
        
        for row, purchase in enumerate(gold_purchases):
            # تاریخ
            date_str = purchase.purchase_date.strftime("%Y-%m-%d") if purchase.purchase_date else "N/A"
            self.gold_table.setItem(row, 0, QTableWidgetItem(date_str))
            
            # مقدار
            qty = float(purchase.gold_quantity) if purchase.gold_quantity else 0
            self.gold_table.setItem(row, 1, QTableWidgetItem(f"{qty:,.2f}"))
            
            # نرخ
            rate = float(purchase.purchase_rate) if purchase.purchase_rate else 0
            self.gold_table.setItem(row, 2, QTableWidgetItem(f"${rate:,.2f}"))
            
            # هزینه کل
            cost = float(purchase.purchase_cost) if purchase.purchase_cost else 0
            self.gold_table.setItem(row, 3, QTableWidgetItem(f"${cost:,.2f}"))
            
            # سود پرسنل
            staff_profit = float(purchase.staff_profit) if purchase.staff_profit else 0
            self.gold_table.setItem(row, 4, QTableWidgetItem(f"${staff_profit:,.2f}" if staff_profit else "N/A"))
            
            total_gold += purchase.gold_quantity or 0
            total_cost += purchase.purchase_cost or 0
        
        # === Silver Bonuses ===
        silver_bonuses = self.session.query(AccountSilver).filter_by(label=self.label).all()
        self.silver_table.setRowCount(len(silver_bonuses))
        
        total_silver = Decimal('0')
        
        for row, bonus in enumerate(silver_bonuses):
            # تاریخ
            date_str = bonus.bonus_date.strftime("%Y-%m-%d") if bonus.bonus_date else "N/A"
            self.silver_table.setItem(row, 0, QTableWidgetItem(date_str))
            
            # مقدار
            qty = float(bonus.silver_quantity) if bonus.silver_quantity else 0
            self.silver_table.setItem(row, 1, QTableWidgetItem(f"{qty:,.2f}"))
            
            total_silver += bonus.silver_quantity or 0
        
        # === Summary ===
        self.lbl_total_gold.setText(f"{float(total_gold):,.2f}")
        self.lbl_total_cost.setText(f"${float(total_cost):,.2f}")
        
        avg_rate = (total_cost / total_gold) if total_gold > 0 else Decimal('0')
        self.lbl_avg_rate.setText(f"${float(avg_rate):,.4f}")
        
        self.lbl_total_silver.setText(f"{float(total_silver):,.2f}")
    
    def closeEvent(self, event):
        """بستن session در هنگام بستن دیالوگ"""
        if self.session:
            self.session.close()
        super().closeEvent(event)


class SalesDetailsDialog(QDialog):
    """
    دیالوگ جزئیات فروش‌های یک آکانت
    
    نمایش:
    - تمام فروش‌ها با جزئیات کامل
    - مقدار، نرخ، مبلغ، بهای تمام شده، سود
    - مشتری، پلتفرم، تاریخ
    """
    
    def __init__(self, label: str, platform: str = None, parent=None):
        super().__init__(parent)
        self.label = label
        self.platform = platform
        self.session: Session = get_financial_session()
        
        title = f"🔵 جزئیات فروش - {label}"
        if platform:
            title += f" [{platform}]"
        
        self.setWindowTitle(title)
        self.setMinimumSize(1200, 700)
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """ساخت رابط کاربری"""
        layout = QVBoxLayout(self)
        
        # === Header ===
        header_text = f"🔵 جزئیات فروش برای آکانت: {self.label}"
        if self.platform:
            header_text += f" | پلتفرم: {self.platform}"
        
        header = QLabel(header_text)
        header.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # === Sales Table ===
        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(11)
        self.sales_table.setHorizontalHeaderLabels([
            "تاریخ", "پلتفرم", "نوع", "مقدار", "نرخ فروش", 
            "مبلغ فروش", "بهای تمام شده", "سود", "مشتری", "سود پرسنل", "مغایرت"
        ])
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.sales_table.setAlternatingRowColors(True)
        self.sales_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.sales_table)
        
        # === Summary ===
        self.summary_group = QGroupBox("📊 خلاصه فروش")
        summary_layout = QGridLayout()
        
        self.lbl_total_sales = QLabel()
        self.lbl_total_revenue = QLabel()
        self.lbl_total_cost = QLabel()
        self.lbl_total_profit = QLabel()
        self.lbl_profit_margin = QLabel()
        self.lbl_unique_customers = QLabel()
        
        summary_layout.addWidget(QLabel("📦 تعداد فروش:"), 0, 0)
        summary_layout.addWidget(self.lbl_total_sales, 0, 1)
        summary_layout.addWidget(QLabel("💰 کل درآمد:"), 0, 2)
        summary_layout.addWidget(self.lbl_total_revenue, 0, 3)
        
        summary_layout.addWidget(QLabel("💵 کل بهای تمام شده:"), 1, 0)
        summary_layout.addWidget(self.lbl_total_cost, 1, 1)
        summary_layout.addWidget(QLabel("💵 کل سود:"), 1, 2)
        summary_layout.addWidget(self.lbl_total_profit, 1, 3)
        
        summary_layout.addWidget(QLabel("📈 حاشیه سود:"), 2, 0)
        summary_layout.addWidget(self.lbl_profit_margin, 2, 1)
        summary_layout.addWidget(QLabel("👥 تعداد مشتریان:"), 2, 2)
        summary_layout.addWidget(self.lbl_unique_customers, 2, 3)
        
        self.summary_group.setLayout(summary_layout)
        layout.addWidget(self.summary_group)
        
        # === Buttons ===
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_close = QPushButton("بستن")
        btn_close.clicked.connect(self.close)
        btn_layout.addWidget(btn_close)
        
        layout.addLayout(btn_layout)
    
    def load_data(self):
        """بارگذاری داده‌ها از دیتابیس"""
        # Query فروش‌ها
        query = self.session.query(Sale).filter_by(label=self.label)
        
        if self.platform:
            query = query.filter_by(platform=self.platform)
        
        sales = query.order_by(Sale.sale_date.desc()).all()
        
        self.sales_table.setRowCount(len(sales))
        
        # آمار
        total_revenue = Decimal('0')
        total_cost = Decimal('0')
        total_profit = Decimal('0')
        customers = set()
        
        for row, sale in enumerate(sales):
            # تاریخ
            date_str = sale.sale_date.strftime("%Y-%m-%d") if sale.sale_date else "N/A"
            self.sales_table.setItem(row, 0, QTableWidgetItem(date_str))
            
            # پلتفرم
            self.sales_table.setItem(row, 1, QTableWidgetItem(sale.platform or "N/A"))
            
            # نوع
            sale_type_icon = "🪙" if sale.sale_type == 'gold' else "⭐"
            self.sales_table.setItem(row, 2, QTableWidgetItem(f"{sale_type_icon} {sale.sale_type}"))
            
            # مقدار
            qty = float(sale.quantity) if sale.quantity else 0
            self.sales_table.setItem(row, 3, QTableWidgetItem(f"{qty:,.2f}"))
            
            # نرخ فروش
            rate = float(sale.sale_rate) if sale.sale_rate else 0
            self.sales_table.setItem(row, 4, QTableWidgetItem(f"{rate:,.2f}"))
            
            # مبلغ فروش
            amount = float(sale.sale_amount) if sale.sale_amount else 0
            self.sales_table.setItem(row, 5, QTableWidgetItem(f"${amount:,.2f}"))
            
            # بهای تمام شده
            cost = float(sale.cost_basis) if sale.cost_basis else 0
            self.sales_table.setItem(row, 6, QTableWidgetItem(f"${cost:,.2f}"))
            
            # سود
            profit = float(sale.profit) if sale.profit else 0
            profit_item = QTableWidgetItem(f"${profit:,.2f}")
            if profit < 0:
                profit_item.setForeground(Qt.GlobalColor.red)
            self.sales_table.setItem(row, 7, profit_item)
            
            # مشتری
            self.sales_table.setItem(row, 8, QTableWidgetItem(sale.customer or "N/A"))
            if sale.customer:
                customers.add(sale.customer)
            
            # سود پرسنل
            staff = float(sale.staff_profit) if sale.staff_profit else 0
            self.sales_table.setItem(row, 9, QTableWidgetItem(f"${staff:,.2f}" if staff else "N/A"))
            
            # مغایرت
            discrepancy = ""
            if sale.staff_profit and sale.profit:
                diff = abs(float(sale.staff_profit) - profit)
                if diff > 0.01:  # حداقل 1 سنت اختلاف
                    discrepancy = f"⚠️ {diff:,.2f}"
            self.sales_table.setItem(row, 10, QTableWidgetItem(discrepancy))
            
            # جمع آمار
            total_revenue += sale.sale_amount or 0
            total_cost += sale.cost_basis or 0
            total_profit += sale.profit or 0
        
        # === Summary ===
        self.lbl_total_sales.setText(str(len(sales)))
        self.lbl_total_revenue.setText(f"${float(total_revenue):,.2f}")
        self.lbl_total_cost.setText(f"${float(total_cost):,.2f}")
        self.lbl_total_profit.setText(f"${float(total_profit):,.2f}")
        
        profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
        self.lbl_profit_margin.setText(f"{float(profit_margin):,.2f}%")
        
        self.lbl_unique_customers.setText(str(len(customers)))
    
    def closeEvent(self, event):
        """بستن session در هنگام بستن دیالوگ"""
        if self.session:
            self.session.close()
        super().closeEvent(event)
