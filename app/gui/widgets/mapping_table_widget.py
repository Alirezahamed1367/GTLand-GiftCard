"""
Widget اختصاصی برای Mapping ستون‌های دیتابیس به Excel
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QComboBox, QLabel, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from typing import List, Dict, Optional


class MappingTableWidget(QWidget):
    """
    Widget برای Mapping ستون‌های دیتابیس به Excel
    """
    
    # Signal برای اطلاع تغییرات
    mapping_changed = pyqtSignal(dict)  # ارسال Mapping های جدید
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_columns = []  # لیست ستون‌های دیتابیس
        self.excel_columns = []  # لیست ستون‌های Excel
        self.sample_data = {}  # نمونه داده برای پیش‌نمایش
        self.init_ui()
    
    def init_ui(self):
        """راه‌اندازی رابط کاربری"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # عنوان و راهنما
        title_label = QLabel("🗺️ نقشه‌برداری ستون‌ها (Mapping)")
        title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2196F3; padding: 5px;")
        layout.addWidget(title_label)
        
        help_label = QLabel(
            "ستون‌های دیتابیس را به ستون‌های Excel متصل کنید.\n"
            "برای تطبیق خودکار، دکمه 'تطبیق خودکار' را بزنید."
        )
        help_label.setStyleSheet("color: #666; font-size: 9pt; padding: 5px;")
        layout.addWidget(help_label)
        
        # جدول Mapping
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "ستون دیتابیس",
            "ستون Excel مقصد",
            "پیش‌نمایش داده",
            "عملیات"
        ])
        
        # تنظیمات جدول - Responsive height (30% صفحه یا حداقل 250px)
        try:
            from PyQt6.QtGui import QScreen
            from PyQt6.QtWidgets import QApplication
            screen = QApplication.primaryScreen().availableGeometry()
            dynamic_height = max(250, int(screen.height() * 0.3))
            self.table.setMinimumHeight(dynamic_height)
        except:
            self.table.setMinimumHeight(300)  # Fallback
        
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # عرض ستون‌ها
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # ستون دیتابیس
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # ستون Excel
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # پیش‌نمایش
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # عملیات
        self.table.setColumnWidth(3, 80)
        
        layout.addWidget(self.table)
        
        # دکمه‌های کنترل
        buttons_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ افزودن ردیف")
        add_btn.setStyleSheet(self.get_button_style("#4CAF50"))
        add_btn.clicked.connect(self.add_row)
        
        remove_btn = QPushButton("➖ حذف ردیف")
        remove_btn.setStyleSheet(self.get_button_style("#F44336"))
        remove_btn.clicked.connect(self.remove_selected_row)
        
        auto_map_btn = QPushButton("🔗 تطبیق خودکار")
        auto_map_btn.setStyleSheet(self.get_button_style("#2196F3"))
        auto_map_btn.clicked.connect(self.auto_map)
        
        clear_btn = QPushButton("🗑️ پاک کردن همه")
        clear_btn.setStyleSheet(self.get_button_style("#FF9800"))
        clear_btn.clicked.connect(self.clear_all)
        
        buttons_layout.addWidget(add_btn)
        buttons_layout.addWidget(remove_btn)
        buttons_layout.addWidget(auto_map_btn)
        buttons_layout.addWidget(clear_btn)
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
        # آمار
        self.stats_label = QLabel("آماده برای Mapping")
        self.stats_label.setStyleSheet("color: #666; font-size: 9pt; padding: 5px;")
        layout.addWidget(self.stats_label)
    
    def set_db_columns(self, columns: List[Dict]):
        """
        تنظیم لیست ستون‌های دیتابیس
        
        Args:
            columns: لیست دیکشنری ستون‌ها (از DataHelper)
        """
        self.db_columns = columns
        self.update_stats()
        
        # اگر Excel columns هم آماده است، Mapping های خالی اضافه کن
        if self.excel_columns and self.table.rowCount() == 0:
            for _ in range(min(len(self.db_columns), 5)):  # حداکثر 5 ردیف
                self.add_row()
    
    def set_excel_columns(self, columns: List[Dict]):
        """
        تنظیم لیست ستون‌های Excel
        
        Args:
            columns: لیست دیکشنری ستون‌ها (از ExcelHelper)
        """
        self.excel_columns = columns
        self.update_stats()
        
        # بروزرسانی Dropdown های موجود
        for row in range(self.table.rowCount()):
            excel_combo = self.table.cellWidget(row, 1)
            if excel_combo:
                current_value = excel_combo.currentText()
                self.populate_excel_combo(excel_combo)
                # بازگردانی مقدار قبلی
                index = excel_combo.findText(current_value)
                if index >= 0:
                    excel_combo.setCurrentIndex(index)
    
    def set_sample_data(self, data: Dict[str, any]):
        """
        تنظیم نمونه داده برای پیش‌نمایش
        
        Args:
            data: دیکشنری نمونه داده
        """
        self.sample_data = data
        self.update_all_previews()
    
    def add_row(self, db_column: str = None, excel_column: str = None):
        """
        افزودن ردیف جدید به جدول
        
        Args:
            db_column: نام ستون دیتابیس (اختیاری)
            excel_column: نام/حرف ستون Excel (اختیاری)
        """
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # ستون 1: Dropdown ستون‌های دیتابیس
        db_combo = QComboBox()
        db_combo.addItem("-- انتخاب کنید --", None)
        
        for col in self.db_columns:
            display_text = col['name']
            if col.get('sample_value'):
                sample = str(col['sample_value'])[:30]
                display_text += f" (نمونه: {sample})"
            db_combo.addItem(display_text, col['name'])
        
        # تنظیم مقدار اولیه
        if db_column:
            index = db_combo.findData(db_column)
            if index >= 0:
                db_combo.setCurrentIndex(index)
        
        db_combo.currentIndexChanged.connect(lambda: self.on_mapping_changed(row))
        self.table.setCellWidget(row, 0, db_combo)
        
        # ستون 2: Dropdown ستون‌های Excel
        excel_combo = QComboBox()
        self.populate_excel_combo(excel_combo)
        
        # تنظیم مقدار اولیه
        if excel_column:
            index = excel_combo.findText(excel_column)
            if index >= 0:
                excel_combo.setCurrentIndex(index)
        
        excel_combo.currentIndexChanged.connect(lambda: self.on_mapping_changed(row))
        self.table.setCellWidget(row, 1, excel_combo)
        
        # ستون 3: پیش‌نمایش
        preview_label = QLabel("--")
        preview_label.setStyleSheet("color: #666; padding: 5px;")
        self.table.setCellWidget(row, 2, preview_label)
        
        # ستون 4: دکمه حذف
        delete_btn = QPushButton("🗑️")
        delete_btn.setMaximumWidth(60)
        delete_btn.clicked.connect(lambda: self.remove_row(row))
        self.table.setCellWidget(row, 3, delete_btn)
        
        # بروزرسانی پیش‌نمایش
        self.update_preview(row)
        self.update_stats()
    
    def populate_excel_combo(self, combo: QComboBox):
        """پر کردن Dropdown ستون‌های Excel"""
        current = combo.currentText()
        combo.clear()
        combo.addItem("-- انتخاب کنید --", None)
        
        for col in self.excel_columns:
            # نمایش: A (نام ستون) یا فقط A
            if col.get('name'):
                display_text = f"{col['letter']} ({col['name']})"
            else:
                display_text = col['letter']
            
            combo.addItem(display_text, col['letter'])
        
        # بازگردانی مقدار قبلی
        if current:
            index = combo.findText(current)
            if index >= 0:
                combo.setCurrentIndex(index)
    
    def remove_row(self, row: int):
        """حذف یک ردیف"""
        if row < self.table.rowCount():
            self.table.removeRow(row)
            self.update_stats()
            self.emit_mapping_changed()
    
    def remove_selected_row(self):
        """حذف ردیف انتخاب شده"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.remove_row(current_row)
    
    def clear_all(self):
        """پاک کردن تمام ردیف‌ها"""
        self.table.setRowCount(0)
        self.update_stats()
        self.emit_mapping_changed()
    
    def auto_map(self):
        """تطبیق خودکار بر اساس نام یکسان یا مشابه"""
        if not self.db_columns or not self.excel_columns:
            return
        
        # پاک کردن Mapping های قبلی
        self.clear_all()
        
        # ساخت دیکشنری نام‌های Excel
        excel_names = {}
        for col in self.excel_columns:
            excel_names[col['letter']] = col.get('name', col['letter'])
        
        # تطبیق
        for db_col in self.db_columns:
            db_name = db_col['name'].lower().strip()
            matched = False
            
            # 1. تطبیق دقیق
            for excel_letter, excel_name in excel_names.items():
                if excel_name and db_name == excel_name.lower().strip():
                    self.add_row(db_col['name'], excel_letter)
                    matched = True
                    break
            
            # 2. تطبیق تقریبی (شامل بودن)
            if not matched:
                for excel_letter, excel_name in excel_names.items():
                    if excel_name:
                        excel_clean = excel_name.lower().strip()
                        if db_name in excel_clean or excel_clean in db_name:
                            self.add_row(db_col['name'], excel_letter)
                            matched = True
                            break
        
        # اگر هیچ تطبیقی نشد، یک ردیف خالی اضافه کن
        if self.table.rowCount() == 0:
            self.add_row()
        
        self.update_stats()
    
    def on_mapping_changed(self, row: int):
        """هنگام تغییر Mapping یک ردیف"""
        self.update_preview(row)
        self.emit_mapping_changed()
    
    def update_preview(self, row: int):
        """بروزرسانی پیش‌نمایش یک ردیف"""
        if row >= self.table.rowCount():
            return
        
        db_combo = self.table.cellWidget(row, 0)
        preview_label = self.table.cellWidget(row, 2)
        
        if not db_combo or not preview_label:
            return
        
        db_column = db_combo.currentData()
        
        if db_column and db_column in self.sample_data:
            value = self.sample_data[db_column]
            preview_text = str(value)[:30] if value else "(خالی)"
            preview_label.setText(preview_text)
            preview_label.setStyleSheet("color: #4CAF50; font-weight: bold; padding: 5px;")
        else:
            preview_label.setText("--")
            preview_label.setStyleSheet("color: #666; padding: 5px;")
    
    def update_all_previews(self):
        """بروزرسانی تمام پیش‌نمایش‌ها"""
        for row in range(self.table.rowCount()):
            self.update_preview(row)
    
    def update_stats(self):
        """بروزرسانی آمار"""
        total_mappings = self.table.rowCount()
        valid_mappings = 0
        
        for row in range(self.table.rowCount()):
            db_combo = self.table.cellWidget(row, 0)
            excel_combo = self.table.cellWidget(row, 1)
            
            if db_combo and excel_combo:
                if db_combo.currentData() and excel_combo.currentData():
                    valid_mappings += 1
        
        stats_text = (
            f"📊 آمار: {total_mappings} ردیف | "
            f"✅ {valid_mappings} Mapping معتبر | "
            f"📋 {len(self.db_columns)} ستون دیتابیس | "
            f"📄 {len(self.excel_columns)} ستون Excel"
        )
        self.stats_label.setText(stats_text)
    
    def get_mappings(self) -> Dict[str, str]:
        """
        دریافت Mapping های تنظیم شده
        
        Returns:
            دیکشنری {ستون_دیتابیس: ستون_Excel}
        """
        mappings = {}
        
        for row in range(self.table.rowCount()):
            db_combo = self.table.cellWidget(row, 0)
            excel_combo = self.table.cellWidget(row, 1)
            
            if db_combo and excel_combo:
                db_col = db_combo.currentData()
                excel_col = excel_combo.currentData()
                
                if db_col and excel_col:
                    mappings[db_col] = excel_col
        
        return mappings
    
    def set_mappings(self, mappings: Dict[str, str]):
        """
        تنظیم Mapping ها (برای حالت ویرایش)
        
        Args:
            mappings: دیکشنری {ستون_دیتابیس: ستون_Excel}
        """
        self.clear_all()
        
        for db_col, excel_col in mappings.items():
            self.add_row(db_col, excel_col)
        
        self.update_stats()
    
    def emit_mapping_changed(self):
        """ارسال Signal تغییر"""
        mappings = self.get_mappings()
        self.mapping_changed.emit(mappings)
    
    def get_button_style(self, color: str) -> str:
        """استایل دکمه"""
        return f"""
            QPushButton {{
                background: {color};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 9pt;
            }}
            QPushButton:hover {{
                opacity: 0.9;
                background: {color};
            }}
            QPushButton:pressed {{
                background: {color};
            }}
        """


if __name__ == "__main__":
    # تست
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # داده‌های نمونه
    db_cols = [
        {'name': 'نام محصول', 'sample_value': 'لپ‌تاپ', 'frequency': 100},
        {'name': 'قیمت', 'sample_value': '25000000', 'frequency': 100},
        {'name': 'تعداد', 'sample_value': '5', 'frequency': 100},
    ]
    
    excel_cols = [
        {'letter': 'A', 'index': 1, 'name': 'کد'},
        {'letter': 'B', 'index': 2, 'name': 'نام'},
        {'letter': 'C', 'index': 3, 'name': 'قیمت'},
        {'letter': 'D', 'index': 4, 'name': 'موجودی'},
    ]
    
    sample_data = {
        'نام محصول': 'لپ‌تاپ',
        'قیمت': '25000000',
        'تعداد': '5'
    }
    
    # ساخت Widget
    widget = MappingTableWidget()
    widget.set_db_columns(db_cols)
    widget.set_excel_columns(excel_cols)
    widget.set_sample_data(sample_data)
    
    # اتصال Signal
    widget.mapping_changed.connect(lambda m: print(f"Mappings changed: {m}"))
    
    widget.setWindowTitle("تست Mapping Widget")
    widget.resize(900, 600)
    widget.show()
    
    sys.exit(app.exec())
