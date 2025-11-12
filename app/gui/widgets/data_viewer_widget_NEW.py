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
from app.core.logger import setup_logger

logger = setup_logger(__name__)


class DataViewerWidget(QWidget):
    """ویجت نمایش کارت‌های شیت‌ها"""
    
    refresh_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DatabaseManager()
        self.selected_sheets = []
        self.setup_ui()
        
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
        
        # دکمه حذف داده‌ها
        delete_data_btn = QPushButton("🗑️ حذف داده‌های انتخاب شده")
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
        
        # دکمه حذف کامل
        delete_sheets_btn = QPushButton("💣 حذف کامل شیت‌های انتخاب شده")
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
        
        # اضافه کردن کارت‌ها - 3 در هر ردیف
        row, col = 0, 0
        for stat in stats:
            card = self.create_simple_card(stat)
            self.cards_layout.addWidget(card, row, col)
            
            col += 1
            if col >= 3:
                col = 0
                row += 1
    
    def create_simple_card(self, stat):
        """ایجاد کارت ساده و خوانا"""
        
        # تعیین رنگ
        if stat['not_exported'] > 0:
            border_color = COLORS['danger']
            status = "❌ دارای Export نشده"
        elif stat['need_reexport'] > 0:
            border_color = COLORS['warning']
            status = "⚠️ نیاز به Re-export"
        else:
            border_color = COLORS['success']
            status = "✅ همه Export شده"
        
        # کارت اصلی
        card = QFrame()
        card.setMinimumSize(350, 380)
        card.setMaximumWidth(450)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 4px solid {border_color};
                border-radius: 15px;
                padding: 20px;
            }}
            QFrame:hover {{
                background-color: #f8f9fa;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(15)
        
        # ==== هدر: Checkbox + عنوان ====
        header = QHBoxLayout()
        
        checkbox = QCheckBox()
        checkbox.setFixedSize(25, 25)
        checkbox.setStyleSheet("""
            QCheckBox::indicator {
                width: 25px;
                height: 25px;
                border: 3px solid #6c757d;
                border-radius: 6px;
                background: white;
            }
            QCheckBox::indicator:checked {
                background-color: #7c3aed;
                border-color: #7c3aed;
            }
        """)
        checkbox.stateChanged.connect(lambda s: self.on_checkbox_changed(stat['sheet_config_id'], s))
        header.addWidget(checkbox)
        
        title = QLabel(stat['name'])
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {border_color};")
        title.setWordWrap(True)
        header.addWidget(title, 1)
        
        layout.addLayout(header)
        
        # ==== وضعیت ====
        status_label = QLabel(status)
        status_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        status_label.setStyleSheet(f"color: {border_color}; padding: 8px; background: {border_color}20; border-radius: 6px;")
        layout.addWidget(status_label)
        
        # ==== تاریخ ====
        if stat['last_extract']:
            date_str = stat['last_extract'].strftime("%Y/%m/%d - %H:%M")
        else:
            date_str = "استخراج نشده"
        
        date_label = QLabel(f"🕐 {date_str}")
        date_label.setFont(QFont("Segoe UI", 9))
        date_label.setStyleSheet("color: #6c757d; padding: 5px 0;")
        layout.addWidget(date_label)
        
        # ==== خط جدا کننده ====
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background: {border_color}; max-height: 3px;")
        layout.addWidget(line)
        
        # ==== آمار - به صورت جدولی ====
        stats_container = QWidget()
        stats_layout = QVBoxLayout(stats_container)
        stats_layout.setSpacing(10)
        stats_layout.setContentsMargins(10, 10, 10, 10)
        stats_container.setStyleSheet("background: #f8f9fa; border-radius: 10px; padding: 10px;")
        
        # کل
        total_row = QHBoxLayout()
        total_row.addWidget(QLabel("📊"), 0)
        total_lbl = QLabel(f"<b>کل:</b> <span style='font-size:14pt; color:{border_color};'>{stat['total']:,}</span> ردیف")
        total_lbl.setFont(QFont("Segoe UI", 11))
        total_row.addWidget(total_lbl, 1)
        stats_layout.addLayout(total_row)
        
        # Export شده
        exp_row = QHBoxLayout()
        exp_row.addWidget(QLabel("✅"), 0)
        exp_lbl = QLabel(f"<b>Export شده:</b> <span style='font-size:13pt; color:{COLORS['success']};'>{stat['exported']:,}</span>")
        exp_lbl.setFont(QFont("Segoe UI", 11))
        exp_row.addWidget(exp_lbl, 1)
        stats_layout.addLayout(exp_row)
        
        # Export نشده
        notexp_row = QHBoxLayout()
        notexp_row.addWidget(QLabel("❌"), 0)
        notexp_lbl = QLabel(f"<b>Export نشده:</b> <span style='font-size:13pt; color:{COLORS['danger']};'>{stat['not_exported']:,}</span>")
        notexp_lbl.setFont(QFont("Segoe UI", 11))
        notexp_row.addWidget(notexp_lbl, 1)
        stats_layout.addLayout(notexp_row)
        
        # Re-export
        reexp_row = QHBoxLayout()
        reexp_row.addWidget(QLabel("⚠️"), 0)
        reexp_lbl = QLabel(f"<b>نیاز به Re-export:</b> <span style='font-size:13pt; color:{COLORS['warning']};'>{stat['need_reexport']:,}</span>")
        reexp_lbl.setFont(QFont("Segoe UI", 11))
        reexp_row.addWidget(reexp_lbl, 1)
        stats_layout.addLayout(reexp_row)
        
        layout.addWidget(stats_container)
        
        # ==== فاصله ====
        layout.addStretch()
        
        # ==== دکمه جزئیات ====
        btn = QPushButton("🔍 مشاهده جزئیات کامل")
        btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        btn.setMinimumHeight(45)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {border_color};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px;
            }}
            QPushButton:hover {{
                background: {COLORS['primary']};
            }}
        """)
        btn.clicked.connect(lambda: self.show_sheet_details(stat['sheet_config_id']))
        layout.addWidget(btn)
        
        # ذخیره
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
        """حذف داده‌های انتخاب شده"""
        if not self.selected_sheets:
            QMessageBox.warning(self, "هشدار", "لطفاً حداقل یک شیت انتخاب کنید")
            return
        
        reply = QMessageBox.question(
            self, "تأیید حذف",
            f"آیا از حذف داده‌های {len(self.selected_sheets)} شیت اطمینان دارید؟\n\n"
            "⚠️ فقط داده‌های استخراج شده حذف می‌شوند، تنظیمات شیت باقی می‌ماند.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                for sheet_id in self.selected_sheets:
                    self.db_manager.delete_sheet_data(sheet_id)
                
                QMessageBox.information(self, "موفق", "داده‌ها با موفقیت حذف شدند")
                self.load_sheets()
            except Exception as e:
                QMessageBox.critical(self, "خطا", f"خطا در حذف: {str(e)}")
    
    def delete_selected_sheets(self):
        """حذف کامل شیت‌ها"""
        if not self.selected_sheets:
            QMessageBox.warning(self, "هشدار", "لطفاً حداقل یک شیت انتخاب کنید")
            return
        
        reply = QMessageBox.critical(
            self, "⚠️ تأیید حذف کامل",
            f"💣 آیا از حذف کامل {len(self.selected_sheets)} شیت اطمینان دارید؟\n\n"
            "❗ تمام داده‌ها و تنظیمات شیت برای همیشه حذف می‌شوند!\n"
            "این عملیات قابل بازگشت نیست!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                for sheet_id in self.selected_sheets:
                    self.db_manager.delete_sheet_config(sheet_id)
                
                QMessageBox.information(self, "موفق", "شیت‌ها با موفقیت حذف شدند")
                self.load_sheets()
            except Exception as e:
                QMessageBox.critical(self, "خطا", f"خطا در حذف: {str(e)}")
    
    def show_sheet_details(self, sheet_id):
        """نمایش جزئیات کامل شیت"""
        from app.gui.dialogs.sheet_details_dialog import SheetDetailsDialog
        dialog = SheetDetailsDialog(sheet_id, self)
        dialog.exec()
        self.load_sheets()  # Refresh
    
    def open_sheet_details(self, stat):
        """متد سازگار با نسخه قبلی"""
        self.show_sheet_details(stat['sheet_config_id'])
