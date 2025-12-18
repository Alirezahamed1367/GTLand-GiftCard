"""
Comprehensive Reports Widget - ویجت گزارشات جامع
================================================
10 نوع گزارش کامل برای تحلیل کسب‌وکار
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox, QTextEdit,
    QGroupBox, QMessageBox, QHeaderView, QDateEdit, QSpinBox,
    QFileDialog, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont
from datetime import datetime, date
import json

from app.models.financial import get_financial_session
from app.core.financial.comprehensive_reports import ComprehensiveReportBuilder
from app.core.logger import app_logger


class ComprehensiveReportsWidget(QWidget):
    """
    ویجت گزارشات جامع - 10 نوع گزارش
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = app_logger
        self.db = get_financial_session()
        self.report_builder = ComprehensiveReportBuilder(self.db)
        self.current_report_data = None
        self.init_ui()
    
    def init_ui(self):
        """ایجاد رابط کاربری"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # عنوان
        title = QLabel("📊 گزارشات جامع")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #1976D2; padding: 10px;")
        layout.addWidget(title)
        
        # انتخاب نوع گزارش
        report_group = QGroupBox("انتخاب نوع گزارش")
        report_layout = QVBoxLayout()
        
        # نوع گزارش
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("نوع گزارش:"))
        self.report_type = QComboBox()
        self.report_type.addItems([
            "📊 Dashboard - خلاصه کل سیستم",
            "📅 گزارش روزانه - Daily Report",
            "📆 گزارش ماهانه - Monthly Report",
            "📋 تمام آکانت‌ها - All Accounts",
            "📦 گزارش موجودی - Inventory",
            "👥 گزارش تامین‌کنندگان - Suppliers",
            "🎮 گزارش پلتفرم‌ها - Platforms",
            "👤 مشتریان برتر - Top Customers",
            "📈 گزارش مقایسه‌ای - Comparative",
            "📁 Export همه گزارشات به Excel"
        ])
        self.report_type.currentIndexChanged.connect(self.on_type_changed)
        self.report_type.setFont(QFont("Segoe UI", 10))
        type_layout.addWidget(self.report_type, 1)
        report_layout.addLayout(type_layout)
        
        # پارامترهای گزارش (پویا)
        self.params_layout = QVBoxLayout()
        report_layout.addLayout(self.params_layout)
        
        # دکمه تولید
        btn_layout = QHBoxLayout()
        self.generate_btn = QPushButton("🔍 تولید گزارش")
        self.generate_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.generate_btn.clicked.connect(self.generate_report)
        btn_layout.addStretch()
        btn_layout.addWidget(self.generate_btn)
        btn_layout.addStretch()
        report_layout.addLayout(btn_layout)
        
        report_group.setLayout(report_layout)
        layout.addWidget(report_group)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        # نمایش گزارش
        result_group = QGroupBox("نتیجه گزارش")
        result_layout = QVBoxLayout()
        
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.report_text.setFont(QFont("Cascadia Code", 9))
        self.report_text.setStyleSheet("background-color: #f5f5f5;")
        result_layout.addWidget(self.report_text)
        
        # دکمه‌های عملیات
        action_layout = QHBoxLayout()
        
        self.export_btn = QPushButton("💾 ذخیره به Excel")
        self.export_btn.setFont(QFont("Segoe UI", 10))
        self.export_btn.clicked.connect(self.export_to_excel)
        self.export_btn.setEnabled(False)
        action_layout.addWidget(self.export_btn)
        
        self.copy_btn = QPushButton("📋 کپی متن")
        self.copy_btn.setFont(QFont("Segoe UI", 10))
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        self.copy_btn.setEnabled(False)
        action_layout.addWidget(self.copy_btn)
        
        action_layout.addStretch()
        result_layout.addLayout(action_layout)
        
        result_group.setLayout(result_layout)
        layout.addWidget(result_group, 1)
        
        # نمایش پارامترهای اولیه
        self.on_type_changed(0)
    
    def on_type_changed(self, index):
        """تغییر نوع گزارش - نمایش پارامترهای مربوطه"""
        # پاک کردن پارامترهای قبلی
        while self.params_layout.count():
            child = self.params_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # اضافه کردن پارامترهای جدید
        if index == 1:  # Daily Report
            date_layout = QHBoxLayout()
            date_layout.addWidget(QLabel("تاریخ:"))
            self.date_param = QDateEdit()
            self.date_param.setDate(QDate.currentDate())
            self.date_param.setCalendarPopup(True)
            date_layout.addWidget(self.date_param)
            date_layout.addStretch()
            self.params_layout.addLayout(date_layout)
            
        elif index == 2:  # Monthly Report
            month_layout = QHBoxLayout()
            month_layout.addWidget(QLabel("سال:"))
            self.year_param = QSpinBox()
            self.year_param.setRange(2020, 2030)
            self.year_param.setValue(datetime.now().year)
            month_layout.addWidget(self.year_param)
            
            month_layout.addWidget(QLabel("ماه:"))
            self.month_param = QSpinBox()
            self.month_param.setRange(1, 12)
            self.month_param.setValue(datetime.now().month)
            month_layout.addWidget(self.month_param)
            month_layout.addStretch()
            self.params_layout.addLayout(month_layout)
            
        elif index == 3:  # All Accounts
            sort_layout = QHBoxLayout()
            sort_layout.addWidget(QLabel("مرتب‌سازی بر اساس:"))
            self.sort_param = QComboBox()
            self.sort_param.addItems(["profit", "revenue", "cost", "label"])
            sort_layout.addWidget(self.sort_param)
            sort_layout.addStretch()
            self.params_layout.addLayout(sort_layout)
            
        elif index == 4:  # Inventory
            threshold_layout = QHBoxLayout()
            threshold_layout.addWidget(QLabel("آستانه موجودی کم:"))
            self.threshold_param = QSpinBox()
            self.threshold_param.setRange(0, 10000)
            self.threshold_param.setValue(500)
            threshold_layout.addWidget(self.threshold_param)
            threshold_layout.addStretch()
            self.params_layout.addLayout(threshold_layout)
            
        elif index == 7:  # Top Customers
            top_layout = QHBoxLayout()
            top_layout.addWidget(QLabel("تعداد مشتریان برتر:"))
            self.top_param = QSpinBox()
            self.top_param.setRange(5, 100)
            self.top_param.setValue(10)
            top_layout.addWidget(self.top_param)
            top_layout.addStretch()
            self.params_layout.addLayout(top_layout)
            
        elif index == 8:  # Comparative
            period_layout = QHBoxLayout()
            period_layout.addWidget(QLabel("دوره مقایسه:"))
            self.period_param = QComboBox()
            self.period_param.addItems(["daily", "monthly"])
            period_layout.addWidget(self.period_param)
            period_layout.addStretch()
            self.params_layout.addLayout(period_layout)
    
    def generate_report(self):
        """تولید گزارش بر اساس نوع انتخاب شده"""
        try:
            self.progress.setVisible(True)
            self.progress.setValue(0)
            self.report_text.clear()
            self.current_report_data = None
            
            index = self.report_type.currentIndex()
            
            self.progress.setValue(20)
            
            if index == 0:  # Dashboard
                data = self.report_builder.generate_dashboard_summary()
                text = self.format_dashboard(data)
                
            elif index == 1:  # Daily Report
                selected_date = self.date_param.date().toPyDate()
                data = self.report_builder.generate_daily_report(selected_date)
                text = self.format_daily_report(data)
                
            elif index == 2:  # Monthly Report
                year = self.year_param.value()
                month = self.month_param.value()
                data = self.report_builder.generate_monthly_report(year, month)
                text = self.format_monthly_report(data)
                
            elif index == 3:  # All Accounts
                sort_by = self.sort_param.currentText()
                df = self.report_builder.generate_all_accounts_report(sort_by)
                text = self.format_dataframe(df, "تمام آکانت‌ها")
                data = df.to_dict('records')
                
            elif index == 4:  # Inventory
                threshold = self.threshold_param.value()
                data = self.report_builder.generate_inventory_report(threshold)
                text = self.format_inventory(data)
                
            elif index == 5:  # Suppliers
                df = self.report_builder.generate_suppliers_report()
                text = self.format_dataframe(df, "گزارش تامین‌کنندگان")
                data = df.to_dict('records')
                
            elif index == 6:  # Platforms
                df = self.report_builder.generate_platforms_report()
                text = self.format_dataframe(df, "گزارش پلتفرم‌ها")
                data = df.to_dict('records')
                
            elif index == 7:  # Top Customers
                top_n = self.top_param.value()
                df = self.report_builder.generate_customers_report(top_n)
                text = self.format_dataframe(df, f"مشتریان برتر (Top {top_n})")
                data = df.to_dict('records')
                
            elif index == 8:  # Comparative
                period = self.period_param.currentText()
                data = self.report_builder.generate_comparative_report(period)
                text = self.format_comparative(data)
                
            elif index == 9:  # Export All
                self.export_all_reports()
                return
            
            self.progress.setValue(80)
            
            self.current_report_data = data
            self.report_text.setText(text)
            
            self.export_btn.setEnabled(True)
            self.copy_btn.setEnabled(True)
            
            self.progress.setValue(100)
            self.progress.setVisible(False)
            
            self.logger.info(f"گزارش تولید شد: {self.report_type.currentText()}")
            
        except Exception as e:
            self.progress.setVisible(False)
            QMessageBox.critical(self, "خطا", f"خطا در تولید گزارش:\n{str(e)}")
            self.logger.error(f"خطا در تولید گزارش: {str(e)}")
    
    def format_dashboard(self, data):
        """فرمت Dashboard"""
        text = "=" * 80 + "\n"
        text += "📊 DASHBOARD - خلاصه کل سیستم\n"
        text += "=" * 80 + "\n\n"
        
        text += "📈 آمار کلی:\n"
        text += f"  • تعداد کل آکانت‌ها: {data['total_accounts']}\n"
        text += f"  • کل سرمایه‌گذاری: {data['total_investments']:,.0f} تومان\n"
        text += f"  • کل درآمد فروش: {data['total_sales_revenue']:,.0f} تومان\n"
        text += f"  • کل سود: {data['total_profit']:,.0f} تومان\n"
        text += f"  • Profit Margin: {data['profit_margin']}%\n\n"
        
        text += "📦 موجودی:\n"
        text += f"  • Gold: {data['gold_inventory']:,.0f}\n"
        text += f"  • Silver: {data['silver_inventory']:,.0f}\n\n"
        
        text += f"🎮 پلتفرم‌های فعال: {data['active_platforms']}\n"
        text += f"👥 تعداد مشتریان: {data['total_customers']}\n\n"
        
        text += "📊 فروش:\n"
        text += f"  • امروز: {data['today_sales']:,.0f} تومان\n"
        text += f"  • این ماه: {data['this_month_sales']:,.0f} تومان\n\n"
        
        text += "🏆 5 آکانت برتر (بیشترین سود):\n"
        for idx, acc in enumerate(data['top_accounts'][:5], 1):
            text += f"  {idx}. {acc['label']}: سود={acc['profit']:,.0f}, درآمد={acc['revenue']:,.0f}\n"
        
        text += "\n📋 آخرین تراکنش‌ها:\n"
        for idx, trans in enumerate(data['recent_transactions'][:5], 1):
            text += f"  {idx}. {trans['date']} - {trans['label']} - {trans['amount']:,.0f} تومان\n"
        
        return text
    
    def format_daily_report(self, data):
        """فرمت Daily Report"""
        text = "=" * 80 + "\n"
        text += f"📅 گزارش روزانه - {data['date']}\n"
        text += "=" * 80 + "\n\n"
        
        text += f"📊 خلاصه:\n"
        text += f"  • تعداد فروش: {data['total_sales_count']}\n"
        text += f"  • درآمد کل: {data['total_sales_revenue']:,.0f} تومان\n"
        text += f"  • Gold فروخته شده: {data['gold_sold']:,.0f}\n"
        text += f"  • Silver فروخته شده: {data['silver_sold']:,.0f}\n\n"
        
        if data['by_platform']:
            text += "🎮 به تفکیک پلتفرم:\n"
            for p in data['by_platform']:
                text += f"  • {p['platform']}: {p['sales_count']} فروش، {p['revenue']:,.0f} تومان\n"
            text += "\n"
        
        if data['by_account']:
            text += "📋 به تفکیک آکانت (Top 10):\n"
            for idx, (label, acc) in enumerate(list(data['by_account'].items())[:10], 1):
                text += f"  {idx}. {label}: {acc['sales_count']} فروش، {acc['revenue']:,.0f} تومان\n"
        
        return text
    
    def format_monthly_report(self, data):
        """فرمت Monthly Report"""
        text = "=" * 80 + "\n"
        text += f"📆 گزارش ماهانه - {data['month_name']} {data['year']}\n"
        text += "=" * 80 + "\n\n"
        
        text += f"📊 خلاصه:\n"
        text += f"  • تعداد فروش: {data['total_sales_count']}\n"
        text += f"  • درآمد کل: {data['total_sales_revenue']:,.0f} تومان\n"
        text += f"  • تعداد خرید: {data['total_purchases_count']}\n"
        text += f"  • هزینه خرید: {data['total_purchases_cost']:,.0f} تومان\n"
        text += f"  • سود خالص: {data['net_profit']:,.0f} تومان\n\n"
        
        if data.get('daily_stats'):
            text += "📅 آمار روزانه:\n"
            for day in data['daily_stats'][:10]:  # فقط 10 روز اول
                date_str = day.get('date', 'N/A')
                if hasattr(date_str, 'strftime'):
                    date_str = date_str.strftime('%Y-%m-%d')
                text += f"  • {date_str}: {day.get('sales_count', 0)} فروش، {day.get('revenue', 0):,.0f} تومان\n"
        
        return text
    
    def format_inventory(self, data):
        """فرمت Inventory Report"""
        text = "=" * 80 + "\n"
        text += "📦 گزارش موجودی\n"
        text += "=" * 80 + "\n\n"
        
        text += f"📊 موجودی کل:\n"
        text += f"  • Gold: {data['total_gold_inventory']:,.0f}\n"
        text += f"  • Silver: {data['total_silver_inventory']:,.0f}\n\n"
        
        text += f"⚠️ هشدارها:\n"
        text += f"  • موجودی کم Gold: {data['low_gold_accounts_count']} آکانت\n"
        text += f"  • موجودی کم Silver: {data['low_silver_accounts_count']} آکانت\n"
        text += f"  • تمام شده Gold: {data['out_of_stock_gold_count']} آکانت\n"
        text += f"  • تمام شده Silver: {data['out_of_stock_silver_count']} آکانت\n\n"
        
        if data['low_gold_accounts']:
            text += "⚠️ آکانت‌های با موجودی کم Gold:\n"
            for label in data['low_gold_accounts'][:10]:
                text += f"  • {label}\n"
        
        return text
    
    def format_comparative(self, data):
        """فرمت Comparative Report"""
        text = "=" * 80 + "\n"
        text += "📈 گزارش مقایسه‌ای\n"
        text += "=" * 80 + "\n\n"
        
        text += f"📊 مقایسه {data['current']['label']} با {data['previous']['label']}:\n\n"
        
        text += f"  {data['current']['label']}:\n"
        text += f"    • درآمد: {data['current']['revenue']:,.0f} تومان\n"
        text += f"    • تعداد فروش: {data['current']['sales_count']}\n\n"
        
        text += f"  {data['previous']['label']}:\n"
        text += f"    • درآمد: {data['previous']['revenue']:,.0f} تومان\n"
        text += f"    • تعداد فروش: {data['previous']['sales_count']}\n\n"
        
        text += f"  📈 تغییرات:\n"
        text += f"    • تغییر درآمد: {data['changes']['revenue_change']:,.0f} تومان ({data['changes']['revenue_change_pct']}%)\n"
        text += f"    • تغییر تعداد فروش: {data['changes']['sales_change']} ({data['changes']['sales_change_pct']}%)\n"
        
        trend_icon = "📈" if data['changes']['trend'] == 'up' else "📉" if data['changes']['trend'] == 'down' else "➡️"
        text += f"    • روند: {trend_icon} {data['changes']['trend']}\n"
        
        return text
    
    def format_dataframe(self, df, title):
        """فرمت DataFrame"""
        if df.empty:
            return f"⚠️ {title}: داده‌ای یافت نشد"
        
        text = "=" * 80 + "\n"
        text += f"{title}\n"
        text += "=" * 80 + "\n\n"
        text += df.to_string(index=False)
        text += f"\n\nتعداد کل: {len(df)} رکورد"
        
        return text
    
    def export_to_excel(self):
        """Export گزارش به Excel"""
        if not self.current_report_data:
            QMessageBox.warning(self, "هشدار", "ابتدا یک گزارش تولید کنید")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "ذخیره گزارش",
            f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            "Excel Files (*.xlsx)"
        )
        
        if filename:
            try:
                import pandas as pd
                
                # اگر DataFrame است
                if isinstance(self.current_report_data, pd.DataFrame):
                    self.current_report_data.to_excel(filename, index=False, engine='openpyxl')
                # اگر Dict است
                else:
                    df = pd.DataFrame([self.current_report_data])
                    df.to_excel(filename, index=False, engine='openpyxl')
                
                QMessageBox.information(self, "موفق", f"گزارش در {filename} ذخیره شد")
                self.logger.info(f"گزارش Export شد: {filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "خطا", f"خطا در ذخیره فایل:\n{str(e)}")
                self.logger.error(f"خطا در Export: {str(e)}")
    
    def export_all_reports(self):
        """Export همه گزارشات به یک فایل Excel"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "ذخیره همه گزارشات",
            f"all_reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            "Excel Files (*.xlsx)"
        )
        
        if filename:
            try:
                self.progress.setVisible(True)
                self.progress.setValue(0)
                
                self.report_builder.export_all_reports_to_excel(filename)
                
                self.progress.setValue(100)
                self.progress.setVisible(False)
                
                QMessageBox.information(
                    self,
                    "موفق",
                    f"تمام گزارشات در {filename} ذخیره شد\n\n"
                    "این فایل شامل 9 Sheet است:\n"
                    "• Dashboard\n• Daily\n• Monthly\n• All Accounts\n"
                    "• Inventory\n• Suppliers\n• Platforms\n• Customers\n• Comparative"
                )
                self.logger.info(f"همه گزارشات Export شد: {filename}")
                
            except Exception as e:
                self.progress.setVisible(False)
                QMessageBox.critical(self, "خطا", f"خطا در ذخیره فایل:\n{str(e)}")
                self.logger.error(f"خطا در Export All: {str(e)}")
    
    def copy_to_clipboard(self):
        """کپی متن گزارش به Clipboard"""
        from PyQt6.QtWidgets import QApplication
        
        text = self.report_text.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            QMessageBox.information(self, "موفق", "متن گزارش کپی شد")
