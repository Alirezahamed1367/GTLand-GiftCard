"""
ویجت مدیریت موجودی - نسخه پایه
Inventory Management Widget (Basic Version)

این نسخه شامل:
- لیست آکانت‌ها با اطلاعات اصلی
- Badge های کلیک‌پذیر برای خرید/فروش
- باز کردن Dialog های جزئیات

نسخه آینده: DataGrid با ستون‌های پویا پلتفرم
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QLabel, QPushButton, QHeaderView,
    QLineEdit, QComboBox, QGroupBox, QGridLayout, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QBrush, QColor
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from typing import List, Dict

from app.models.financial import (
    Account, AccountGold, AccountSilver, Sale, Platform,
    get_financial_session
)
from app.gui.dialogs.details_dialogs import PurchaseDetailsDialog, SalesDetailsDialog


class ClickableBadge(QPushButton):
    """دکمه Badge کلیک‌پذیر"""
    
    def __init__(self, label: str, count: int, badge_type: str, parent=None):
        super().__init__(parent)
        self.account_label = label
        self.count = count
        self.badge_type = badge_type  # 'purchase' یا 'sale'
        
        if badge_type == 'purchase':
            self.setText(f"📦 {count}")
            self.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    padding: 3px 8px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)
        else:  # sale
            self.setText(f"🔵 {count}")
            self.setStyleSheet("""
                QPushButton {
                    background-color: #2ecc71;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    padding: 3px 8px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #27ae60;
                }
            """)
        
        self.setMaximumWidth(80)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class InventoryManagementWidget(QWidget):
    """
    ویجت مدیریت موجودی
    
    Features:
    - لیست تمام آکانت‌ها
    - خلاصه خرید (Gold/Silver)
    - خلاصه فروش (تعداد، مبلغ، سود)
    - Badge های کلیک‌پذیر
    - فیلتر و جستجو
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session: Session = get_financial_session()
        self.accounts_data: List[Dict] = []
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """ساخت رابط کاربری"""
        layout = QVBoxLayout(self)
        
        # === Header ===
        header = QLabel("📊 مدیریت موجودی و فروش")
        header.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # === Filters ===
        filter_group = QGroupBox("🔍 جستجو و فیلتر")
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("جستجو:"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Label یا Email...")
        self.search_box.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.search_box, 2)
        
        filter_layout.addWidget(QLabel("وضعیت:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["همه", "Consumed", "Global", "Silver Bonus"])
        self.status_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.status_filter, 1)
        
        btn_refresh = QPushButton("🔄 بروزرسانی")
        btn_refresh.clicked.connect(self.load_data)
        filter_layout.addWidget(btn_refresh)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # === Summary ===
        self.summary_group = QGroupBox("📊 خلاصه کل")
        summary_layout = QGridLayout()
        
        self.lbl_total_accounts = QLabel("0")
        self.lbl_total_gold_purchased = QLabel("0")
        self.lbl_total_cost = QLabel("$0")
        self.lbl_total_revenue = QLabel("$0")
        self.lbl_total_profit = QLabel("$0")
        self.lbl_profit_margin = QLabel("0%")
        
        summary_layout.addWidget(QLabel("📦 تعداد آکانت:"), 0, 0)
        summary_layout.addWidget(self.lbl_total_accounts, 0, 1)
        summary_layout.addWidget(QLabel("🪙 کل Gold خریداری شده:"), 0, 2)
        summary_layout.addWidget(self.lbl_total_gold_purchased, 0, 3)
        
        summary_layout.addWidget(QLabel("💵 کل هزینه:"), 1, 0)
        summary_layout.addWidget(self.lbl_total_cost, 1, 1)
        summary_layout.addWidget(QLabel("💰 کل درآمد:"), 1, 2)
        summary_layout.addWidget(self.lbl_total_revenue, 1, 3)
        
        summary_layout.addWidget(QLabel("💵 کل سود:"), 2, 0)
        summary_layout.addWidget(self.lbl_total_profit, 2, 1)
        summary_layout.addWidget(QLabel("📈 حاشیه سود:"), 2, 2)
        summary_layout.addWidget(self.lbl_profit_margin, 2, 3)
        
        self.summary_group.setLayout(summary_layout)
        layout.addWidget(self.summary_group)
        
        # === Accounts Table ===
        table_label = QLabel("📋 لیست آکانت‌ها")
        table_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(table_label)
        
        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(11)
        self.accounts_table.setHorizontalHeaderLabels([
            "Label", "Email", "Supplier", "Status",
            "Gold (Qty)", "Gold (Cost)",
            "Silver (Bonus)",
            "فروش (تعداد)", "فروش (مبلغ)", "سود",
            "عملیات"
        ])
        
        self.accounts_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.accounts_table.horizontalHeader().setStretchLastSection(True)
        self.accounts_table.setAlternatingRowColors(True)
        self.accounts_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.accounts_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.accounts_table)
    
    def load_data(self):
        """بارگذاری داده‌ها از دیتابیس"""
        # بارگذاری تمام آکانت‌ها
        accounts = self.session.query(Account).all()
        
        self.accounts_data = []
        
        total_gold = Decimal('0')
        total_cost = Decimal('0')
        total_revenue = Decimal('0')
        total_profit = Decimal('0')
        
        for account in accounts:
            # خرید Gold
            gold_purchases = self.session.query(AccountGold).filter_by(label=account.label).all()
            gold_qty = sum(p.gold_quantity or 0 for p in gold_purchases)
            gold_cost = sum(p.purchase_cost or 0 for p in gold_purchases)
            
            # بونوس Silver
            silver_bonuses = self.session.query(AccountSilver).filter_by(label=account.label).all()
            silver_qty = sum(b.silver_quantity or 0 for b in silver_bonuses)
            
            # فروش
            sales = self.session.query(Sale).filter_by(label=account.label).all()
            sales_count = len(sales)
            sales_amount = sum(s.sale_amount or 0 for s in sales)
            sales_profit = sum(s.profit or 0 for s in sales)
            
            self.accounts_data.append({
                'account': account,
                'gold_qty': gold_qty,
                'gold_cost': gold_cost,
                'silver_qty': silver_qty,
                'sales_count': sales_count,
                'sales_amount': sales_amount,
                'sales_profit': sales_profit,
                'purchase_count': len(gold_purchases) + len(silver_bonuses)
            })
            
            total_gold += gold_qty
            total_cost += gold_cost
            total_revenue += sales_amount
            total_profit += sales_profit
        
        # به‌روزرسانی Summary
        self.lbl_total_accounts.setText(str(len(accounts)))
        self.lbl_total_gold_purchased.setText(f"{float(total_gold):,.2f}")
        self.lbl_total_cost.setText(f"${float(total_cost):,.2f}")
        self.lbl_total_revenue.setText(f"${float(total_revenue):,.2f}")
        self.lbl_total_profit.setText(f"${float(total_profit):,.2f}")
        
        profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
        self.lbl_profit_margin.setText(f"{float(profit_margin):,.2f}%")
        
        # نمایش جدول
        self.apply_filters()
    
    def apply_filters(self):
        """اعمال فیلترها و نمایش جدول"""
        search_text = self.search_box.text().lower()
        status_filter = self.status_filter.currentText()
        
        # فیلتر داده‌ها
        filtered_data = []
        for data in self.accounts_data:
            account = data['account']
            
            # فیلتر جستجو
            if search_text:
                if search_text not in account.label.lower() and \
                   (not account.email or search_text not in account.email.lower()):
                    continue
            
            # فیلتر وضعیت
            if status_filter != "همه":
                if account.status != status_filter:
                    continue
            
            filtered_data.append(data)
        
        # پر کردن جدول
        self.accounts_table.setRowCount(len(filtered_data))
        
        for row, data in enumerate(filtered_data):
            account = data['account']
            
            # Label
            self.accounts_table.setItem(row, 0, QTableWidgetItem(account.label))
            
            # Email
            self.accounts_table.setItem(row, 1, QTableWidgetItem(account.email or "N/A"))
            
            # Supplier
            self.accounts_table.setItem(row, 2, QTableWidgetItem(account.supplier or "N/A"))
            
            # Status
            status_item = QTableWidgetItem(account.status or "N/A")
            if account.status == "Consumed":
                status_item.setForeground(QBrush(QColor("#e74c3c")))
            elif account.status == "Global":
                status_item.setForeground(QBrush(QColor("#2ecc71")))
            self.accounts_table.setItem(row, 3, status_item)
            
            # Gold Qty
            gold_qty = float(data['gold_qty'])
            self.accounts_table.setItem(row, 4, QTableWidgetItem(f"{gold_qty:,.2f}"))
            
            # Gold Cost
            gold_cost = float(data['gold_cost'])
            self.accounts_table.setItem(row, 5, QTableWidgetItem(f"${gold_cost:,.2f}"))
            
            # Silver Bonus
            silver_qty = float(data['silver_qty'])
            self.accounts_table.setItem(row, 6, QTableWidgetItem(f"{silver_qty:,.2f}"))
            
            # Sales Count
            self.accounts_table.setItem(row, 7, QTableWidgetItem(str(data['sales_count'])))
            
            # Sales Amount
            sales_amount = float(data['sales_amount'])
            self.accounts_table.setItem(row, 8, QTableWidgetItem(f"${sales_amount:,.2f}"))
            
            # Profit
            profit = float(data['sales_profit'])
            profit_item = QTableWidgetItem(f"${profit:,.2f}")
            if profit < 0:
                profit_item.setForeground(QBrush(QColor("#e74c3c")))
            elif profit > 0:
                profit_item.setForeground(QBrush(QColor("#2ecc71")))
            self.accounts_table.setItem(row, 9, profit_item)
            
            # عملیات (Badges)
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            actions_layout.setSpacing(5)
            
            # Purchase Badge
            if data['purchase_count'] > 0:
                purchase_btn = ClickableBadge(account.label, data['purchase_count'], 'purchase')
                purchase_btn.clicked.connect(lambda checked, lbl=account.label: self.show_purchase_details(lbl))
                actions_layout.addWidget(purchase_btn)
            
            # Sales Badge
            if data['sales_count'] > 0:
                sales_btn = ClickableBadge(account.label, data['sales_count'], 'sale')
                sales_btn.clicked.connect(lambda checked, lbl=account.label: self.show_sales_details(lbl))
                actions_layout.addWidget(sales_btn)
            
            actions_layout.addStretch()
            self.accounts_table.setCellWidget(row, 10, actions_widget)
    
    def show_purchase_details(self, label: str):
        """نمایش جزئیات خریدها"""
        dialog = PurchaseDetailsDialog(label, self)
        dialog.exec()
    
    def show_sales_details(self, label: str):
        """نمایش جزئیات فروش‌ها"""
        dialog = SalesDetailsDialog(label, parent=self)
        dialog.exec()
    
    def closeEvent(self, event):
        """بستن session در هنگام بستن ویجت"""
        if self.session:
            self.session.close()
        super().closeEvent(event)
