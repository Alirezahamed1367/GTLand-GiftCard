"""
ویجت گزارش‌ساز پیشرفته
کاربر می‌تواند گزارش سفارشی بسازد
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QComboBox, QLabel, QListWidget, QCheckBox, QLineEdit,
    QDateEdit, QTextEdit, QMessageBox, QFileDialog, QTableWidget,
    QTableWidgetItem, QHeaderView, QSplitter
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont
from sqlalchemy.orm import Session
from app.core.financial.advanced_report_builder import AdvancedReportBuilder, ReportTemplates
from typing import Dict, Any
import pandas as pd


class AdvancedReportWidget(QWidget):
    """
    ویجت گزارش‌ساز پیشرفته
    
    ویژگی‌ها:
    - انتخاب نوع گزارش
    - فیلترهای متعدد
    - پیش‌نمایش گزارش
    - صادرات به Excel
    - ذخیره/بارگذاری قالب
    """
    
    report_generated = pyqtSignal(pd.DataFrame)
    
    def __init__(self, session: Session, parent=None):
        super().__init__(parent)
        self.session = session
        self.report_builder = AdvancedReportBuilder(session)
        self.current_df = None
        
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.init_ui()
    
    def init_ui(self):
        """ایجاد رابط کاربری"""
        main_layout = QVBoxLayout()
        
        # عنوان
        title = QLabel("📊 گزارش‌ساز پیشرفته")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)
        
        # Splitter برای تقسیم صفحه
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # ═══ پنل چپ: تنظیمات گزارش ═══
        settings_panel = self.create_settings_panel()
        splitter.addWidget(settings_panel)
        
        # ═══ پنل راست: پیش‌نمایش گزارش ═══
        preview_panel = self.create_preview_panel()
        splitter.addWidget(preview_panel)
        
        splitter.setSizes([400, 600])
        main_layout.addWidget(splitter)
        
        self.setLayout(main_layout)
    
    def create_settings_panel(self) -> QWidget:
        """پنل تنظیمات گزارش"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # ═══ نوع گزارش ═══
        type_group = QGroupBox("📋 نوع گزارش")
        type_layout = QVBoxLayout()
        
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems([
            "📊 گزارش Label (تک آکانت)",
            "🎮 گزارش پلتفرم",
            "👥 گزارش مشتری",
            "🔧 گزارش سفارشی"
        ])
        self.report_type_combo.currentIndexChanged.connect(self.on_report_type_changed)
        type_layout.addWidget(self.report_type_combo)
        
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)
        
        # ═══ قالب‌های آماده ═══
        template_group = QGroupBox("📑 قالب‌های آماده")
        template_layout = QVBoxLayout()
        
        self.template_combo = QComboBox()
        self.template_combo.addItems([
            "انتخاب قالب...",
            "📅 فروش امروز",
            "🏆 مشتریان برتر",
            "⚖️ مقایسه پلتفرم‌ها",
            "⚠️ موجودی کم"
        ])
        self.template_combo.currentIndexChanged.connect(self.load_template)
        template_layout.addWidget(self.template_combo)
        
        template_group.setLayout(template_layout)
        layout.addWidget(template_group)
        
        # ═══ فیلترها ═══
        filter_group = QGroupBox("🔍 فیلترها")
        filter_layout = QVBoxLayout()
        
        # Label
        h1 = QHBoxLayout()
        h1.addWidget(QLabel("Label:"))
        self.filter_label = QLineEdit()
        self.filter_label.setPlaceholderText("مثال: A1054")
        h1.addWidget(self.filter_label)
        filter_layout.addLayout(h1)
        
        # پلتفرم
        h2 = QHBoxLayout()
        h2.addWidget(QLabel("پلتفرم:"))
        self.filter_platform = QComboBox()
        self.filter_platform.addItems([
            "همه",
            "roblox",
            "apple",
            "nintendo",
            "pubg",
            "freefire"
        ])
        h2.addWidget(self.filter_platform)
        filter_layout.addLayout(h2)
        
        # نوع فروش
        h3 = QHBoxLayout()
        h3.addWidget(QLabel("نوع:"))
        self.filter_sale_type = QComboBox()
        self.filter_sale_type.addItems(["همه", "gold", "silver"])
        h3.addWidget(self.filter_sale_type)
        filter_layout.addLayout(h3)
        
        # تاریخ از
        h4 = QHBoxLayout()
        h4.addWidget(QLabel("از تاریخ:"))
        self.filter_date_from = QDateEdit()
        self.filter_date_from.setCalendarPopup(True)
        self.filter_date_from.setDate(QDate.currentDate().addMonths(-1))
        h4.addWidget(self.filter_date_from)
        filter_layout.addLayout(h4)
        
        # تاریخ تا
        h5 = QHBoxLayout()
        h5.addWidget(QLabel("تا تاریخ:"))
        self.filter_date_to = QDateEdit()
        self.filter_date_to.setCalendarPopup(True)
        self.filter_date_to.setDate(QDate.currentDate())
        h5.addWidget(self.filter_date_to)
        filter_layout.addLayout(h5)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # ═══ مرتب‌سازی ═══
        sort_group = QGroupBox("↕️ مرتب‌سازی")
        sort_layout = QVBoxLayout()
        
        h6 = QHBoxLayout()
        h6.addWidget(QLabel("مرتب بر اساس:"))
        self.sort_by_combo = QComboBox()
        self.sort_by_combo.addItems([
            "Total Profit",
            "Total Revenue",
            "Total Cost",
            "Gold Remaining",
            "Label"
        ])
        h6.addWidget(self.sort_by_combo)
        sort_layout.addLayout(h6)
        
        h7 = QHBoxLayout()
        self.sort_desc = QCheckBox("نزولی")
        self.sort_desc.setChecked(True)
        h7.addWidget(self.sort_desc)
        sort_layout.addLayout(h7)
        
        sort_group.setLayout(sort_layout)
        layout.addWidget(sort_group)
        
        # دکمه‌ها
        button_layout = QHBoxLayout()
        
        generate_btn = QPushButton("🔍 تولید گزارش")
        generate_btn.clicked.connect(self.generate_report)
        generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        button_layout.addWidget(generate_btn)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        panel.setLayout(layout)
        return panel
    
    def create_preview_panel(self) -> QWidget:
        """پنل پیش‌نمایش گزارش"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # عنوان
        header_layout = QHBoxLayout()
        preview_label = QLabel("📄 پیش‌نمایش گزارش")
        preview_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header_layout.addWidget(preview_label)
        header_layout.addStretch()
        
        # دکمه‌های عملیات
        export_excel_btn = QPushButton("📥 Excel")
        export_excel_btn.clicked.connect(self.export_to_excel)
        header_layout.addWidget(export_excel_btn)
        
        save_config_btn = QPushButton("💾 ذخیره قالب")
        save_config_btn.clicked.connect(self.save_report_config)
        header_layout.addWidget(save_config_btn)
        
        layout.addLayout(header_layout)
        
        # جدول نمایش
        self.preview_table = QTableWidget()
        self.preview_table.setAlternatingRowColors(True)
        layout.addWidget(self.preview_table)
        
        # آمار
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("color: #7f8c8d; padding: 5px;")
        layout.addWidget(self.stats_label)
        
        panel.setLayout(layout)
        return panel
    
    def on_report_type_changed(self, index: int):
        """تغییر نوع گزارش"""
        # می‌توان بر اساس نوع، فیلترها را فعال/غیرفعال کرد
        pass
    
    def load_template(self, index: int):
        """بارگذاری قالب آماده"""
        if index == 0:
            return
        
        template_map = {
            1: ReportTemplates.daily_sales_summary(),
            2: ReportTemplates.top_customers(10),
            3: ReportTemplates.platform_comparison(),
            4: ReportTemplates.low_stock_accounts(10)
        }
        
        config = template_map.get(index)
        if config:
            self.apply_config(config)
            QMessageBox.information(self, "قالب", "✅ قالب بارگذاری شد")
    
    def apply_config(self, config: Dict[str, Any]):
        """اعمال پیکربندی به فیلترها"""
        filters = config.get('filters', {})
        
        if 'label' in filters:
            self.filter_label.setText(filters['label'])
        
        if 'platform' in filters:
            idx = self.filter_platform.findText(filters['platform'])
            if idx >= 0:
                self.filter_platform.setCurrentIndex(idx)
        
        if 'sale_type' in filters:
            idx = self.filter_sale_type.findText(filters['sale_type'])
            if idx >= 0:
                self.filter_sale_type.setCurrentIndex(idx)
        
        # Sort
        sort_by = config.get('sort_by')
        if sort_by:
            idx = self.sort_by_combo.findText(sort_by)
            if idx >= 0:
                self.sort_by_combo.setCurrentIndex(idx)
    
    def generate_report(self):
        """تولید گزارش"""
        try:
            # ساخت config
            config = self.build_config()
            
            # تولید گزارش
            df = self.report_builder.build_report(config)
            
            if df.empty:
                QMessageBox.information(self, "گزارش", "⚠️ داده‌ای یافت نشد")
                return
            
            self.current_df = df
            
            # نمایش در جدول
            self.display_dataframe(df)
            
            # آمار
            self.stats_label.setText(
                f"📊 تعداد سطرها: {len(df)} | "
                f"ستون‌ها: {len(df.columns)}"
            )
            
            self.report_generated.emit(df)
            
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"❌ خطا در تولید گزارش:\n{str(e)}")
    
    def build_config(self) -> Dict[str, Any]:
        """ساخت پیکربندی از فیلترها"""
        report_type_map = ['label', 'platform', 'customer', 'custom']
        report_type = report_type_map[self.report_type_combo.currentIndex()]
        
        filters = {}
        
        # فیلتر label
        if self.filter_label.text():
            filters['label'] = self.filter_label.text()
        
        # فیلتر platform
        if self.filter_platform.currentIndex() > 0:
            filters['platform'] = self.filter_platform.currentText()
        
        # فیلتر sale_type
        if self.filter_sale_type.currentIndex() > 0:
            filters['sale_type'] = self.filter_sale_type.currentText()
        
        # فیلتر تاریخ
        filters['date_from'] = self.filter_date_from.date().toString('yyyy-MM-dd')
        filters['date_to'] = self.filter_date_to.date().toString('yyyy-MM-dd')
        
        config = {
            'report_type': report_type,
            'filters': filters,
            'sort_by': self.sort_by_combo.currentText(),
            'sort_order': 'desc' if self.sort_desc.isChecked() else 'asc'
        }
        
        return config
    
    def display_dataframe(self, df: pd.DataFrame):
        """نمایش DataFrame در جدول"""
        self.preview_table.clear()
        
        # تنظیم ابعاد
        self.preview_table.setRowCount(len(df))
        self.preview_table.setColumnCount(len(df.columns))
        self.preview_table.setHorizontalHeaderLabels(df.columns.tolist())
        
        # پر کردن داده‌ها
        for i in range(len(df)):
            for j in range(len(df.columns)):
                value = df.iloc[i, j]
                
                # فرمت عدد
                if isinstance(value, (int, float)):
                    if abs(value) > 1000:
                        text = f"{value:,.2f}"
                    else:
                        text = f"{value:.2f}"
                else:
                    text = str(value) if value is not None else ""
                
                item = QTableWidgetItem(text)
                
                # راست‌چین برای اعداد
                if isinstance(value, (int, float)):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                
                self.preview_table.setItem(i, j, item)
        
        # تنظیم عرض ستون‌ها
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    
    def export_to_excel(self):
        """صادرات به Excel"""
        if self.current_df is None or self.current_df.empty:
            QMessageBox.warning(self, "خطا", "⚠️ ابتدا گزارش را تولید کنید")
            return
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "ذخیره گزارش",
            "report.xlsx",
            "Excel Files (*.xlsx)"
        )
        
        if not filepath:
            return
        
        try:
            self.report_builder.export_to_excel(self.current_df, filepath)
            QMessageBox.information(self, "موفقیت", f"✅ گزارش در '{filepath}' ذخیره شد")
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"❌ خطا در صادرات:\n{str(e)}")
    
    def save_report_config(self):
        """ذخیره پیکربندی گزارش"""
        from PyQt6.QtWidgets import QInputDialog
        
        name, ok = QInputDialog.getText(
            self,
            "ذخیره قالب",
            "نام قالب:"
        )
        
        if ok and name:
            try:
                config = self.build_config()
                report_id = self.report_builder.save_report_config(name, config)
                QMessageBox.information(
                    self,
                    "موفقیت",
                    f"✅ قالب '{name}' ذخیره شد (ID: {report_id})"
                )
            except Exception as e:
                QMessageBox.critical(self, "خطا", f"❌ خطا در ذخیره:\n{str(e)}")
