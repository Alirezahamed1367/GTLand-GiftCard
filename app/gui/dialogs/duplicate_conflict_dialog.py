"""
پنجره تشخیص و حل تعارض داده‌های تکراری
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QGroupBox, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
import json
from typing import Dict, Optional


class DuplicateConflictDialog(QDialog):
    """پنجره مدیریت تعارض داده‌های تکراری"""
    
    def __init__(self, existing_data: Dict, new_data: Dict, row_number: int, parent=None):
        super().__init__(parent)
        
        self.existing_data = existing_data
        self.new_data = new_data
        self.row_number = row_number
        self.user_choice = None  # 'update', 'skip', 'keep_both'
        
        self.init_ui()
        
    def init_ui(self):
        """راه‌اندازی رابط کاربری"""
        self.setWindowTitle("⚠️ تشخیص داده تکراری")
        self.setModal(True)
        self.resize(900, 600)
        
        layout = QVBoxLayout()
        
        # عنوان هشدار
        title_label = QLabel(f"🔍 ردیف {self.row_number} قبلاً استخراج شده است!")
        title_label.setStyleSheet("""
            QLabel {
                background-color: #FFF3CD;
                color: #856404;
                padding: 15px;
                border-radius: 5px;
                font-size: 14pt;
                font-weight: bold;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # توضیحات
        info_label = QLabel(
            "داده‌های جدید با داده‌های موجود در دیتابیس تطابق ندارند.\n"
            "لطفاً تصمیم بگیرید چه کاری انجام شود:"
        )
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("padding: 10px; font-size: 10pt;")
        layout.addWidget(info_label)
        
        # جدول مقایسه
        comparison_group = QGroupBox("📊 مقایسه داده‌ها")
        comparison_layout = QVBoxLayout()
        
        self.comparison_table = QTableWidget()
        self.comparison_table.setColumnCount(3)
        self.comparison_table.setHorizontalHeaderLabels([
            "فیلد", "داده موجود (دیتابیس)", "داده جدید (Google Sheet)"
        ])
        self.comparison_table.horizontalHeader().setStretchLastSection(True)
        self.comparison_table.setAlternatingRowColors(True)
        
        self.populate_comparison_table()
        
        comparison_layout.addWidget(self.comparison_table)
        comparison_group.setLayout(comparison_layout)
        layout.addWidget(comparison_group)
        
        # آمار تفاوت‌ها
        stats_label = QLabel()
        stats_text = self.calculate_differences()
        stats_label.setText(stats_text)
        stats_label.setStyleSheet("""
            QLabel {
                background-color: #E3F2FD;
                padding: 10px;
                border-radius: 5px;
                font-size: 9pt;
            }
        """)
        layout.addWidget(stats_label)
        
        # دکمه‌های عملیات
        buttons_layout = QHBoxLayout()
        
        # دکمه بروزرسانی
        update_btn = QPushButton("🔄 بروزرسانی داده")
        update_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 12px 24px;
                font-size: 11pt;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        update_btn.clicked.connect(self.on_update)
        buttons_layout.addWidget(update_btn)
        
        # دکمه نگه‌داشتن (رد کردن)
        skip_btn = QPushButton("🚫 نگه‌داشتن داده قدیم")
        skip_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 12px 24px;
                font-size: 11pt;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        skip_btn.clicked.connect(self.on_skip)
        buttons_layout.addWidget(skip_btn)
        
        # دکمه لغو
        cancel_btn = QPushButton("❌ لغو")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                padding: 12px 24px;
                font-size: 11pt;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
        
        # راهنما
        help_label = QLabel(
            "💡 راهنما:\n"
            "• بروزرسانی: داده قدیم با داده جدید جایگزین می‌شود\n"
            "• نگه‌داشتن: داده قدیم حفظ می‌شود و داده جدید نادیده گرفته می‌شود"
        )
        help_label.setStyleSheet("""
            QLabel {
                background-color: #F5F5F5;
                padding: 10px;
                border-radius: 5px;
                font-size: 8pt;
                color: #666;
            }
        """)
        layout.addWidget(help_label)
        
        self.setLayout(layout)
    
    def populate_comparison_table(self):
        """پر کردن جدول مقایسه"""
        # ترکیب کلیدها
        all_keys = set(self.existing_data.keys()) | set(self.new_data.keys())
        
        self.comparison_table.setRowCount(len(all_keys))
        
        row = 0
        for key in sorted(all_keys):
            # نام فیلد
            key_item = QTableWidgetItem(key)
            key_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            self.comparison_table.setItem(row, 0, key_item)
            
            # داده موجود
            existing_value = self.existing_data.get(key, "—")
            existing_item = QTableWidgetItem(str(existing_value))
            
            # داده جدید
            new_value = self.new_data.get(key, "—")
            new_item = QTableWidgetItem(str(new_value))
            
            # رنگ‌بندی بر اساس تفاوت
            if existing_value != new_value:
                # تفاوت دارد - زرد
                existing_item.setBackground(QColor("#FFEB3B"))
                new_item.setBackground(QColor("#8BC34A"))
                
                existing_item.setFont(QFont("Arial", 9, QFont.Weight.Bold))
                new_item.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            else:
                # یکسان - سفید
                existing_item.setBackground(QColor("#FFFFFF"))
                new_item.setBackground(QColor("#FFFFFF"))
            
            self.comparison_table.setItem(row, 1, existing_item)
            self.comparison_table.setItem(row, 2, new_item)
            
            row += 1
        
        # تنظیم عرض ستون‌ها
        self.comparison_table.setColumnWidth(0, 200)
        self.comparison_table.setColumnWidth(1, 300)
        self.comparison_table.setColumnWidth(2, 300)
    
    def calculate_differences(self) -> str:
        """محاسبه آمار تفاوت‌ها"""
        all_keys = set(self.existing_data.keys()) | set(self.new_data.keys())
        
        different_count = 0
        same_count = 0
        new_fields = 0
        removed_fields = 0
        
        for key in all_keys:
            existing_value = self.existing_data.get(key)
            new_value = self.new_data.get(key)
            
            if existing_value is None:
                new_fields += 1
            elif new_value is None:
                removed_fields += 1
            elif existing_value != new_value:
                different_count += 1
            else:
                same_count += 1
        
        stats = f"📈 آمار: "
        stats += f"{different_count} فیلد تغییر یافته | "
        stats += f"{same_count} فیلد بدون تغییر"
        
        if new_fields > 0:
            stats += f" | {new_fields} فیلد جدید"
        if removed_fields > 0:
            stats += f" | {removed_fields} فیلد حذف شده"
        
        return stats
    
    def on_update(self):
        """بروزرسانی داده"""
        reply = QMessageBox.question(
            self,
            "تایید بروزرسانی",
            f"آیا مطمئنید که می‌خواهید داده ردیف {self.row_number} را بروزرسانی کنید؟\n\n"
            "⚠️ داده قدیم جایگزین می‌شود و قابل بازگشت نیست!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.user_choice = 'update'
            self.accept()
    
    def on_skip(self):
        """رد کردن و نگه‌داشتن داده قدیم"""
        reply = QMessageBox.question(
            self,
            "تایید نگه‌داشتن",
            f"آیا مطمئنید که می‌خواهید داده قدیم را نگه دارید؟\n\n"
            "داده جدید از Google Sheet نادیده گرفته می‌شود.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.user_choice = 'skip'
            self.accept()
    
    def get_user_choice(self) -> Optional[str]:
        """دریافت انتخاب کاربر"""
        return self.user_choice
