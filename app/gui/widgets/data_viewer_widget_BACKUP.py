"""
Widget مدیریت داده‌های استخراج شده - نمای خلاصه با کارت‌ها

توسعه‌دهنده: علیرضا حامد
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QScrollArea, QFrame, QGridLayout, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from datetime import datetime

from app.core.database import db_manager
from app.core.logger import app_logger
from app.gui.dialogs.sheet_details_dialog import SheetDetailsDialog
from app.utils.ui_constants import COLORS, FONTS


class DataViewerWidget(QWidget):
    """Widget نمایش خلاصه داده‌ها با کارت‌های شیت"""
    
    data_updated = pyqtSignal()  # سیگنال بروزرسانی داده
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_sheets = []  # لیست شیت‌های انتخاب شده
        self.init_ui()
        self.load_summary()
    
    def init_ui(self):
        """راه‌اندازی رابط کاربری"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header_layout = QHBoxLayout()
        
        # عنوان
        title_label = QLabel("📊 مدیریت شیت‌ها")
        title_label.setFont(FONTS['large_bold'])
        title_label.setStyleSheet(f"color: {COLORS['primary']}; padding: 5px;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # دکمه بروزرسانی
        refresh_btn = QPushButton("🔄 بروزرسانی")
        refresh_btn.setFont(FONTS['medium'])
        refresh_btn.clicked.connect(self.load_summary)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent']};
            }}
        """)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # نوار ابزار عملیات
        toolbar_layout = QHBoxLayout()
        
        # انتخاب همه
        select_all_btn = QPushButton("☑️ انتخاب همه")
        select_all_btn.setFont(FONTS['medium'])
        select_all_btn.clicked.connect(self.select_all_sheets)
        select_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['info']};
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
                border: none;
            }}
            QPushButton:hover {{ background-color: #7B1FA2; }}
        """)
        toolbar_layout.addWidget(select_all_btn)
        
        # لغو انتخاب همه
        deselect_all_btn = QPushButton("⬜ لغو انتخاب همه")
        deselect_all_btn.setFont(FONTS['medium'])
        deselect_all_btn.clicked.connect(self.deselect_all_sheets)
        deselect_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #757575;
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
                border: none;
            }}
            QPushButton:hover {{ background-color: #616161; }}
        """)
        toolbar_layout.addWidget(deselect_all_btn)
        
        toolbar_layout.addStretch()
        
        # حذف انتخاب شده‌ها (فقط داده‌ها)
        delete_data_btn = QPushButton("🗑️ حذف داده‌های انتخاب شده")
        delete_data_btn.setFont(FONTS['medium'])
        delete_data_btn.clicked.connect(self.delete_selected_data)
        delete_data_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['warning']};
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
                border: none;
            }}
            QPushButton:hover {{ background-color: #F57C00; }}
        """)
        toolbar_layout.addWidget(delete_data_btn)
        
        # حذف کامل شیت‌های انتخاب شده
        delete_sheets_btn = QPushButton("💣 حذف کامل شیت‌های انتخاب شده")
        delete_sheets_btn.setFont(FONTS['medium'])
        delete_sheets_btn.clicked.connect(self.delete_selected_sheets)
        delete_sheets_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['danger']};
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
                border: none;
            }}
            QPushButton:hover {{ background-color: #D32F2F; }}
        """)
        toolbar_layout.addWidget(delete_sheets_btn)
        
        layout.addLayout(toolbar_layout)
        
        # راهنما
        help_label = QLabel("💡 انتخاب کنید و حذف کنید، یا روی کارت کلیک کنید برای مشاهده جزئیات.")
        help_label.setFont(FONTS['small'])
        help_label.setStyleSheet(f"color: {COLORS['secondary']}; padding: 5px; background-color: #f0f8ff; border-radius: 3px;")
        help_label.setWordWrap(True)
        layout.addWidget(help_label)
        
        # Scroll Area برای کارت‌ها
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        # Container برای کارت‌ها
        self.cards_container = QWidget()
        self.cards_layout = QGridLayout(self.cards_container)
        self.cards_layout.setSpacing(20)
        self.cards_layout.setContentsMargins(10, 10, 10, 10)
        
        scroll.setWidget(self.cards_container)
        layout.addWidget(scroll)
        
        scroll.setWidget(self.cards_container)
        layout.addWidget(scroll)
    
    def load_summary(self):
        """بارگذاری خلاصه آمار شیت‌ها"""
        try:
            # پاک کردن کارت‌های قبلی
            for i in reversed(range(self.cards_layout.count())):
                widget = self.cards_layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()
            
            # دریافت آمار همه شیت‌ها
            all_stats = db_manager.get_all_sheets_statistics()
            
            if not all_stats:
                # نمایش پیام خالی بودن
                empty_label = QLabel("📭 هنوز داده‌ای استخراج نشده است.\n\nلطفاً از بخش «استخراج داده» شیت‌ها را تنظیم و داده‌ها را استخراج کنید.")
                empty_label.setFont(FONTS['large'])
                empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                empty_label.setStyleSheet(f"color: {COLORS['secondary']}; padding: 50px;")
                self.cards_layout.addWidget(empty_label, 0, 0)
                return
            
            # ایجاد کارت برای هر شیت (4 کارت در هر ردیف)
            row = 0
            col = 0
            for stat in all_stats:
                card = self.create_sheet_card(stat)
                self.cards_layout.addWidget(card, row, col)
                
                col += 1
                if col >= 4:  # 4 کارت در هر ردیف
                    col = 0
                    row += 1
            
            # افزودن Stretch در انتها
            self.cards_layout.setRowStretch(row + 1, 1)
            
        except Exception as e:
            app_logger.error(f"خطا در بارگذاری خلاصه: {str(e)}")
            QMessageBox.critical(self, "خطا", f"خطا در بارگذاری داده‌ها:\n{str(e)}")
    
    def create_sheet_card(self, stat: dict) -> QFrame:
        """ایجاد کارت فشرده و زیبا برای یک شیت"""
        # Frame اصلی
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setFrameShadow(QFrame.Shadow.Raised)
        card.setMinimumHeight(230)  # ارتفاع ثابت برای اطمینان از نمایش همه المان‌ها
        card.setMaximumHeight(250)
        card.setMinimumWidth(300)
        
        # رنگ‌بندی بر اساس وضعیت
        if stat['not_exported'] == 0 and stat['need_reexport'] == 0:
            border_color = COLORS['success']
            bg_color = "#f1f8f4"
        elif stat['not_exported'] > 0 and stat['need_reexport'] == 0:
            border_color = COLORS['danger']
            bg_color = "#fff5f5"
        elif stat['need_reexport'] > 0:
            border_color = COLORS['warning']
            bg_color = "#fffaf0"
        else:
            border_color = COLORS['primary']
            bg_color = "#f5f9ff"
        
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-left: 5px solid {border_color};
                border-radius: 8px;
                padding: 12px;
            }}
            QFrame:hover {{
                background-color: white;
                border-left: 6px solid {border_color};
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 10, 12, 10)
        
        # عنوان شیت
        title_layout = QHBoxLayout()
        
        # Checkbox
        checkbox = QCheckBox()
        checkbox.setStyleSheet("QCheckBox { font-size: 16px; }")
        checkbox.stateChanged.connect(lambda state: self.on_sheet_selected(stat['sheet_config_id'], state))
        title_layout.addWidget(checkbox)
        
        title = QLabel(f"📊 {stat['name']}")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {border_color};")
        title_layout.addWidget(title)
        
        title_layout.addStretch()
        
        # آیکون وضعیت
        if stat['not_exported'] == 0 and stat['need_reexport'] == 0:
            status_icon = QLabel("✅")
        elif stat['not_exported'] > 0:
            status_icon = QLabel("❌")
        else:
            status_icon = QLabel("⚠️")
        status_icon.setFont(QFont("Segoe UI Emoji", 14))
        title_layout.addWidget(status_icon)
        
        layout.addLayout(title_layout)
        
        # آخرین استخراج
        if stat['last_extract']:
            last_extract_text = stat['last_extract'].strftime("%Y/%m/%d %H:%M")
        else:
            last_extract_text = "هنوز استخراج نشده"
        
        last_extract_label = QLabel(f"🕐 {last_extract_text}")
        last_extract_label.setFont(QFont("Segoe UI", 9))
        last_extract_label.setStyleSheet(f"color: {COLORS['secondary']};")
        layout.addWidget(last_extract_label)
        
        # خط جداکننده
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"background-color: {border_color}; margin: 5px 0;")
        separator.setFixedHeight(1)
        layout.addWidget(separator)
        
        # آمار - همیشه نمایش داده می‌شود
        # کل (همیشه نمایش)
        total_label = QLabel(f"📊 کل: <span style='font-size:12pt; font-weight:bold; color:{border_color}'>{stat['total']:,}</span> ردیف")
        total_label.setFont(QFont("Segoe UI", 10))
        total_label.setWordWrap(True)
        layout.addWidget(total_label)
        
        # Export شده (همیشه نمایش)
        exported_label = QLabel(f"✅ Export شده: <span style='font-size:11pt; font-weight:bold; color:{COLORS['success']}'>{stat['exported']:,}</span>")
        exported_label.setFont(QFont("Segoe UI", 10))
        layout.addWidget(exported_label)
        
        # Export نشده (همیشه نمایش)
        not_exp_label = QLabel(f"❌ Export نشده: <span style='font-size:11pt; font-weight:bold; color:{COLORS['danger']}'>{stat['not_exported']:,}</span>")
        not_exp_label.setFont(QFont("Segoe UI", 10))
        layout.addWidget(not_exp_label)
        
        # نیاز به Re-export (همیشه نمایش)
        reexp_label = QLabel(f"⚠️ نیاز به Re-export: <span style='font-size:11pt; font-weight:bold; color:{COLORS['warning']}'>{stat['need_reexport']:,}</span>")
        reexp_label.setFont(QFont("Segoe UI", 10))
        layout.addWidget(reexp_label)
        
        layout.addStretch()
        
        # دکمه مشاهده
        view_btn = QPushButton("👁 مشاهده جزئیات")
        view_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        view_btn.setFixedHeight(32)
        view_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {border_color};
                color: white;
                padding: 8px;
                border-radius: 5px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent']};
            }}
        """)
        view_btn.clicked.connect(lambda: self.open_sheet_details(stat))
        layout.addWidget(view_btn)
        
        return card
    
    def on_sheet_selected(self, sheet_config_id: int, state: int):
        """رویداد انتخاب/عدم انتخاب یک شیت"""
        if state == Qt.CheckState.Checked.value:
            if sheet_config_id not in self.selected_sheets:
                self.selected_sheets.append(sheet_config_id)
        else:
            if sheet_config_id in self.selected_sheets:
                self.selected_sheets.remove(sheet_config_id)
    
    def select_all_sheets(self):
        """انتخاب همه شیت‌ها"""
        self.selected_sheets.clear()
        for i in range(self.cards_layout.count()):
            widget = self.cards_layout.itemAt(i).widget()
            if widget and isinstance(widget, QFrame):
                checkbox = widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(True)
    
    def deselect_all_sheets(self):
        """لغو انتخاب همه شیت‌ها"""
        self.selected_sheets.clear()
        for i in range(self.cards_layout.count()):
            widget = self.cards_layout.itemAt(i).widget()
            if widget and isinstance(widget, QFrame):
                checkbox = widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(False)
    
    def delete_selected_data(self):
        """حذف فقط داده‌های شیت‌های انتخاب شده (نه خود شیت)"""
        if not self.selected_sheets:
            QMessageBox.warning(self, "هشدار", "لطفاً حداقل یک شیت انتخاب کنید!")
            return
        
        reply = QMessageBox.question(
            self,
            "تأیید حذف داده‌ها",
            f"آیا از حذف داده‌های {len(self.selected_sheets)} شیت انتخاب شده اطمینان دارید؟\n\n"
            "⚠️ توجه: فقط داده‌های استخراج شده حذف می‌شوند، خود تنظیمات شیت باقی می‌ماند.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                total_deleted = 0
                for sheet_id in self.selected_sheets:
                    # حذف همه داده‌های این شیت
                    data_list = db_manager.get_sales_data_by_sheet_config(sheet_id)
                    for data in data_list:
                        success, _ = db_manager.delete_sales_data(data.id)
                        if success:
                            total_deleted += 1
                
                QMessageBox.information(
                    self,
                    "موفق",
                    f"✅ {total_deleted:,} رکورد با موفقیت حذف شد!"
                )
                
                self.selected_sheets.clear()
                self.load_summary()
                self.data_updated.emit()
                
            except Exception as e:
                app_logger.error(f"خطا در حذف داده‌ها: {str(e)}")
                QMessageBox.critical(self, "خطا", f"خطا در حذف:\n{str(e)}")
    
    def delete_selected_sheets(self):
        """حذف کامل شیت‌های انتخاب شده (تنظیمات + داده‌ها)"""
        if not self.selected_sheets:
            QMessageBox.warning(self, "هشدار", "لطفاً حداقل یک شیت انتخاب کنید!")
            return
        
        reply = QMessageBox.critical(
            self,
            "⚠️ هشدار: حذف کامل شیت",
            f"آیا از حذف کامل {len(self.selected_sheets)} شیت انتخاب شده اطمینان دارید؟\n\n"
            "💣 این عملیات:\n"
            "   • تنظیمات شیت را حذف می‌کند\n"
            "   • تمام داده‌های استخراج شده را حذف می‌کند\n"
            "   • قابل بازگشت نیست!\n\n"
            "⚠️ برای ادامه YES را انتخاب کنید:",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                total_data = 0
                total_sheets = 0
                
                for sheet_id in self.selected_sheets:
                    # حذف داده‌ها
                    data_list = db_manager.get_sales_data_by_sheet_config(sheet_id)
                    for data in data_list:
                        success, _ = db_manager.delete_sales_data(data.id)
                        if success:
                            total_data += 1
                    
                    # حذف تنظیمات شیت
                    success, msg = db_manager.delete_sheet_config(sheet_id)
                    if success:
                        total_sheets += 1
                
                QMessageBox.information(
                    self,
                    "موفق",
                    f"✅ حذف کامل انجام شد:\n\n"
                    f"   • {total_sheets} شیت حذف شد\n"
                    f"   • {total_data:,} رکورد حذف شد"
                )
                
                self.selected_sheets.clear()
                self.load_summary()
                self.data_updated.emit()
                
            except Exception as e:
                app_logger.error(f"خطا در حذف کامل: {str(e)}")
                QMessageBox.critical(self, "خطا", f"خطا در حذف:\n{str(e)}")
    
    def open_sheet_details(self, stat: dict):
        """باز کردن دیالوگ جزئیات شیت"""
        try:
            dialog = SheetDetailsDialog(
                sheet_config_id=stat['sheet_config_id'],
                sheet_name=stat['name'],
                parent=self
            )
            
            # اتصال سیگنال برای بروزرسانی
            dialog.data_updated.connect(self.on_data_updated)
            
            # نمایش دیالوگ
            dialog.exec()
            
            # بروزرسانی خلاصه پس از بسته شدن دیالوگ
            self.load_summary()
            
        except Exception as e:
            app_logger.error(f"خطا در باز کردن جزئیات: {str(e)}")
            QMessageBox.critical(self, "خطا", f"خطا در باز کردن جزئیات:\n{str(e)}")
    
    def on_data_updated(self):
        """رویداد بروزرسانی داده"""
        self.load_summary()
        self.data_updated.emit()
    
    def refresh_data(self):
        """بروزرسانی داده‌ها (alias برای load_summary)"""
        self.load_summary()
