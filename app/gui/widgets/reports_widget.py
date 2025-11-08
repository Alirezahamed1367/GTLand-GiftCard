"""
ویجت گزارش‌ها
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QTabWidget, QHeaderView,
    QLabel, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from app.core.database import db_manager
from app.models import ProcessLog, ExportLog


class ReportsWidget(QWidget):
    """ویجت گزارش‌ها و لاگ‌ها"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        """راه‌اندازی رابط کاربری"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # عنوان
        title = QLabel("📈 گزارش‌ها و لاگ‌ها")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #2196F3;")
        layout.addWidget(title)
        
        # تب‌ها
        tabs = QTabWidget()
        
        # تب لاگ‌های عملیات
        tabs.addTab(self.create_process_logs_tab(), "📝 لاگ عملیات")
        
        # تب لاگ‌های خروجی
        tabs.addTab(self.create_export_logs_tab(), "📤 لاگ خروجی")
        
        # تب آمار
        tabs.addTab(self.create_stats_tab(), "📊 آمار")
        
        layout.addWidget(tabs)
        
        # دکمه بروزرسانی
        refresh_btn = QPushButton("🔄 بروزرسانی")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #1976D2;
            }
        """)
        refresh_btn.clicked.connect(self.load_data)
        layout.addWidget(refresh_btn)
    
    def create_process_logs_tab(self):
        """ایجاد تب لاگ‌های عملیات"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(6)
        self.process_table.setHorizontalHeaderLabels([
            "شناسه", "نوع", "وضعیت", "پیام", "تاریخ شروع", "تاریخ پایان"
        ])
        
        self.setup_table(self.process_table)
        layout.addWidget(self.process_table)
        
        return widget
    
    def create_export_logs_tab(self):
        """ایجاد تب لاگ‌های خروجی"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.export_table = QTableWidget()
        self.export_table.setColumnCount(5)
        self.export_table.setHorizontalHeaderLabels([
            "شناسه", "نوع", "تعداد رکورد", "مسیر فایل", "تاریخ"
        ])
        
        self.setup_table(self.export_table)
        layout.addWidget(self.export_table)
        
        return widget
    
    def create_stats_tab(self):
        """ایجاد تب آمار"""
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setSpacing(20)
        
        # اسکرول برای آمار
        from PyQt6.QtWidgets import QScrollArea
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)
        
        stats_container = QWidget()
        layout = QVBoxLayout(stats_container)
        layout.setSpacing(20)
        
        # آمار دیتابیس
        db_group = QGroupBox("💾 آمار دیتابیس")
        db_layout = QVBoxLayout()
        
        self.db_stats_label = QLabel("در حال بارگذاری...")
        self.db_stats_label.setWordWrap(True)
        self.db_stats_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.db_stats_label.setStyleSheet("""
            QLabel {
                background: #e8f5e9;
                padding: 20px;
                border-radius: 10px;
                font-size: 11pt;
                line-height: 1.8;
                color: #1b5e20;
            }
        """)
        db_layout.addWidget(self.db_stats_label)
        
        db_group.setLayout(db_layout)
        layout.addWidget(db_group)
        
        # آمار عملیات
        ops_group = QGroupBox("⚡ آمار عملیات")
        ops_layout = QVBoxLayout()
        
        self.ops_stats_label = QLabel("در حال بارگذاری...")
        self.ops_stats_label.setWordWrap(True)
        self.ops_stats_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.ops_stats_label.setStyleSheet("""
            QLabel {
                background: #e3f2fd;
                padding: 20px;
                border-radius: 10px;
                font-size: 11pt;
                line-height: 1.8;
                color: #0d47a1;
            }
        """)
        ops_layout.addWidget(self.ops_stats_label)
        
        ops_group.setLayout(ops_layout)
        layout.addWidget(ops_group)
        
        layout.addStretch()
        
        scroll.setWidget(stats_container)
        main_layout.addWidget(scroll)
        
        return widget
    
    def setup_table(self, table):
        """تنظیمات مشترک جدول"""
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setAlternatingRowColors(True)
        table.setStyleSheet("""
            QTableWidget {
                background: white;
                gridline-color: #e0e0e0;
                font-size: 10pt;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background: #2196F3;
                color: white;
            }
            QHeaderView::section {
                background: #f5f5f5;
                padding: 10px;
                border: 1px solid #e0e0e0;
                font-weight: bold;
            }
        """)
        
        header = table.horizontalHeader()
        header.setStretchLastSection(True)
    
    def load_data(self):
        """بارگذاری داده‌ها"""
        self.load_process_logs()
        self.load_export_logs()
        self.load_statistics()
    
    def load_process_logs(self):
        """بارگذاری لاگ‌های عملیات"""
        try:
            db = db_manager.get_session()
            logs = db.query(ProcessLog).order_by(ProcessLog.id.desc()).limit(100).all()
            
            self.process_table.setRowCount(len(logs))
            
            for row, log in enumerate(logs):
                # شناسه
                self.process_table.setItem(row, 0, QTableWidgetItem(str(log.id)))
                
                # نوع
                self.process_table.setItem(row, 1, QTableWidgetItem(log.process_type))
                
                # وضعیت
                status_item = QTableWidgetItem(log.status)
                if log.status == "SUCCESS":
                    status_item.setForeground(QColor("#4CAF50"))
                elif log.status == "ERROR":
                    status_item.setForeground(QColor("#F44336"))
                else:
                    status_item.setForeground(QColor("#FF9800"))
                self.process_table.setItem(row, 2, status_item)
                
                # پیام
                message = log.message[:100] + "..." if len(log.message) > 100 else log.message
                self.process_table.setItem(row, 3, QTableWidgetItem(message))
                
                # تاریخ شروع
                start_date = log.started_at.strftime("%Y-%m-%d %H:%M:%S") if log.started_at else "-"
                self.process_table.setItem(row, 4, QTableWidgetItem(start_date))
                
                # تاریخ پایان
                end_date = log.completed_at.strftime("%Y-%m-%d %H:%M:%S") if log.completed_at else "-"
                self.process_table.setItem(row, 5, QTableWidgetItem(end_date))
            
            db.close()
            
        except Exception as e:
            print(f"خطا در بارگذاری لاگ‌های عملیات: {str(e)}")
    
    def load_export_logs(self):
        """بارگذاری لاگ‌های خروجی"""
        try:
            db = db_manager.get_session()
            logs = db.query(ExportLog).order_by(ExportLog.id.desc()).limit(100).all()
            
            self.export_table.setRowCount(len(logs))
            
            for row, log in enumerate(logs):
                # شناسه
                self.export_table.setItem(row, 0, QTableWidgetItem(str(log.id)))
                
                # نوع
                self.export_table.setItem(row, 1, QTableWidgetItem(str(log.export_type)))
                
                # تعداد
                self.export_table.setItem(row, 2, QTableWidgetItem(f"{log.record_count:,}"))
                
                # مسیر
                path = log.file_path[-50:] + "..." if len(log.file_path) > 50 else log.file_path
                self.export_table.setItem(row, 3, QTableWidgetItem(path))
                
                # تاریخ
                date = log.created_at.strftime("%Y-%m-%d %H:%M:%S")
                self.export_table.setItem(row, 4, QTableWidgetItem(date))
            
            db.close()
            
        except Exception as e:
            print(f"خطا در بارگذاری لاگ‌های خروجی: {str(e)}")
    
    def load_statistics(self):
        """بارگذاری آمار"""
        try:
            stats = db_manager.get_statistics()
            
            # آمار دیتابیس با فونت بهتر
            db_text = f"""
📊 آمار دیتابیس:

📋 تنظیمات شیت‌ها: {stats.get('total_configs', 0):,} ({stats.get('active_configs', 0):,} فعال)

📦 کل رکوردها: {stats.get('total_records', 0):,}

✅ خروجی گرفته شده: {stats.get('exported_records', 0):,}

⏳ در انتظار: {stats.get('pending_records', 0):,}

🔄 بروز شده: {stats.get('updated_records', 0):,}
            """.strip()
            
            self.db_stats_label.setText(db_text)
            
            # آمار عملیات
            db = db_manager.get_session()
            
            total_processes = db.query(ProcessLog).count()
            successful = db.query(ProcessLog).filter_by(status="SUCCESS").count()
            failed = db.query(ProcessLog).filter_by(status="ERROR").count()
            
            total_exports = db.query(ExportLog).count()
            
            db.close()
            
            success_rate = (successful / total_processes * 100) if total_processes > 0 else 0
            
            ops_text = f"""
⚡ آمار عملیات:

🔢 کل عملیات: {total_processes:,}

✅ موفق: {successful:,}

❌ ناموفق: {failed:,}

📈 نرخ موفقیت: {success_rate:.1f}%

📤 کل خروجی‌ها: {total_exports:,}
            """.strip()
            
            self.ops_stats_label.setText(ops_text)
            
            self.ops_stats_label.setText(
                f"⚡ آمار عملیات:\n\n"
                f"📝 کل عملیات: {total_processes:,}\n"
                f"✅ موفق: {successful:,}\n"
                f"❌ ناموفق: {failed:,}\n"
                f"📤 کل خروجی‌ها: {total_exports:,}"
            )
            
        except Exception as e:
            self.db_stats_label.setText(f"❌ خطا: {str(e)}")
            self.ops_stats_label.setText(f"❌ خطا: {str(e)}")
