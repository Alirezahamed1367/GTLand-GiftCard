"""
گزارشات مالی - Financial Reports Widget
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QTextEdit, QTabWidget
)
from PyQt6.QtGui import QFont

from app.core.financial import FinancialCalculator
from app.models.financial import FinancialSessionLocal, Department
from app.core.logger import app_logger


class FinancialReportsWidget(QWidget):
    """ویجت گزارشات مالی"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = app_logger
        self.calculator = FinancialCalculator()
        self.init_ui()
        self.load_reports()
    
    def init_ui(self):
        """راه‌اندازی رابط کاربری"""
        layout = QVBoxLayout(self)
        
        title = QLabel("📈 گزارشات مالی")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #2196F3; padding: 10px;")
        layout.addWidget(title)
        
        # فیلتر دپارتمان
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("دپارتمان:"))
        
        self.dept_combo = QComboBox()
        filter_layout.addWidget(self.dept_combo)
        
        generate_btn = QPushButton("📊 تولید گزارش")
        generate_btn.clicked.connect(self.generate_report)
        filter_layout.addWidget(generate_btn)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # نمایش گزارش
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.report_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', monospace;
                font-size: 11pt;
                background: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.report_text)
    
    def load_reports(self):
        """بارگذاری گزینه‌های گزارش"""
        try:
            db = FinancialSessionLocal()
            departments = db.query(Department).all()
            
            self.dept_combo.clear()
            self.dept_combo.addItem("همه دپارتمان‌ها", None)
            for dept in departments:
                self.dept_combo.addItem(dept.name, dept.id)
            
            db.close()
            
        except Exception as e:
            self.logger.error(f"خطا در بارگذاری گزارشات: {str(e)}")
    
    def generate_report(self):
        """تولید گزارش"""
        try:
            dept_id = self.dept_combo.currentData()
            
            if dept_id:
                # گزارش دپارتمان
                result = self.calculator.calculate_department_profit(dept_id)
                
                report = f"""
{'='*60}
گزارش سود/زیان دپارتمان
{'='*60}

دپارتمان: {self.dept_combo.currentText()}
تعداد آکانت‌ها: {result.get('accounts_count', 0):,}

خرید:
  مجموع: {result.get('total_purchase', 0):,.2f} USDT

فروش:
  Gold: {result.get('gold_sales', 0):,.2f} USDT
  Silver: {result.get('silver_sales', 0):,.2f} USDT
  کل: {result.get('total_sales', 0):,.2f} USDT

سود/زیان:
  سود خالص: {result.get('total_profit', 0):,.2f} USDT
  حاشیه سود: {result.get('profit_margin', 0):.2f}%

معادل تومانی:
  خرید: {result.get('total_purchase', 0) * 110000:,.0f} تومان
  فروش: {result.get('total_sales', 0) * 110000:,.0f} تومان
  سود: {result.get('total_profit', 0) * 110000:,.0f} تومان

{'='*60}
                """
                
                self.report_text.setText(report)
            else:
                self.report_text.setText("لطفاً یک دپارتمان انتخاب کنید")
            
        except Exception as e:
            self.logger.error(f"خطا در تولید گزارش: {str(e)}")
            self.report_text.setText(f"خطا: {str(e)}")
