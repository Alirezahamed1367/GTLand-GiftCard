"""
ویجت نمایش داده‌های استخراج شده - نسخه بازنویسی شده
نمایش کارت‌های خلاصه برای هر شیت با آمار کامل
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QScrollArea, QFrame, QCheckBox,
                             QMessageBox, QGridLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from app.utils.ui_constants import COLORS
from app.core.database import DatabaseManager
from loguru import logger


class DataViewerWidget(QWidget):
    """ویجت نمایش کارت‌های شیت‌ها"""
    
    refresh_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DatabaseManager()
        self.selected_sheets = []
        self.setup_ui()
        # بارگذاری خودکار کارت‌ها
        self.load_sheets()
        
    def setup_ui(self):
        """راه‌اندازی رابط کاربری"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Toolbar
        toolbar = self.create_toolbar()
        layout.addWidget(toolbar)
        
        # Scroll Area برای کارت‌ها
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: #f5f5f5; border: none; }")
        
        # Container for cards
        self.cards_container = QWidget()
        self.cards_layout = QGridLayout(self.cards_container)
        self.cards_layout.setSpacing(20)
        self.cards_layout.setContentsMargins(10, 10, 10, 10)
        
        scroll.setWidget(self.cards_container)
        layout.addWidget(scroll)
        
    def create_toolbar(self):
        """ایجاد نوار ابزار"""
        toolbar = QFrame()
        toolbar.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        layout = QHBoxLayout(toolbar)
        layout.setSpacing(10)
        
        # دکمه بروزرسانی
        refresh_btn = QPushButton("🔄 بروزرسانی")
        refresh_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['info']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary']};
            }}
        """)
        refresh_btn.clicked.connect(self.load_sheets)
        layout.addWidget(refresh_btn)
        
        layout.addStretch()
        
        # دکمه انتخاب همه
        select_all_btn = QPushButton("☑️ انتخاب همه")
        select_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent']};
            }}
        """)
        select_all_btn.clicked.connect(self.select_all_sheets)
        layout.addWidget(select_all_btn)
        
        # دکمه لغو انتخاب
        deselect_all_btn = QPushButton("⬜ لغو انتخاب همه")
        deselect_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        deselect_all_btn.clicked.connect(self.deselect_all_sheets)
        layout.addWidget(deselect_all_btn)
        
        # دکمه حذف داده‌ها (فقط داده‌ها - تنظیمات باقی می‌ماند)
        delete_data_btn = QPushButton("🗑️ حذف فقط داده‌ها")
        delete_data_btn.setToolTip("حذف داده‌های استخراج شده - تنظیمات شیت حفظ می‌شود")
        delete_data_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['warning']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background-color: #e68900;
            }}
        """)
        delete_data_btn.clicked.connect(self.delete_selected_data)
        layout.addWidget(delete_data_btn)
        
        # دکمه حذف کامل (داده‌ها + تنظیمات)
        delete_sheets_btn = QPushButton("💣 حذف کامل (داده + تنظیمات)")
        delete_sheets_btn.setToolTip("⚠️ حذف کامل شیت‌ها همراه با تنظیماتشان - غیرقابل بازگشت!")
        delete_sheets_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['danger']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #c82333;
            }}
        """)
        delete_sheets_btn.clicked.connect(self.delete_selected_sheets)
        layout.addWidget(delete_sheets_btn)
        
        return toolbar
        
    def load_sheets(self):
        """بارگذاری و نمایش کارت‌ها"""
        # پاک کردن کارت‌های قبلی
        for i in reversed(range(self.cards_layout.count())):
            widget = self.cards_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        self.selected_sheets.clear()
        
        # دریافت آمار
        stats = self.db_manager.get_all_sheets_statistics()
        
        if not stats:
            no_data = QLabel("هیچ شیتی استخراج نشده است")
            no_data.setFont(QFont("Segoe UI", 14))
            no_data.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_data.setStyleSheet("color: #6c757d; padding: 50px;")
            self.cards_layout.addWidget(no_data, 0, 0)
            return
        
        # اضافه کردن کارت‌ها - 4 در هر ردیف (چون کوچک‌تر شدند)
        row, col = 0, 0
        for stat in stats:
            card = self.create_simple_card(stat)
            self.cards_layout.addWidget(card, row, col)
            
            col += 1
            if col >= 4:  # 4 کارت در هر ردیف
                col = 0
                row += 1
    
    def create_simple_card(self, stat):
        """ایجاد کارت ساده بدون آمار"""
        
        # تعیین رنگ بر اساس وضعیت
        if stat['not_exported'] > 0:
            border_color = COLORS['danger']
            status_text = "نشده دارد Export"
        elif stat['need_reexport'] > 0:
            border_color = COLORS['warning']
            status_text = "نیاز به Re-export"
        else:
            border_color = COLORS['success']
            status_text = "همه Export شده"
        
        # کارت اصلی
        card = QFrame()
        card.setObjectName("SheetCard")
        card.setFixedSize(340, 200)
        card.setStyleSheet(f"""
            QFrame#SheetCard {{
                background-color: white;
                border: 3px solid {border_color};
                border-radius: 10px;
            }}
            QFrame#SheetCard:hover {{
                background-color: #f8f9fa;
            }}
        """)
        
        # Layout اصلی
        main_layout = QVBoxLayout(card)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # ========== ردیف 1: Checkbox + عنوان ==========
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        # Checkbox
        checkbox = QCheckBox()
        checkbox.setFixedSize(22, 22)
        checkbox.setStyleSheet("""
            QCheckBox::indicator {
                width: 22px;
                height: 22px;
                border: 2px solid #6c757d;
                border-radius: 4px;
                background: white;
            }
            QCheckBox::indicator:checked {
                background-color: #7c3aed;
                border-color: #7c3aed;
            }
        """)
        checkbox.stateChanged.connect(lambda s: self.on_checkbox_changed(stat['sheet_config_id'], s))
        header_layout.addWidget(checkbox)
        
        # عنوان شیت
        title = QLabel(stat['name'])
        title.setFont(QFont("Tahoma", 11, QFont.Weight.Bold))
        title.setStyleSheet(f"""
            QLabel {{
                color: {border_color};
                background: transparent;
                padding: 2px;
            }}
        """)
        title.setWordWrap(True)
        title.setMinimumHeight(25)
        header_layout.addWidget(title, 1)
        
        main_layout.addLayout(header_layout)
        
        # ========== ردیف 2: وضعیت ==========
        status = QLabel(status_text)
        status.setFont(QFont("Tahoma", 9, QFont.Weight.Bold))
        status.setStyleSheet(f"""
            QLabel {{
                color: {border_color};
                background-color: #f8f9fa;
                padding: 8px;
                border-radius: 6px;
                border: 1px solid {border_color};
            }}
        """)
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status.setMinimumHeight(30)
        main_layout.addWidget(status)
        
        # ========== ردیف 3: تاریخ ==========
        if stat['last_extract']:
            date_str = stat['last_extract'].strftime("%Y/%m/%d - %H:%M")
        else:
            date_str = "استخراج نشده"
        
        date = QLabel(f"⏰ {date_str}")
        date.setFont(QFont("Tahoma", 9))
        date.setStyleSheet("""
            QLabel {
                color: #6c757d;
                background: transparent;
                padding: 4px;
            }
        """)
        date.setMinimumHeight(20)
        main_layout.addWidget(date)
        
        # فضای خالی
        main_layout.addStretch()
        
        # ========== ردیف 4: دکمه ==========
        view_btn = QPushButton("📋 مشاهده جزئیات کامل")
        view_btn.setFont(QFont("Tahoma", 10, QFont.Weight.Bold))
        view_btn.setMinimumHeight(40)
        view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        view_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {border_color};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['accent']};
            }}
        """)
        view_btn.clicked.connect(lambda: self.show_sheet_details(stat['sheet_config_id'], stat['name']))
        main_layout.addWidget(view_btn)
        
        # ذخیره اطلاعات
        card.checkbox = checkbox
        card.sheet_id = stat['sheet_config_id']
        
        return card
    
    def on_checkbox_changed(self, sheet_id, state):
        """تغییر وضعیت checkbox"""
        if state == Qt.CheckState.Checked.value:
            if sheet_id not in self.selected_sheets:
                self.selected_sheets.append(sheet_id)
        else:
            if sheet_id in self.selected_sheets:
                self.selected_sheets.remove(sheet_id)
    
    def select_all_sheets(self):
        """انتخاب همه"""
        for i in range(self.cards_layout.count()):
            widget = self.cards_layout.itemAt(i).widget()
            if hasattr(widget, 'checkbox'):
                widget.checkbox.setChecked(True)
    
    def deselect_all_sheets(self):
        """لغو انتخاب همه"""
        for i in range(self.cards_layout.count()):
            widget = self.cards_layout.itemAt(i).widget()
            if hasattr(widget, 'checkbox'):
                widget.checkbox.setChecked(False)
        self.selected_sheets.clear()
    
    def delete_selected_data(self):
        """حذف فقط داده‌های استخراج شده (تنظیمات شیت حفظ می‌شود)"""
        if not self.selected_sheets:
            QMessageBox.warning(self, "هشدار", "لطفاً حداقل یک شیت انتخاب کنید")
            return
        
        reply = QMessageBox.question(
            self, "🗑️ تأیید حذف داده‌ها",
            f"آیا از حذف داده‌های {len(self.selected_sheets)} شیت انتخاب شده اطمینان دارید؟\n\n"
            "✅ فقط داده‌های استخراج شده حذف می‌شوند\n"
            "✅ تنظیمات شیت حفظ می‌شود\n"
            "✅ می‌توانید دوباره استخراج کنید",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                deleted_count = 0
                for sheet_id in self.selected_sheets:
                    success, msg = self.db_manager.delete_sheet_data(sheet_id)
                    if success:
                        deleted_count += 1
                
                QMessageBox.information(
                    self, "✅ موفق", 
                    f"داده‌های {deleted_count} شیت با موفقیت حذف شدند\n\n"
                    "تنظیمات شیت‌ها حفظ شده است"
                )
                self.load_sheets()
            except Exception as e:
                QMessageBox.critical(self, "خطا", f"خطا در حذف: {str(e)}")
    
    def delete_selected_sheets(self):
        """حذف کامل شیت‌ها (داده‌ها + تنظیمات)"""
        if not self.selected_sheets:
            QMessageBox.warning(self, "هشدار", "لطفاً حداقل یک شیت انتخاب کنید")
            return
        
        reply = QMessageBox.critical(
            self, "💣 ⚠️ تأیید حذف کامل",
            f"❗❗❗ آیا از حذف کامل {len(self.selected_sheets)} شیت اطمینان دارید؟ ❗❗❗\n\n"
            "⛔ تمام داده‌های استخراج شده حذف می‌شوند\n"
            "⛔ تنظیمات شیت‌ها حذف می‌شوند\n"
            "⛔ باید دوباره شیت‌ها را تعریف کنید\n"
            "⛔ این عملیات قابل بازگشت نیست!\n\n"
            "⚠️ برای حذف فقط داده‌ها از دکمه 'حذف فقط داده‌ها' استفاده کنید",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                deleted_count = 0
                for sheet_id in self.selected_sheets:
                    success, msg = self.db_manager.delete_sheet_config(sheet_id)
                    if success:
                        deleted_count += 1
                
                QMessageBox.information(
                    self, "✅ حذف شد", 
                    f"{deleted_count} شیت به طور کامل حذف شدند\n\n"
                    "برای استفاده مجدد باید شیت‌ها را دوباره تعریف کنید"
                )
                self.load_sheets()
            except Exception as e:
                QMessageBox.critical(self, "خطا", f"خطا در حذف: {str(e)}")
    
    def show_sheet_details(self, sheet_id, sheet_name):
        """نمایش جزئیات کامل شیت"""
        from app.gui.dialogs.sheet_details_dialog import SheetDetailsDialog
        dialog = SheetDetailsDialog(sheet_id, sheet_name, self)
        dialog.exec()
        self.load_sheets()  # Refresh
    
    def open_sheet_details(self, stat):
        """متد سازگار با نسخه قبلی"""
        self.show_sheet_details(stat['sheet_config_id'])
