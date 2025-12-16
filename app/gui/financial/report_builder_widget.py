"""
Report Builder Widget - سیستم گزارش‌گیری جدید
================================================
گزارشات بر اساس سیستم Label-Based
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox, QTextEdit,
    QGroupBox, QMessageBox, QHeaderView,
    QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from datetime import datetime

from app.models.financial import (
    Account,
    AccountGold,
    AccountSilver,
    Sale,
    Customer,
    get_financial_session
)
from app.core.financial.calculation_engine import CalculationEngine
from app.core.financial.report_generator import ReportGenerator
from app.core.logger import app_logger


class ReportBuilderWidget(QWidget):
    """
    ویجت گزارش‌ساز
    """
    
    # Signals
    export_requested = pyqtSignal(str, dict)  # (report_type, data)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = app_logger
        self.db = get_financial_session()
        self.engine = CalculationEngine(self.db)
        self.generator = ReportGenerator(self.engine)
        self.init_ui()
    
    def init_ui(self):
        """ایجاد رابط کاربری"""
        layout = QVBoxLayout(self)
        
        # عنوان
        title = QLabel("📊 گزارشات مالی")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # انتخاب نوع گزارش
        report_group = QGroupBox("انتخاب گزارش")
        report_layout = QVBoxLayout()
        
        # نوع گزارش
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("نوع گزارش:"))
        self.report_type = QComboBox()
        self.report_type.addItems([
            "گزارش Label (تک آکانت)",
            "گزارش Email (چند آکانت)",
            "گزارش Customer (مشتری)",
            "گزارش کلی سیستم"
        ])
        self.report_type.currentTextChanged.connect(self.on_type_changed)
        type_layout.addWidget(self.report_type)
        type_layout.addStretch()
        report_layout.addLayout(type_layout)
        
        # فیلد ورودی
        input_layout = QHBoxLayout()
        self.input_label = QLabel("Label:")
        input_layout.addWidget(self.input_label)
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("مثال: g450")
        input_layout.addWidget(self.input_field)
        
        self.generate_btn = QPushButton("🔍 تولید گزارش")
        self.generate_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.generate_btn.clicked.connect(self.generate_report)
        input_layout.addWidget(self.generate_btn)
        
        report_layout.addLayout(input_layout)
        report_group.setLayout(report_layout)
        layout.addWidget(report_group)
        
        # نمایش گزارش
        result_group = QGroupBox("نتیجه گزارش")
        result_layout = QVBoxLayout()
        
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.report_text.setFont(QFont("Cascadia Code", 9))
        result_layout.addWidget(self.report_text)
        
        # دکمه‌های عملیات
        actions_layout = QHBoxLayout()
        
        self.export_btn = QPushButton("📤 Export به Excel")
        self.export_btn.clicked.connect(self.export_to_excel)
        self.export_btn.setEnabled(False)
        actions_layout.addWidget(self.export_btn)
        
        self.clear_btn = QPushButton("🗑️ پاک کردن")
        self.clear_btn.clicked.connect(self.clear_report)
        actions_layout.addWidget(self.clear_btn)
        
        actions_layout.addStretch()
        result_layout.addLayout(actions_layout)
        
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)
    
    def on_type_changed(self, report_type: str):
        """تغییر نوع گزارش"""
        if "Label" in report_type:
            self.input_label.setText("Label:")
            self.input_field.setPlaceholderText("مثال: g450")
        elif "Email" in report_type:
            self.input_label.setText("Email:")
            self.input_field.setPlaceholderText("مثال: test@example.com")
        elif "Customer" in report_type:
            self.input_label.setText("Customer:")
            self.input_field.setPlaceholderText("مثال: PX")
        else:
            self.input_label.setText("")
            self.input_field.setPlaceholderText("گزارش کلی نیاز به ورودی ندارد")
            self.input_field.setEnabled(False)
            return
        
        self.input_field.setEnabled(True)
    
    def generate_report(self):
        """تولید گزارش"""
        try:
            report_type = self.report_type.currentText()
            input_value = self.input_field.text().strip()
            
            if "کلی" not in report_type and not input_value:
                QMessageBox.warning(self, "خطا", "لطفاً مقدار ورودی را وارد کنید")
                return
            
            # تولید گزارش بر اساس نوع
            if "Label" in report_type:
                report = self.generator.generate_label_report(input_value)
            elif "Email" in report_type:
                report = self.generator.generate_email_report(input_value)
            elif "Customer" in report_type:
                report = self.generator.generate_customer_report(input_value)
            else:
                report = self.generator.generate_system_summary_report()
            
            self.report_text.setText(report)
            self.export_btn.setEnabled(True)
            self.logger.info(f"گزارش تولید شد: {report_type}")
            
        except Exception as e:
            self.logger.error(f"خطا در تولید گزارش: {str(e)}")
            QMessageBox.critical(
                self,
                "خطا",
                f"خطا در تولید گزارش:\n{str(e)}"
            )
    
    def export_to_excel(self):
        """Export به Excel"""
        try:
            from PyQt6.QtWidgets import QFileDialog
            
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "ذخیره گزارش",
                f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                "Excel Files (*.xlsx)"
            )
            
            if filename:
                self.generator.export_to_excel(filename)
                QMessageBox.information(
                    self,
                    "موفق",
                    f"گزارش با موفقیت ذخیره شد:\n{filename}"
                )
                self.logger.info(f"گزارش ذخیره شد: {filename}")
        
        except Exception as e:
            self.logger.error(f"خطا در export: {str(e)}")
            QMessageBox.critical(
                self,
                "خطا",
                f"خطا در ذخیره گزارش:\n{str(e)}"
            )
    
    def clear_report(self):
        """پاک کردن گزارش"""
        self.report_text.clear()
        self.input_field.clear()
        self.export_btn.setEnabled(False)
    
    def closeEvent(self, event):
        """بستن دیتابیس"""
        self.db.close()
        event.accept()
