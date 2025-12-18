"""
Professional Excel-Like Grid Widget
====================================
نمایش داده‌ها به صورت حرفه‌ای همانند Excel:
- سطرها: هر Label
- ستون‌ها: خرید، فروش‌ها به تفکیک Platform، سود/زیان
- محاسبات خودکار
"""
from typing import Dict, List, Optional, Any
from decimal import Decimal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QComboBox, QCheckBox, QGroupBox,
    QMessageBox, QFileDialog, QDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QBrush
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd
import json
import os

from app.models.financial import (
    Account, AccountGold, Sale, Platform,
    get_financial_session
)
from app.core.financial.calculation_engine import CalculationEngine
from app.gui.financial.column_customization_dialog import ColumnCustomizationDialog


class ProfessionalGridWidget(QWidget):
    """
    ویجت Grid حرفه‌ای
    
    ساختار ستون‌ها:
    ┌──────────┬───────────┬──────────┬─────────┬─────────────────────────────────────┬─────────────┐
    │  Label   │   Email   │  خرید    │  نرخ    │      فروش به تفکیک Platform        │    سود      │
    │          │           │  (GOLD)  │  خرید   │  Roblox │ Apple │ Steam │ جمع فروش │   کل/درصد   │
    └──────────┴───────────┴──────────┴─────────┴─────────┴───────┴───────┴───────────┴─────────────┘
    """
    
    def __init__(self, db_path: str = "data/financial/financial.db"):
        super().__init__()
        
        # استفاده از session موجود
        self.session = get_financial_session()
        self.calc_engine = CalculationEngine(self.session)
        
        # داده‌های Grid
        self.grid_data: List[Dict[str, Any]] = []
        self.platforms: List[str] = []  # لیست پلتفرم‌های موجود
        
        # بارگذاری تنظیمات شخصی‌سازی
        self.column_config = self.load_column_config()
        
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        """ساخت رابط کاربری"""
        layout = QVBoxLayout(self)
        
        # ═══ هدر ═══
        header_layout = QHBoxLayout()
        
        title = QLabel("📊 گزارش حرفه‌ای خرید و فروش")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # فیلترها
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["همه", "فقط سودده", "فقط زیان‌ده", "موجودی دارد"])
        self.filter_combo.currentTextChanged.connect(self.apply_filters)
        header_layout.addWidget(QLabel("فیلتر:"))
        customize_btn = QPushButton("⚙️ شخصی‌سازی ستون‌ها")
        customize_btn.clicked.connect(self.customize_columns)
        customize_btn.setStyleSheet("""
            QPushButton {
                background: #9C27B0;
                color: white;
                padding: 5px 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #7B1FA2;
            }
        """)
        header_layout.addWidget(customize_btn)
        
        header_layout.addWidget(self.filter_combo)
        
        # دکمه‌ها
        refresh_btn = QPushButton("🔄 بروزرسانی")
        refresh_btn.clicked.connect(self.load_data)
        header_layout.addWidget(refresh_btn)
        
        export_btn = QPushButton("📥 خروجی Excel")
        export_btn.clicked.connect(self.export_to_excel)
        header_layout.addWidget(export_btn)
        
        layout.addLayout(header_layout)
        
        # ═══ Grid اصلی ═══
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #D0D0D0;
                background-color: white;
            }
            QTableWidget::item:selected {
                background-color: #E3F2FD;
                color: black;
            }
            QHeaderView::section {
                background-color: #1976D2;
                color: white;
                padding: 8px;
                font-weight: bold;
                border: 1px solid #0D47A1;
            }
        """)
        
        # Double-click برای جزئیات
        self.table.cellDoubleClicked.connect(self.show_label_details)
        
        layout.addWidget(self.table)
        
        # ═══ خلاصه کل ═══
        summary_group = QGroupBox("خلاصه کل")
        summary_layout = QHBoxLayout()
        
        self.lbl_total_accounts = QLabel("تعداد: 0")
        self.lbl_total_revenue = QLabel("فروش کل: 0")
        self.lbl_total_profit = QLabel("سود کل: 0")
        self.lbl_total_cost = QLabel("هزینه کل: 0")
        
        for lbl in [self.lbl_total_accounts, self.lbl_total_revenue, 
                    self.lbl_total_profit, self.lbl_total_cost]:
            lbl.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            summary_layout.addWidget(lbl)
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
    
    def load_data(self):
        """بارگذاری داده‌ها از دیتابیس"""
        # بارگذاری پلتفرم‌ها
        try:
            platforms = self.session.query(Platform).filter_by(is_active=True).all()
            self.platforms = [p.code for p in platforms]
        except Exception as e:
            print(f"⚠️ خطا در بارگذاری platforms: {e}")
            self.platforms = []
        
        if not self.platforms:
            # استخراج پلتفرم‌های موجود از Sales
            try:
                from sqlalchemy import distinct
                platform_results = self.session.query(distinct(Sale.platform)).filter(
                    Sale.platform.isnot(None)
                ).all()
                self.platforms = [p[0] for p in platform_results if p[0]]
            except:
                pass
            
            if not self.platforms:
                self.platforms = ['roblox', 'apple', 'steam']  # پیش‌فرض
        
        # بارگذاری تمام Accounts
        accounts = self.session.query(Account).all()
        
        self.grid_data = []
        
        for account in accounts:
            label = account.label
            
            # محاسبه خلاصه
            summary = self.calc_engine.calculate_label_summary(label)
            if not summary:
                continue
            
            # فروش به تفکیک Platform
            platform_sales = self._get_platform_sales(label)
            
            # 🆕 محاسبه جمع فروش تمام پلتفرم‌ها (ستون شخصی)
            custom_total_qty = sum(platform_sales.get(f'{p}_qty', 0) for p in self.platforms)
            custom_total_revenue = sum(platform_sales.get(f'{p}_revenue', 0) for p in self.platforms)
            custom_profit = custom_total_revenue - summary['gold']['cost']
            custom_profit_pct = (custom_profit / summary['gold']['cost'] * 100) if summary['gold']['cost'] > 0 else 0
            
            row_data = {
                'label': label,
                'email': summary['email'] or '',
                'supplier': summary['supplier'] or '',
                
                # خرید
                'gold_purchased': summary['gold']['purchased'],
                'purchase_rate': summary['gold']['purchase_rate'],
                'purchase_cost': summary['gold']['cost'],
                
                # فروش به تفکیک Platform
                **platform_sales,  # {'roblox_qty': ..., 'roblox_revenue': ..., ...}
                
                # 🆕 ستون شخصی: جمع فروش تمام پلتفرم‌ها
                'custom_total_qty': custom_total_qty,
                'custom_total_revenue': custom_total_revenue,
                'custom_profit': custom_profit,
                'custom_profit_pct': custom_profit_pct,
                
                # جمع فروش
                'total_sold': summary['gold']['sold'] + summary['silver']['sold'],
                'total_revenue': summary['total']['revenue'],
                
                # سود
                'total_profit': summary['total']['profit'],
                'profit_pct': (summary['total']['profit'] / summary['total']['cost'] * 100) 
                              if summary['total']['cost'] > 0 else 0,
                
                # موجودی
                'remaining_gold': summary['gold']['remaining'],
                'remaining_silver': summary['silver']['remaining']
            }
            
            self.grid_data.append(row_data)
        
        # نمایش در Grid
        self.populate_table()
        self.update_summary()
    
    def _get_platform_sales(self, label: str) -> Dict[str, float]:
        """
        فروش‌ها به تفکیک Platform
        
        Returns:
            {
                'roblox_qty': 0.5,
                'roblox_revenue': 2500,
                'apple_qty': 0.3,
                'apple_revenue': 1500,
                ...
            }
        """
        result = {}
        
        for platform_code in self.platforms:
            # فروش‌های این Platform
            sales = self.session.query(Sale).filter_by(
                label=label,
                platform=platform_code
            ).all()
            
            qty = sum(float(s.quantity) for s in sales)
            revenue = sum(float(s.sale_amount) for s in sales)
            
            result[f'{platform_code}_qty'] = qty
            result[f'{platform_code}_revenue'] = revenue
        
        return result
    
    def populate_table(self):
        """نمایش داده‌ها در جدول با توجه به تنظیمات شخصی‌سازی"""
        
        # نقشه نام ستون‌ها
        column_names = {
            'label': 'Label',
            'email': 'Email',
            'supplier': 'تأمین‌کننده',
            'gold_purchased': 'خرید (Gold)',
            'purchase_rate': 'نرخ خرید',
            'purchase_cost': 'هزینه خرید',
            'custom_total_qty': '🆕 شخصی\n(مقدار)',
            'custom_total_revenue': '🆕 شخصی\n(فروش)',
            'custom_profit': '🆕 شخصی\n(سود)',
            'custom_profit_pct': '🆕 شخصی\n(سود%)',
            'total_sold': 'جمع فروش',
            'total_revenue': 'درآمد کل',
            'total_profit': 'سود/زیان',
            'profit_pct': 'درصد سود',
            'remaining_gold': 'موجودی Gold',
            'remaining_silver': 'موجودی Silver'
        }
        
        # ساخت لیست ستون‌های نمایشی
        visible_cols = self.column_config.get('visible_columns', list(column_names.keys()))
        column_order = self.column_config.get('column_order', list(column_names.keys()))
        
        # فیلتر ستون‌های visible
        display_columns = [col for col in column_order if col in visible_cols]
        headers = [column_names.get(col, col) for col in display_columns]
        
        # اضافه کردن ستون‌های Platform
        platform_headers = []
        if self.column_config.get('show_platforms', True) and self.platforms:
            for p in self.platforms:
                platform_headers.append(f'{p.title()}\n(مقدار)')
                platform_headers.append(f'{p.title()}\n(فروش)')
        
        # اضافه کردن ستون‌های فرمول
        formula_headers = []
        custom_formulas = self.column_config.get('custom_formulas', [])
        for formula in custom_formulas:
            formula_headers.append(formula['name'])
        
        all_headers = headers + platform_headers + formula_headers
        
        # تنظیم جدول
        self.table.setRowCount(len(self.grid_data))
        self.table.setColumnCount(len(all_headers))
        self.table.setHorizontalHeaderLabels(all_headers)
        
        # پر کردن داده‌ها
        for row_idx, row_data in enumerate(self.grid_data):
            col_idx = 0
            
            # ستون‌های پایه
            for col_key in display_columns:
                value = row_data.get(col_key, '')
                
                # فرمت‌بندی بر اساس نوع
                if col_key in ['gold_purchased', 'total_sold', 'remaining_gold', 'custom_total_qty']:
                    formatted = f"{value:.2f}" if value else '-'
                    align = 'right'
                elif col_key in ['purchase_rate', 'purchase_cost', 'total_revenue', 'custom_total_revenue']:
                    formatted = f"{value:,.0f}" if value else '-'
                    align = 'right'
                elif col_key in ['total_profit', 'custom_profit']:
                    formatted = f"{value:,.0f}" if value else '0'
                    align = 'right'
                    color = QColor(34, 139, 34) if value >= 0 else QColor(220, 20, 60)
                    self._set_cell(row_idx, col_idx, formatted, align, color, True)
                    col_idx += 1
                    continue
                elif col_key in ['profit_pct', 'custom_profit_pct']:
                    formatted = f"{value:.1f}%" if value else '0%'
                    align = 'right'
                    color = QColor(34, 139, 34) if value >= 0 else QColor(220, 20, 60)
                    self._set_cell(row_idx, col_idx, formatted, align, color)
                    col_idx += 1
                    continue
                else:
                    formatted = str(value) if value else ''
                    align = 'left'
                
                self._set_cell(row_idx, col_idx, formatted, align)
                col_idx += 1
            
            # ستون‌های Platform
            if self.column_config.get('show_platforms', True):
                for platform_code in self.platforms:
                    qty = row_data.get(f'{platform_code}_qty', 0)
                    revenue = row_data.get(f'{platform_code}_revenue', 0)
                    
                    self._set_cell(row_idx, col_idx, f"{qty:.2f}" if qty > 0 else '-', 'right')
                    col_idx += 1
                    
                    self._set_cell(row_idx, col_idx, f"{revenue:,.0f}" if revenue > 0 else '-', 'right')
                    col_idx += 1
            
            # ستون‌های فرمول
            for formula in custom_formulas:
                result = self.calculate_formula(formula['formula'], row_data)
                
                if result is not None:
                    # فرمت بر اساس نوع
                    if formula['format'] == 'currency':
                        formatted = f"{result:,.0f}"
                    elif formula['format'] == 'percent':
                        formatted = f"{result:.1f}%"
                    else:
                        formatted = f"{result:.2f}"
                else:
                    formatted = '-'
                
                self._set_cell(row_idx, col_idx, formatted, 'right')
                col_idx += 1
        
        # تنظیم عرض ستون‌ها
        self.table.horizontalHeader().setStretchLastSection(False)
        for i in range(min(3, len(all_headers))):
            self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        for i in range(3, len(all_headers)):
            self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
            self.table.setColumnWidth(i, 100)
    
    def _set_cell(self, row: int, col: int, value: str, align: str = 'center', 
                  color: QColor = None, bold: bool = False):
        """تنظیم یک سلول"""
        item = QTableWidgetItem(str(value))
        
        # تراز
        if align == 'right':
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        elif align == 'left':
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        else:
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # رنگ
        if color:
            item.setForeground(QBrush(color))
        
        # Bold
        if bold:
            font = item.font()
            font.setBold(True)
            item.setFont(font)
        
        self.table.setItem(row, col, item)
    
    def update_summary(self):
        """بروزرسانی خلاصه کل"""
        if not self.grid_data:
            return
        
        total_accounts = len(self.grid_data)
        total_revenue = sum(row['total_revenue'] for row in self.grid_data)
        total_profit = sum(row['total_profit'] for row in self.grid_data)
        total_cost = sum(row['purchase_cost'] for row in self.grid_data)
        
        self.lbl_total_accounts.setText(f"تعداد: {total_accounts}")
        self.lbl_total_revenue.setText(f"فروش کل: {total_revenue:,.0f}")
        self.lbl_total_profit.setText(f"سود کل: {total_profit:,.0f}")
        self.lbl_total_cost.setText(f"هزینه کل: {total_cost:,.0f}")
        
        # رنگ سود/زیان
        if total_profit >= 0:
            self.lbl_total_profit.setStyleSheet("color: green;")
        else:
            self.lbl_total_profit.setStyleSheet("color: red;")
    
    def apply_filters(self):
        """اعمال فیلترها"""
        filter_text = self.filter_combo.currentText()
        
        for row_idx in range(self.table.rowCount()):
            show_row = True
            
            if row_idx >= len(self.grid_data):
                continue
            
            row_data = self.grid_data[row_idx]
            
            if filter_text == "فقط سودده":
                show_row = row_data['total_profit'] > 0
            elif filter_text == "فقط زیان‌ده":
                show_row = row_data['total_profit'] < 0
            elif filter_text == "موجودی دارد":
                show_row = (row_data['remaining_gold'] > 0 or row_data['remaining_silver'] > 0)
            
            self.table.setRowHidden(row_idx, not show_row)
    
    def show_label_details(self, row: int, col: int):
        """نمایش جزئیات Label (Double-click)"""
        if row >= len(self.grid_data):
            return
        
        row_data = self.grid_data[row]
        label = row_data['label']
        
        # محاسبه دقیق
        summary = self.calc_engine.calculate_label_summary(label)
        
        details = f"""
📋 جزئیات {label}
{'='*40}

📧 Email: {summary['email']}
📦 تأمین‌کننده: {summary['supplier']}

💰 خرید:
   • مقدار: {summary['gold']['purchased']} Gold
   • نرخ: {summary['gold']['purchase_rate']:,.0f}
   • هزینه: {summary['gold']['cost']:,.0f}

💵 فروش:
   • Gold فروخته شده: {summary['gold']['sold']}
   • Silver فروخته شده: {summary['silver']['sold']}
   • درآمد: {summary['total']['revenue']:,.0f}

💎 سود/زیان:
   • سود Gold: {summary['gold']['profit']:,.0f}
   • سود Silver: {summary['silver']['profit']:,.0f}
   • جمع: {summary['total']['profit']:,.0f}
   • درصد: {summary['gold']['profit_pct']:.1f}%

📊 آمار:
   • تعداد فروش: {summary['stats']['sale_count']}
   • مشتریان منحصر: {summary['stats']['unique_customers']}

🔄 موجودی:
   • Gold باقی‌مانده: {summary['gold']['remaining']}
   • Silver باقی‌مانده: {summary['silver']['remaining']}
"""
        
        QMessageBox.information(self, f"جزئیات {label}", details)
    
    def export_to_excel(self):
        """خروجی به Excel"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "ذخیره فایل Excel", 
            "data/exports/professional_report.xlsx", 
            "Excel Files (*.xlsx)"
        )
        
        if not file_path:
            return
        
        try:
            # تبدیل به DataFrame
            df_data = []
            
            for row_data in self.grid_data:
                row = {
                    'Label': row_data['label'],
                    'Email': row_data['email'],
                    'Supplier': row_data['supplier'],
                    'Gold_Purchased': row_data['gold_purchased'],
                    'Purchase_Rate': row_data['purchase_rate'],
                    'Purchase_Cost': row_data['purchase_cost']
                }
                
                # Platform columns
                for platform_code in self.platforms:
                    row[f'{platform_code.title()}_Qty'] = row_data.get(f'{platform_code}_qty', 0)
                    row[f'{platform_code.title()}_Revenue'] = row_data.get(f'{platform_code}_revenue', 0)
                
                row.update({
                    'Total_Sold': row_data['total_sold'],
                    'Total_Revenue': row_data['total_revenue'],
                    'Total_Profit': row_data['total_profit'],
                    'Profit_Pct': row_data['profit_pct'],
                    'Remaining_Gold': row_data['remaining_gold'],
                    'Remaining_Silver': row_data['remaining_silver']
                })
                
                df_data.append(row)
            
            df = pd.DataFrame(df_data)
            
            # ذخیره
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Professional Report')
            
            QMessageBox.information(self, "موفقیت", f"✅ فایل ذخیره شد:\n{file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در ذخیره Excel:\n{str(e)}")
    
    def load_column_config(self) -> Dict:
        """بارگذاری تنظیمات ستون‌ها"""
        import os
        config_path = 'data/financial/grid_config.json'
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # پیش‌فرض
        return {
            'visible_columns': [
                'label', 'email', 'supplier', 'gold_purchased', 
                'purchase_rate', 'purchase_cost', 'total_sold',
                'total_revenue', 'total_profit', 'profit_pct',
                'remaining_gold', 'remaining_silver'
            ],
            'column_order': [
                'label', 'email', 'supplier', 'gold_purchased',
                'purchase_rate', 'purchase_cost', 'total_sold',
                'total_revenue', 'total_profit', 'profit_pct',
                'remaining_gold', 'remaining_silver'
            ],
            'custom_formulas': [],
            'show_platforms': True
        }
    
    def customize_columns(self):
        """باز کردن دیالوگ شخصی‌سازی"""
        dialog = ColumnCustomizationDialog(self.column_config, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.column_config = dialog.get_config()
            # بارگذاری مجدد با تنظیمات جدید
            self.load_data()
            QMessageBox.information(
                self, "موفقیت",
                "✅ تنظیمات اعمال شد!\n\nگزارش با ستون‌های جدید نمایش داده می‌شود."
            )
    
    def calculate_formula(self, formula: str, row_data: Dict) -> Any:
        """محاسبه فرمول سفارشی"""
        try:
            # جایگزینی متغیرها با مقادیر واقعی
            formula_str = formula
            for key, value in row_data.items():
                placeholder = '{' + key + '}'
                if placeholder in formula_str:
                    # تبدیل به عدد برای محاسبه
                    numeric_value = float(value) if value is not None else 0
                    formula_str = formula_str.replace(placeholder, str(numeric_value))
            
            # محاسبه فرمول
            result = eval(formula_str)
            return result
            
        except Exception as e:
            return None
    
    def closeEvent(self, event):
        """بستن Session"""
        self.session.close()
        event.accept()
