"""
دیالوگ نمایش جزئیات داده‌های یک شیت
Dialog for displaying detailed records of a specific sheet
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QPushButton, QLabel, QCheckBox,
    QComboBox, QMessageBox, QHeaderView, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from typing import Dict, List, Optional
from datetime import datetime

from app.core.database import DatabaseManager
from app.utils.ui_constants import COLORS, FONTS


class SheetDetailsDialog(QDialog):
    """دیالوگ تمام صفحه برای نمایش جزئیات داده‌های یک شیت"""
    
    data_updated = pyqtSignal()  # سیگنال برای refresh کردن
    
    def __init__(self, sheet_config_id: int, sheet_name: str, parent=None):
        super().__init__(parent)
        self.sheet_config_id = sheet_config_id
        self.sheet_name = sheet_name
        self.db_manager = DatabaseManager()
        
        # متغیرهای Pagination
        self.page_size = 200  # 200 ردیف در هر صفحه
        self.current_page = 1
        self.total_pages = 1
        self.total_records = 0
        self.current_filter = "all"  # all, exported, not_exported, updated
        
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        """تنظیمات رابط کاربری"""
        self.setWindowTitle(f"جزئیات داده‌ها - {self.sheet_name}")
        self.setWindowState(Qt.WindowState.WindowMaximized)  # تمام صفحه
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        # Layout اصلی
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # ============ Header Section ============
        header_layout = QHBoxLayout()
        
        # عنوان
        title = QLabel(f"📊 {self.sheet_name}")
        title.setFont(FONTS['large_bold'])
        title.setStyleSheet(f"color: {COLORS['primary']}; padding: 5px;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # دکمه بازگشت
        self.back_btn = QPushButton("◀ بازگشت")
        self.back_btn.setFont(FONTS['medium'])
        self.back_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['secondary']};
                color: white;
                padding: 8px 20px;
                border-radius: 5px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent']};
            }}
        """)
        self.back_btn.clicked.connect(self.accept)
        header_layout.addWidget(self.back_btn)
        
        main_layout.addLayout(header_layout)
        
        # ============ Filter & Stats Section ============
        filter_layout = QHBoxLayout()
        
        # فیلتر
        filter_label = QLabel("فیلتر:")
        filter_label.setFont(FONTS['medium'])
        filter_layout.addWidget(filter_label)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            "همه داده‌ها",
            "Export شده",
            "Export نشده",
            "نیاز به Re-export"
        ])
        self.filter_combo.setFont(FONTS['medium'])
        self.filter_combo.currentIndexChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.filter_combo)
        
        filter_layout.addSpacing(20)
        
        # آمار
        self.stats_label = QLabel()
        self.stats_label.setFont(FONTS['medium'])
        filter_layout.addWidget(self.stats_label)
        
        filter_layout.addStretch()
        
        main_layout.addLayout(filter_layout)
        
        # ============ Action Buttons ============
        action_layout = QHBoxLayout()
        
        # انتخاب همه
        self.select_all_btn = QPushButton("✓ انتخاب همه")
        self.select_all_btn.setFont(FONTS['medium'])
        self.select_all_btn.clicked.connect(self.select_all)
        action_layout.addWidget(self.select_all_btn)
        
        # عدم انتخاب همه
        self.deselect_all_btn = QPushButton("✗ عدم انتخاب همه")
        self.deselect_all_btn.setFont(FONTS['medium'])
        self.deselect_all_btn.clicked.connect(self.deselect_all)
        action_layout.addWidget(self.deselect_all_btn)
        
        action_layout.addSpacing(20)
        
        # Export
        self.export_btn = QPushButton("📤 Export موارد انتخابی")
        self.export_btn.setFont(FONTS['medium'])
        self.export_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['success']};
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: #27ae60;
            }}
        """)
        self.export_btn.clicked.connect(self.export_selected)
        action_layout.addWidget(self.export_btn)
        
        # حذف
        self.delete_btn = QPushButton("🗑 حذف موارد انتخابی")
        self.delete_btn.setFont(FONTS['medium'])
        self.delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['danger']};
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: #c0392b;
            }}
        """)
        self.delete_btn.clicked.connect(self.delete_selected)
        action_layout.addWidget(self.delete_btn)
        
        action_layout.addStretch()
        
        main_layout.addLayout(action_layout)
        
        # ============ Table ============
        self.table = QTableWidget()
        self.table.setFont(FONTS['medium'])
        self.table.setColumnCount(8)  # کاهش از 9 به 8
        self.table.setHorizontalHeaderLabels([
            "انتخاب", "ردیف", "ID", "داده", "تاریخ استخراج",
            "Export", "Update", "عملیات"
        ])
        
        # تنظیمات Table
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(0, 60)   # انتخاب
        self.table.setColumnWidth(1, 70)   # ردیف
        self.table.setColumnWidth(2, 80)   # ID
        self.table.setColumnWidth(3, 400)  # داده (بزرگتر)
        self.table.setColumnWidth(4, 140)  # تاریخ
        self.table.setColumnWidth(5, 80)   # Export
        self.table.setColumnWidth(6, 80)   # Update
        self.table.setColumnWidth(7, 200)  # عملیات
        
        main_layout.addWidget(self.table)
        
        # ============ Pagination (Bottom) ============
        pagination_layout = QHBoxLayout()
        
        # اطلاعات صفحه
        self.page_info = QLabel()
        self.page_info.setFont(FONTS['medium'])
        pagination_layout.addWidget(self.page_info)
        
        pagination_layout.addStretch()
        
        # دکمه صفحه قبل
        self.prev_btn = QPushButton("▶ قبلی")
        self.prev_btn.setFont(FONTS['medium'])
        self.prev_btn.clicked.connect(self.prev_page)
        pagination_layout.addWidget(self.prev_btn)
        
        # شماره صفحه
        self.current_page_label = QLabel()
        self.current_page_label.setFont(FONTS['large_bold'])
        self.current_page_label.setStyleSheet(f"color: {COLORS['primary']}; padding: 0 15px;")
        pagination_layout.addWidget(self.current_page_label)
        
        # دکمه صفحه بعد
        self.next_btn = QPushButton("بعدی ◀")
        self.next_btn.setFont(FONTS['medium'])
        self.next_btn.clicked.connect(self.next_page)
        pagination_layout.addWidget(self.next_btn)
        
        pagination_layout.addStretch()
        
        # تعداد در هر صفحه
        page_size_label = QLabel("تعداد در صفحه:")
        page_size_label.setFont(FONTS['medium'])
        pagination_layout.addWidget(page_size_label)
        
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["100", "200", "300", "500"])
        self.page_size_combo.setCurrentText("200")
        self.page_size_combo.setFont(FONTS['medium'])
        self.page_size_combo.currentTextChanged.connect(self.on_page_size_changed)
        pagination_layout.addWidget(self.page_size_combo)
        
        main_layout.addLayout(pagination_layout)
        
        # ============ Back Button (Bottom) ============
        bottom_back_layout = QHBoxLayout()
        bottom_back_layout.addStretch()
        
        bottom_back_btn = QPushButton("◀ بازگشت")
        bottom_back_btn.setFont(FONTS['medium'])
        bottom_back_btn.setStyleSheet(self.back_btn.styleSheet())
        bottom_back_btn.clicked.connect(self.accept)
        bottom_back_layout.addWidget(bottom_back_btn)
        
        main_layout.addLayout(bottom_back_layout)
        
        self.setLayout(main_layout)
        
    def load_data(self):
        """بارگذاری داده‌ها با Pagination"""
        try:
            # محاسبه Offset
            offset = (self.current_page - 1) * self.page_size
            
            # بارگذاری بر اساس فیلتر
            if self.current_filter == "all":
                data_list, total = self.db_manager.get_all_sales_data_paginated(
                    limit=self.page_size,
                    offset=offset,
                    sheet_config_id=self.sheet_config_id
                )
            elif self.current_filter == "exported":
                data_list, total = self.db_manager.get_sales_data_by_export_status_paginated(
                    is_exported=True,
                    limit=self.page_size,
                    offset=offset,
                    sheet_config_id=self.sheet_config_id
                )
            elif self.current_filter == "not_exported":
                data_list, total = self.db_manager.get_sales_data_by_export_status_paginated(
                    is_exported=False,
                    limit=self.page_size,
                    offset=offset,
                    sheet_config_id=self.sheet_config_id
                )
            else:  # updated
                data_list, total = self.db_manager.get_updated_sales_data_paginated(
                    limit=self.page_size,
                    offset=offset,
                    sheet_config_id=self.sheet_config_id
                )
            
            self.total_records = total
            self.total_pages = (total + self.page_size - 1) // self.page_size
            
            # پاک کردن Table
            self.table.setRowCount(0)
            
            # محاسبه شماره ردیف شروع
            start_row_number = offset + 1
            
            # پر کردن Table
            for idx, data in enumerate(data_list):
                row = self.table.rowCount()
                self.table.insertRow(row)
                
                # Checkbox
                checkbox = QCheckBox()
                checkbox.setStyleSheet("QCheckBox { margin-right: 15px; }")
                checkbox_widget = QWidget()
                checkbox_layout = QHBoxLayout(checkbox_widget)
                checkbox_layout.addWidget(checkbox)
                checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                checkbox_layout.setContentsMargins(0, 0, 0, 0)
                self.table.setCellWidget(row, 0, checkbox_widget)
                
                # شماره ردیف (ردیف واقعی، نه index)
                row_number_item = QTableWidgetItem(str(start_row_number + idx))
                row_number_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 1, row_number_item)
                
                # ID
                id_item = QTableWidgetItem(str(data.id))
                id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 2, id_item)
                
                # استخراج داده‌ها از JSON
                json_data = data.data if isinstance(data.data, dict) else {}
                
                # نمایش خلاصه داده (3 فیلد اول)
                data_preview = ", ".join([f"{k}: {v}" for k, v in list(json_data.items())[:3]])
                if len(json_data) > 3:
                    data_preview += "..."
                
                data_item = QTableWidgetItem(data_preview or "بدون داده")
                self.table.setItem(row, 3, data_item)
                
                # تاریخ استخراج
                extract_date = data.extracted_at.strftime("%Y/%m/%d %H:%M") if data.extracted_at else "-"
                extract_item = QTableWidgetItem(extract_date)
                extract_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 4, extract_item)
                
                # حذف ستون‌های اضافی (phone, address)
                # حذف ستون‌های اضافی (phone, address)
                
                # وضعیت Export
                export_text = "✓" if data.is_exported else "✗"
                export_item = QTableWidgetItem(export_text)
                export_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if data.is_exported:
                    export_item.setBackground(QColor(COLORS['success']))
                    export_item.setForeground(QColor("white"))
                else:
                    export_item.setBackground(QColor(COLORS['danger']))
                    export_item.setForeground(QColor("white"))
                self.table.setItem(row, 5, export_item)
                
                # وضعیت Update
                update_text = "⚠" if data.is_updated else "-"
                update_item = QTableWidgetItem(update_text)
                update_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if data.is_updated:
                    update_item.setBackground(QColor(COLORS['warning']))
                    update_item.setForeground(QColor("white"))
                self.table.setItem(row, 6, update_item)
                
                # دکمه‌های عملیات
                ops_widget = self.create_operation_buttons(data.id)
                self.table.setCellWidget(row, 7, ops_widget)
            
            # آپدیت آمار و Pagination
            self.update_stats()
            self.update_pagination_controls()
            
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در بارگذاری داده‌ها:\n{str(e)}")
    
    def create_operation_buttons(self, data_id: int) -> QWidget:
        """ایجاد دکمه‌های عملیات برای هر ردیف"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)
        
        # دکمه نمایش تغییرات (فقط برای ردیف‌های updated)
        data = self.db_manager.get_sales_data_by_id(data_id)
        if data and data.is_updated:
            changes_btn = QPushButton("🔍")
            changes_btn.setToolTip("نمایش تغییرات")
            changes_btn.setFixedSize(35, 25)
            changes_btn.setStyleSheet(f"background-color: {COLORS['warning']}; color: white; font-weight: bold;")
            changes_btn.clicked.connect(lambda: self.show_changes(data_id))
            layout.addWidget(changes_btn)
        
        # دکمه Export
        export_btn = QPushButton("📤")
        export_btn.setToolTip("Export این ردیف")
        export_btn.setFixedSize(35, 25)
        export_btn.clicked.connect(lambda: self.export_single(data_id))
        layout.addWidget(export_btn)
        
        # دکمه ویرایش
        edit_btn = QPushButton("✏")
        edit_btn.setToolTip("ویرایش این ردیف")
        edit_btn.setFixedSize(35, 25)
        edit_btn.clicked.connect(lambda: self.edit_single(data_id))
        layout.addWidget(edit_btn)
        
        # دکمه حذف
        delete_btn = QPushButton("🗑")
        delete_btn.setToolTip("حذف این ردیف")
        delete_btn.setFixedSize(35, 25)
        delete_btn.setStyleSheet(f"background-color: {COLORS['danger']}; color: white;")
        delete_btn.clicked.connect(lambda: self.delete_single(data_id))
        layout.addWidget(delete_btn)
        
        layout.addStretch()
        
        return widget
    
    def show_changes(self, data_id: int):
        """نمایش جزئیات تغییرات یک ردیف"""
        try:
            data = self.db_manager.get_sales_data_by_id(data_id)
            if not data:
                QMessageBox.warning(self, "خطا", "داده یافت نشد!")
                return
            
            # نمایش اطلاعات تغییرات
            changes_text = f"""
📊 جزئیات تغییرات - ID: {data.id}

🔑 کلید یکتا: {data.unique_key}
📍 شماره ردیف: {data.row_number}

⚠️ وضعیت: ویرایش شده (نیاز به Re-export)
🔢 تعداد دفعات ویرایش: {data.update_count}

📅 تاریخ استخراج اولیه: {data.extracted_at.strftime('%Y/%m/%d %H:%M:%S') if data.extracted_at else '-'}
📅 آخرین بروزرسانی: {data.updated_at.strftime('%Y/%m/%d %H:%M:%S') if data.updated_at else '-'}

📦 داده‌های فعلی:
{self.format_json_data(data.data)}

💡 توضیحات:
این ردیف پس از Export شدن، تغییراتی در گوگل شیت داشته است.
برای همگام‌سازی، دوباره Export کنید تا تغییرات اعمال شود.

✅ Export اولیه: {data.exported_at.strftime('%Y/%m/%d %H:%M:%S') if data.exported_at else 'هنوز Export نشده'}
🔄 نوع Export: {data.export_type or 'مشخص نشده'}
            """
            
            QMessageBox.information(self, "جزئیات تغییرات", changes_text)
            
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در نمایش تغییرات:\n{str(e)}")
    
    def format_json_data(self, data_dict: dict) -> str:
        """فرمت زیبای JSON"""
        import json
        try:
            return json.dumps(data_dict, ensure_ascii=False, indent=2)
        except:
            return str(data_dict)
    
    def update_stats(self):
        """آپدیت نمایش آمار"""
        filter_names = {
            "all": "همه",
            "exported": "Export شده",
            "not_exported": "Export نشده",
            "updated": "نیاز به Re-export"
        }
        
        filter_text = filter_names.get(self.current_filter, "همه")
        self.stats_label.setText(
            f"📊 {filter_text}: {self.total_records:,} ردیف"
        )
    
    def update_pagination_controls(self):
        """آپدیت کنترل‌های Pagination"""
        # اطلاعات صفحه
        start = (self.current_page - 1) * self.page_size + 1
        end = min(self.current_page * self.page_size, self.total_records)
        self.page_info.setText(f"نمایش {start:,} تا {end:,} از {self.total_records:,}")
        
        # شماره صفحه
        self.current_page_label.setText(f"صفحه {self.current_page} از {self.total_pages}")
        
        # فعال/غیرفعال کردن دکمه‌ها
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < self.total_pages)
    
    def prev_page(self):
        """صفحه قبل"""
        if self.current_page > 1:
            self.current_page -= 1
            self.load_data()
    
    def next_page(self):
        """صفحه بعد"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_data()
    
    def on_page_size_changed(self, text: str):
        """تغییر تعداد ردیف در صفحه"""
        self.page_size = int(text)
        self.current_page = 1
        self.load_data()
    
    def on_filter_changed(self, index: int):
        """تغییر فیلتر"""
        filters = ["all", "exported", "not_exported", "updated"]
        self.current_filter = filters[index]
        self.current_page = 1
        self.load_data()
    
    def select_all(self):
        """انتخاب همه ردیف‌های صفحه جاری"""
        for row in range(self.table.rowCount()):
            checkbox_widget = self.table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(True)
    
    def deselect_all(self):
        """عدم انتخاب همه"""
        for row in range(self.table.rowCount()):
            checkbox_widget = self.table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(False)
    
    def get_selected_ids(self) -> List[int]:
        """دریافت ID ردیف‌های انتخاب شده"""
        selected = []
        for row in range(self.table.rowCount()):
            checkbox_widget = self.table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    id_item = self.table.item(row, 2)
                    if id_item:
                        selected.append(int(id_item.text()))
        return selected
    
    def export_selected(self):
        """Export موارد انتخابی"""
        selected_ids = self.get_selected_ids()
        if not selected_ids:
            QMessageBox.warning(self, "هشدار", "لطفاً حداقل یک ردیف انتخاب کنید.")
            return
        
        # باز کردن دیالوگ Export
        from app.gui.dialogs.export_dialog import ExportDialog
        dialog = ExportDialog(selected_ids, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.data_updated.emit()
            self.load_data()
    
    def delete_selected(self):
        """حذف موارد انتخابی"""
        selected_ids = self.get_selected_ids()
        if not selected_ids:
            QMessageBox.warning(self, "هشدار", "لطفاً حداقل یک ردیف انتخاب کنید.")
            return
        
        reply = QMessageBox.question(
            self,
            "تأیید حذف",
            f"آیا از حذف {len(selected_ids)} ردیف اطمینان دارید؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success_count = 0
            for data_id in selected_ids:
                success, _ = self.db_manager.delete_sales_data(data_id)
                if success:
                    success_count += 1
            
            QMessageBox.information(
                self,
                "نتیجه",
                f"{success_count} از {len(selected_ids)} ردیف با موفقیت حذف شد."
            )
            
            self.data_updated.emit()
            self.load_data()
    
    def export_single(self, data_id: int):
        """Export یک ردیف"""
        from app.gui.dialogs.export_dialog import ExportDialog
        dialog = ExportDialog([data_id], self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.data_updated.emit()
            self.load_data()
    
    def edit_single(self, data_id: int):
        """ویرایش یک ردیف"""
        from app.gui.dialogs.edit_data_dialog import EditDataDialog
        dialog = EditDataDialog(data_id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.data_updated.emit()
            self.load_data()
    
    def delete_single(self, data_id: int):
        """حذف یک ردیف"""
        reply = QMessageBox.question(
            self,
            "تأیید حذف",
            "آیا از حذف این ردیف اطمینان دارید؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.db_manager.delete_sales_data(data_id)
            if success:
                QMessageBox.information(self, "موفق", "ردیف با موفقیت حذف شد.")
                self.data_updated.emit()
                self.load_data()
            else:
                QMessageBox.critical(self, "خطا", f"خطا در حذف:\n{message}")
