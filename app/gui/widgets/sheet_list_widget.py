"""
ویجت لیست شیت‌ها
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from app.core.database import db_manager
from app.gui.dialogs.sheet_config_dialog import SheetConfigDialog


class SheetListWidget(QWidget):
    """ویجت لیست شیت‌های پیکربندی شده"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        """راه‌اندازی رابط کاربری"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # جدول
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "شناسه", "نام", "آدرس شیت", "برگه", "وضعیت", "تاریخ ایجاد"
        ])
        
        # تنظیمات جدول
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
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
        
        # تنظیم عرض ستون‌ها
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.table)
        
        # دکمه‌ها
        buttons_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ افزودن")
        add_btn.setStyleSheet(self.get_button_style("#4CAF50"))
        add_btn.clicked.connect(self.add_sheet)
        buttons_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("✏️ ویرایش")
        edit_btn.setStyleSheet(self.get_button_style("#2196F3"))
        edit_btn.clicked.connect(self.edit_sheet)
        buttons_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️ حذف")
        delete_btn.setStyleSheet(self.get_button_style("#F44336"))
        delete_btn.clicked.connect(self.delete_sheet)
        buttons_layout.addWidget(delete_btn)
        
        refresh_btn = QPushButton("🔄 بروزرسانی")
        refresh_btn.setStyleSheet(self.get_button_style("#FF9800"))
        refresh_btn.clicked.connect(self.load_data)
        buttons_layout.addWidget(refresh_btn)
        
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
    
    def load_data(self):
        """بارگذاری داده‌ها"""
        try:
            configs = db_manager.get_all_sheet_configs()
            
            self.table.setRowCount(len(configs))
            
            for row, config in enumerate(configs):
                # شناسه
                self.table.setItem(row, 0, QTableWidgetItem(str(config.id)))
                
                # نام
                name_item = QTableWidgetItem(config.name)
                name_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                self.table.setItem(row, 1, name_item)
                
                # آدرس (کوتاه شده)
                url = config.sheet_url[:50] + "..." if len(config.sheet_url) > 50 else config.sheet_url
                self.table.setItem(row, 2, QTableWidgetItem(url))
                
                # برگه
                self.table.setItem(row, 3, QTableWidgetItem(config.worksheet_name or "Sheet1"))
                
                # وضعیت
                status_item = QTableWidgetItem("✅ فعال" if config.is_active else "❌ غیرفعال")
                if config.is_active:
                    status_item.setForeground(QColor("#4CAF50"))
                else:
                    status_item.setForeground(QColor("#F44336"))
                self.table.setItem(row, 4, status_item)
                
                # تاریخ
                date_str = config.created_at.strftime("%Y-%m-%d %H:%M")
                self.table.setItem(row, 5, QTableWidgetItem(date_str))
            
            # مرتب‌سازی
            self.table.sortItems(0, Qt.SortOrder.DescendingOrder)
            
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"❌ خطا در بارگذاری داده‌ها:\n{str(e)}")
    
    def add_sheet(self):
        """افزودن شیت جدید"""
        dialog = SheetConfigDialog(self)
        if dialog.exec():
            self.load_data()
    
    def edit_sheet(self):
        """ویرایش شیت"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "هشدار", "لطفاً یک شیت را انتخاب کنید!")
            return
        
        config_id = int(self.table.item(current_row, 0).text())
        config = db_manager.get_sheet_config(config_id)
        
        if config:
            dialog = SheetConfigDialog(self, config)
            if dialog.exec():
                self.load_data()
    
    def delete_sheet(self):
        """حذف شیت"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "هشدار", "لطفاً یک شیت را انتخاب کنید!")
            return
        
        config_id = int(self.table.item(current_row, 0).text())
        config_name = self.table.item(current_row, 1).text()
        
        reply = QMessageBox.question(
            self,
            "تایید حذف",
            f"آیا از حذف شیت '{config_name}' مطمئن هستید؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = db_manager.delete_sheet_config(config_id)
            
            if success:
                QMessageBox.information(self, "موفق", "✅ " + message)
                self.load_data()
            else:
                QMessageBox.critical(self, "خطا", "❌ " + message)
    
    def get_button_style(self, color):
        """استایل دکمه"""
        return f"""
            QPushButton {{
                background: {color};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 10pt;
                font-weight: bold;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
        """
