"""
Widget مدیریت داده‌های استخراج شده

توسعه‌دهنده: علیرضا حامد
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QMessageBox, QComboBox,
    QLineEdit, QHeaderView, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QAction
from datetime import datetime
import json

from app.core.database import db_manager
from app.core.logger import app_logger
from app.gui.dialogs.edit_data_dialog import EditDataDialog
from app.gui.dialogs.advanced_export_dialog import AdvancedExportDialog


class DataViewerWidget(QWidget):
    """Widget نمایش و مدیریت داده‌های استخراج شده"""
    
    data_updated = pyqtSignal()  # سیگنال بروزرسانی داده
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_filter = "all"  # all, extracted, exported, updated
        self.selected_sheet_config_id = None  # فیلتر بر اساس SheetConfig (None = همه)
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        """راه‌اندازی رابط کاربری"""
        layout = QVBoxLayout(self)
        
        # عنوان
        title_label = QLabel("📊 مدیریت داده‌های استخراج شده")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2196F3; padding: 10px;")
        layout.addWidget(title_label)
        
        # نوار ابزار
        toolbar = QHBoxLayout()
        
        # فیلتر شیت (جدید!)
        toolbar.addWidget(QLabel("📋 شیت:"))
        
        self.sheet_combo = QComboBox()
        self.sheet_combo.addItem("همه شیت‌ها", None)
        self.load_sheet_configs()
        self.sheet_combo.currentIndexChanged.connect(self.on_sheet_changed)
        toolbar.addWidget(self.sheet_combo)
        
        toolbar.addWidget(QLabel(" | "))
        
        # فیلتر وضعیت
        toolbar.addWidget(QLabel("🔍 وضعیت:"))
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            "همه داده‌ها",
            "فقط استخراج شده (بدون Export)",
            "Export شده",
            "ویرایش شده (نیاز به Re-export)"
        ])
        self.filter_combo.currentIndexChanged.connect(self.on_filter_changed)
        toolbar.addWidget(self.filter_combo)
        
        toolbar.addStretch()
        
        # دکمه‌ها
        select_all_btn = QPushButton("☑️ انتخاب همه")
        select_all_btn.clicked.connect(self.select_all)
        select_all_btn.setStyleSheet(self.get_button_style("#9C27B0"))
        toolbar.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("⬜ لغو انتخاب همه")
        deselect_all_btn.clicked.connect(self.deselect_all)
        deselect_all_btn.setStyleSheet(self.get_button_style("#757575"))
        toolbar.addWidget(deselect_all_btn)
        
        refresh_btn = QPushButton("🔄 بروزرسانی")
        refresh_btn.clicked.connect(self.load_data)
        refresh_btn.setStyleSheet(self.get_button_style("#2196F3"))
        toolbar.addWidget(refresh_btn)
        
        export_selected_btn = QPushButton("📤 Export انتخاب شده")
        export_selected_btn.clicked.connect(self.export_selected)
        export_selected_btn.setStyleSheet(self.get_button_style("#4CAF50"))
        toolbar.addWidget(export_selected_btn)
        
        delete_btn = QPushButton("🗑️ حذف انتخاب شده")
        delete_btn.clicked.connect(self.delete_selected)
        delete_btn.setStyleSheet(self.get_button_style("#F44336"))
        toolbar.addWidget(delete_btn)
        
        layout.addLayout(toolbar)
        
        # آمار
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("background: #f5f5f5; padding: 10px; border-radius: 5px;")
        layout.addWidget(self.stats_label)
        
        # جدول داده‌ها
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "✅", "ID", "شیت", "داده", "تاریخ استخراج",
            "وضعیت Export", "تعداد ویرایش", "عملیات"
        ])
        
        # تنظیمات جدول
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.table)
    
    def load_sheet_configs(self):
        """بارگذاری لیست SheetConfig ها"""
        try:
            configs = db_manager.get_all_sheet_configs()
            
            self.sheet_combo.clear()
            self.sheet_combo.addItem("همه شیت‌ها", None)
            
            for config in configs:
                self.sheet_combo.addItem(
                    f"📊 {config.name}",
                    config.id
                )
        except Exception as e:
            app_logger.error(f"خطا در بارگذاری SheetConfig ها: {str(e)}")
    
    def on_sheet_changed(self, index):
        """تغییر شیت انتخابی"""
        self.selected_sheet_config_id = self.sheet_combo.itemData(index)
        self.load_data()
    
    def on_filter_changed(self, index):
        """تغییر فیلتر"""
        filters = {
            0: "all",
            1: "extracted",
            2: "exported",
            3: "updated"
        }
        self.current_filter = filters.get(index, "all")
        self.load_data()
    
    def select_all(self):
        """انتخاب همه ردیف‌ها"""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setCheckState(Qt.CheckState.Checked)
    
    def deselect_all(self):
        """لغو انتخاب همه ردیف‌ها"""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setCheckState(Qt.CheckState.Unchecked)
    
    def load_data(self):
        """بارگذاری داده‌ها از دیتابیس با فیلتر SheetConfig"""
        try:
            # بارگذاری بر اساس فیلتر وضعیت
            if self.current_filter == "all":
                data_list = db_manager.get_all_sales_data()
            elif self.current_filter == "extracted":
                data_list = db_manager.get_sales_data_by_export_status(is_exported=False)
            elif self.current_filter == "exported":
                data_list = db_manager.get_sales_data_by_export_status(is_exported=True)
            elif self.current_filter == "updated":
                data_list = db_manager.get_updated_sales_data()
            else:
                data_list = []
            
            # فیلتر بر اساس SheetConfig (اگر انتخاب شده باشد)
            if self.selected_sheet_config_id is not None:
                data_list = [d for d in data_list if d.sheet_config_id == self.selected_sheet_config_id]
            
            # پاک کردن جدول
            self.table.setRowCount(0)
            
            # پر کردن جدول
            for data in data_list:
                row = self.table.rowCount()
                self.table.insertRow(row)
                
                # چک‌باکس
                check_item = QTableWidgetItem()
                check_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                check_item.setCheckState(Qt.CheckState.Unchecked)
                self.table.setItem(row, 0, check_item)
                
                # ID
                self.table.setItem(row, 1, QTableWidgetItem(str(data.id)))
                
                # نام شیت
                sheet_name = data.sheet_config.name if data.sheet_config else "نامشخص"
                self.table.setItem(row, 2, QTableWidgetItem(sheet_name))
                
                # داده (نمایش خلاصه)
                data_summary = ", ".join([f"{k}: {v}" for k, v in list(data.data.items())[:2]]) + "..."
                data_item = QTableWidgetItem(data_summary)
                self.table.setItem(row, 3, data_item)
                
                # تاریخ استخراج
                extracted_date = data.extracted_at.strftime("%Y-%m-%d %H:%M") if data.extracted_at else "-"
                self.table.setItem(row, 4, QTableWidgetItem(extracted_date))
                
                # وضعیت Export
                if data.is_exported:
                    status_item = QTableWidgetItem("✅ Export شده")
                    status_item.setForeground(QColor("#4CAF50"))
                    if data.is_updated:
                        status_item.setText("⚠️ ویرایش شده")
                        status_item.setForeground(QColor("#FF9800"))
                else:
                    status_item = QTableWidgetItem("❌ Export نشده")
                    status_item.setForeground(QColor("#F44336"))
                
                self.table.setItem(row, 5, status_item)
                
                # تعداد ویرایش
                self.table.setItem(row, 6, QTableWidgetItem(str(data.update_count)))
                
                # دکمه عملیات
                actions_btn = QPushButton("⚙️ عملیات")
                actions_btn.clicked.connect(lambda checked, r=row: self.show_row_actions(r))
                self.table.setCellWidget(row, 7, actions_btn)
                
                # رنگ‌بندی ردیف بر اساس وضعیت
                if data.is_exported and not data.is_updated:
                    # Export شده - خاکستری
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        if item:
                            item.setBackground(QColor("#f5f5f5"))
            
            # بروزرسانی آمار
            self.update_stats()
            
        except Exception as e:
            app_logger.error(f"خطا در بارگذاری داده‌ها: {str(e)}")
            QMessageBox.critical(self, "خطا", f"❌ خطا در بارگذاری داده‌ها:\n{str(e)}")
    
    def refresh_data(self):
        """بروزرسانی داده‌ها (alias برای load_data)"""
        self.load_data()
    
    def update_stats(self):
        """بروزرسانی آمار با توجه به فیلتر SheetConfig"""
        try:
            # اگر شیت خاصی انتخاب شده
            if self.selected_sheet_config_id is not None:
                # آمار فقط برای این شیت
                all_data = db_manager.get_all_sales_data()
                filtered_data = [d for d in all_data if d.sheet_config_id == self.selected_sheet_config_id]
                
                total = len(filtered_data)
                exported = len([d for d in filtered_data if d.is_exported])
                not_exported = total - exported
                updated = len([d for d in filtered_data if d.is_updated])
                
                # نام شیت
                config = db_manager.get_sheet_config(self.selected_sheet_config_id)
                sheet_name = config.name if config else "نامشخص"
                
                stats_text = (
                    f"📋 شیت: {sheet_name} | "
                    f"📊 کل: {total} | "
                    f"✅ Export شده: {exported} | "
                    f"❌ Export نشده: {not_exported} | "
                    f"⚠️ نیاز به Re-export: {updated}"
                )
            else:
                # آمار کل (همه شیت‌ها)
                total = db_manager.get_sales_data_count()
                exported = db_manager.get_sales_data_count(is_exported=True)
                not_exported = total - exported
                updated = db_manager.get_updated_sales_data_count()
                
                stats_text = (
                    f"📊 کل (همه شیت‌ها): {total} | "
                    f"✅ Export شده: {exported} | "
                    f"❌ Export نشده: {not_exported} | "
                    f"⚠️ نیاز به Re-export: {updated}"
                )
            
            self.stats_label.setText(stats_text)
        except Exception as e:
            app_logger.error(f"خطا در بروزرسانی آمار: {str(e)}")
    
    def show_context_menu(self, position):
        """نمایش منوی کلیک راست"""
        menu = QMenu(self)
        
        view_action = QAction("👁️ مشاهده جزئیات", self)
        view_action.triggered.connect(self.view_details)
        menu.addAction(view_action)
        
        edit_action = QAction("✏️ ویرایش", self)
        edit_action.triggered.connect(self.edit_data)
        menu.addAction(edit_action)
        
        menu.addSeparator()
        
        export_action = QAction("📤 Export", self)
        export_action.triggered.connect(self.export_selected)
        menu.addAction(export_action)
        
        menu.addSeparator()
        
        delete_action = QAction("🗑️ حذف", self)
        delete_action.triggered.connect(self.delete_selected)
        menu.addAction(delete_action)
        
        menu.exec(self.table.viewport().mapToGlobal(position))
    
    def show_row_actions(self, row):
        """نمایش عملیات ردیف"""
        menu = QMenu(self)
        
        view_action = QAction("👁️ مشاهده", self)
        view_action.triggered.connect(lambda: self.view_row_details(row))
        menu.addAction(view_action)
        
        edit_action = QAction("✏️ ویرایش", self)
        edit_action.triggered.connect(lambda: self.edit_row_data(row))
        menu.addAction(edit_action)
        
        menu.addSeparator()
        
        delete_action = QAction("🗑️ حذف", self)
        delete_action.triggered.connect(lambda: self.delete_row(row))
        menu.addAction(delete_action)
        
        menu.exec(self.sender().mapToGlobal(self.sender().rect().bottomLeft()))
    
    def view_details(self):
        """مشاهده جزئیات"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.view_row_details(current_row)
    
    def view_row_details(self, row):
        """مشاهده جزئیات ردیف"""
        try:
            data_id = int(self.table.item(row, 1).text())
            data = db_manager.get_sales_data_by_id(data_id)
            
            if data:
                details = f"""
📋 جزئیات داده شماره {data.id}

🔑 کلید یکتا: {data.unique_key}
📊 شیت: {data.sheet_config.name if data.sheet_config else 'نامشخص'}
📍 شماره ردیف: {data.row_number}

📦 داده‌ها:
{json.dumps(data.data, ensure_ascii=False, indent=2)}

📅 تاریخ استخراج: {data.extracted_at.strftime('%Y-%m-%d %H:%M:%S') if data.extracted_at else '-'}
📅 تاریخ بروزرسانی: {data.updated_at.strftime('%Y-%m-%d %H:%M:%S') if data.updated_at else '-'}

✅ Export شده: {'بله' if data.is_exported else 'خیر'}
{'📅 تاریخ Export: ' + data.exported_at.strftime('%Y-%m-%d %H:%M:%S') if data.exported_at else ''}

⚠️ ویرایش شده: {'بله' if data.is_updated else 'خیر'}
🔢 تعداد ویرایش: {data.update_count}

📝 یادداشت‌ها: {data.notes or 'ندارد'}
                """
                
                QMessageBox.information(self, "جزئیات داده", details)
        except Exception as e:
            app_logger.error(f"خطا در نمایش جزئیات: {str(e)}")
            QMessageBox.critical(self, "خطا", f"❌ خطا: {str(e)}")
    
    def edit_data(self):
        """ویرایش داده"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.edit_row_data(current_row)
    
    def edit_row_data(self, row):
        """ویرایش داده ردیف"""
        try:
            data_id = int(self.table.item(row, 1).text())
            
            # باز کردن Dialog ویرایش
            dialog = EditDataDialog(data_id, self)
            dialog.data_updated.connect(self.refresh_data)
            dialog.exec()
            
        except Exception as e:
            app_logger.error(f"خطا در ویرایش: {str(e)}")
            QMessageBox.critical(self, "خطا", f"❌ خطا: {str(e)}")
    
    def export_selected(self):
        """Export داده‌های انتخاب شده"""
        selected_ids = self.get_selected_ids()
        
        if not selected_ids:
            QMessageBox.warning(self, "هشدار", "لطفاً حداقل یک ردیف انتخاب کنید!")
            return
        
        try:
            # باز کردن دیالوگ Export
            dialog = AdvancedExportDialog(self)
            dialog.export_completed.connect(self.refresh_data)
            dialog.exec()
            
        except Exception as e:
            app_logger.error(f"خطا در Export: {str(e)}")
            QMessageBox.critical(self, "خطا", f"❌ خطا: {str(e)}")
    
    def delete_selected(self):
        """حذف داده‌های انتخاب شده"""
        selected_ids = self.get_selected_ids()
        
        if not selected_ids:
            QMessageBox.warning(self, "هشدار", "لطفاً حداقل یک ردیف انتخاب کنید!")
            return
        
        reply = QMessageBox.question(
            self,
            "تأیید حذف",
            f"آیا مطمئن هستید که می‌خواهید {len(selected_ids)} ردیف را حذف کنید؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                for data_id in selected_ids:
                    db_manager.delete_sales_data(data_id)
                
                QMessageBox.information(self, "موفق", f"✅ {len(selected_ids)} ردیف با موفقیت حذف شد!")
                self.load_data()
                self.data_updated.emit()
            except Exception as e:
                app_logger.error(f"خطا در حذف داده‌ها: {str(e)}")
                QMessageBox.critical(self, "خطا", f"❌ خطا در حذف:\n{str(e)}")
    
    def delete_row(self, row):
        """حذف یک ردیف"""
        try:
            data_id = int(self.table.item(row, 1).text())
            
            reply = QMessageBox.question(
                self,
                "تأیید حذف",
                "آیا مطمئن هستید که می‌خواهید این ردیف را حذف کنید؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                db_manager.delete_sales_data(data_id)
                QMessageBox.information(self, "موفق", "✅ ردیف با موفقیت حذف شد!")
                self.load_data()
                self.data_updated.emit()
        except Exception as e:
            app_logger.error(f"خطا در حذف ردیف: {str(e)}")
            QMessageBox.critical(self, "خطا", f"❌ خطا: {str(e)}")
    
    def get_selected_ids(self):
        """دریافت ID های انتخاب شده"""
        selected_ids = []
        for row in range(self.table.rowCount()):
            check_item = self.table.item(row, 0)
            if check_item and check_item.checkState() == Qt.CheckState.Checked:
                id_item = self.table.item(row, 1)
                if id_item:
                    selected_ids.append(int(id_item.text()))
        return selected_ids
    
    def get_button_style(self, color):
        """استایل دکمه"""
        return f"""
            QPushButton {{
                background: {color};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 10pt;
                font-weight: bold;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
        """
