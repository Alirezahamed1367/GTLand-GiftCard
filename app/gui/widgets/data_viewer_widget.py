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
from app.core.google_sheets import GoogleSheetExtractor
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
        
        # 🆕 کارت‌های آماری
        self.stats_container = QFrame()
        self.stats_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        stats_layout = QHBoxLayout(self.stats_container)
        stats_layout.setSpacing(15)
        
        # کارت کل داده‌ها
        self.total_card = self.create_stat_card("📊 کل داده‌ها", "0", "#3b82f6")
        stats_layout.addWidget(self.total_card)
        
        # کارت منتقل شده
        self.transferred_card = self.create_stat_card("✅ منتقل شده", "0", "#10b981")
        stats_layout.addWidget(self.transferred_card)
        
        # کارت در انتظار
        self.pending_card = self.create_stat_card("⏳ در انتظار", "0", "#f59e0b")
        stats_layout.addWidget(self.pending_card)
        
        # کارت خطا
        self.failed_card = self.create_stat_card("❌ خطا", "0", "#ef4444")
        stats_layout.addWidget(self.failed_card)
        
        layout.addWidget(self.stats_container)
        
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
    
    def create_stat_card(self, title: str, value: str, color: str):
        """ایجاد کارت آماری کوچک"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        card.setFixedHeight(70)  # کوچک‌تر
        
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(4)
        card_layout.setContentsMargins(8, 8, 8, 8)
        
        # عنوان
        title_label = QLabel(title)
        title_label.setFont(QFont("Tahoma", 8, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white; background: transparent;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title_label)
        
        # مقدار
        value_label = QLabel(value)
        value_label.setFont(QFont("Tahoma", 18, QFont.Weight.Bold))
        value_label.setStyleSheet("color: white; background: transparent;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(value_label)
        
        # ذخیره reference برای بروزرسانی
        card.value_label = value_label
        
        return card
        
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
        
        # 🆕 دکمه انتقال دسته‌جمعی
        bulk_transfer_btn = QPushButton("⚡ انتقال دسته‌جمعی")
        bulk_transfer_btn.setToolTip("انتقال تمام داده‌های منتقل نشده یکجا")
        bulk_transfer_btn.setFont(QFont("Tahoma", 10, QFont.Weight.Bold))
        bulk_transfer_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #10b981;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background-color: #059669;
            }}
        """)
        bulk_transfer_btn.clicked.connect(self.bulk_transfer_all_pending)
        layout.addWidget(bulk_transfer_btn)
        
        # دکمه انتقال به مرحله بعد (Stage 2)
        transfer_btn = QPushButton("🚀 انتقال به مرحله بعدی")
        transfer_btn.setToolTip("انتقال داده‌های انتخاب شده به سیستم مالی (Stage 2) با پردازش نقش‌ها")
        transfer_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #7c3aed;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #6d28d9;
            }}
        """)
        transfer_btn.clicked.connect(self.transfer_to_stage2)
        layout.addWidget(transfer_btn)
        
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
        
        # 🆕 محاسبه و نمایش آمار کلی
        self.update_overall_stats()
        
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
    
    def update_overall_stats(self):
        """بروزرسانی کارت‌های آماری کلی"""
        try:
            from app.models.financial import get_financial_session, RawData, TransferStatus
            
            session = get_financial_session()
            
            # کل داده‌ها
            total = session.query(RawData).count()
            
            # منتقل شده
            transferred = session.query(RawData).filter_by(transferred=True).count()
            
            # در انتظار
            pending = session.query(RawData).filter(
                (RawData.transfer_status == TransferStatus.PENDING) | (RawData.transfer_status == None)
            ).count()
            
            # خطا
            failed = session.query(RawData).filter_by(
                transfer_status=TransferStatus.FAILED
            ).count()
            
            # بروزرسانی کارت‌ها
            self.total_card.value_label.setText(str(total))
            self.transferred_card.value_label.setText(str(transferred))
            self.pending_card.value_label.setText(str(pending))
            self.failed_card.value_label.setText(str(failed))
            
            session.close()
            
        except Exception as e:
            logger.error(f"خطا در بروزرسانی آمار: {e}")
    
    def create_simple_card(self, stat):
        """ایجاد کارت ساده بدون آمار"""
        
        # تعیین رنگ بر اساس وضعیت
        # بررسی وضعیت transferred
        all_data_count = stat.get('total', 0)
        transferred_count = stat.get('transferred_count', 0)
        
        if transferred_count >= all_data_count and all_data_count > 0:
            # همه منتقل شده
            border_color = "#10b981"  # سبز
            status_text = "✅ همه منتقل شده"
        elif transferred_count > 0:
            # بعضی منتقل شده
            border_color = "#f59e0b"  # نارنجی
            status_text = f"⚠️ {all_data_count - transferred_count} منتقل نشده"
        elif stat['not_exported'] > 0:
            border_color = COLORS['danger']
            status_text = "❌ Export نشده دارد"
        elif stat['need_reexport'] > 0:
            border_color = COLORS['warning']
            status_text = "⚠️ نیاز به Re-export"
        else:
            border_color = COLORS['success']
            status_text = "✅ Export شده"
        
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
        
        # 🆕 ========== آمار انتقال برای این شیت ==========
        try:
            from app.models.financial import get_financial_session, SheetImport, RawData
            session = get_financial_session()
            
            # پیدا کردن SheetImport با نام این شیت
            sheet_import = session.query(SheetImport).filter_by(sheet_name=stat['name']).first()
            
            if sheet_import:
                total_rows = session.query(RawData).filter_by(sheet_import_id=sheet_import.id).count()
                transferred_rows = session.query(RawData).filter_by(sheet_import_id=sheet_import.id, transferred=True).count()
                pending_rows = total_rows - transferred_rows
                
                stats_text = f"📊 کل: {total_rows} | ✅ منتقل: {transferred_rows} | ⏳ باقی: {pending_rows}"
            else:
                stats_text = "📊 آماری موجود نیست"
            
            session.close()
        except:
            stats_text = "📊 آماری موجود نیست"
        
        stats_label = QLabel(stats_text)
        stats_label.setFont(QFont("Tahoma", 8, QFont.Weight.Bold))
        stats_label.setStyleSheet("""
            QLabel {
                color: #495057;
                background-color: #e9ecef;
                padding: 6px;
                border-radius: 4px;
            }
        """)
        stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(stats_label)
        
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
    
    def transfer_to_stage2(self):
        """
        انتقال داده‌ها به سیستم مالی جدید (Label-Based System)
        
        این متد داده‌های استخراج شده را به سیستم مالی منتقل می‌کند:
        1. بررسی وجود Import های قبلی
        2. باز کردن Smart Import Wizard
        """
        if not self.selected_sheets:
            QMessageBox.warning(self, "هشدار", "⚠️ لطفاً حداقل یک شیت انتخاب کنید")
            return
        
        # نمایش پیام راهنما
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("🔄 انتقال به سیستم مالی")
        msg.setText(
            "📊 انتقال داده‌ها به سیستم مالی جدید\n\n"
            "سیستم جدید Label-Based دارای ویژگی‌های زیر است:\n"
            "✅ Field Mapping پویا\n"
            "✅ محاسبه خودکار سود\n"
            "✅ مدیریت موجودی\n"
            "✅ گزارشات پیشرفته\n\n"
            "برای Import داده‌ها:\n"
            "1️⃣ به تب '🔄 مدیریت BI' بروید\n"
            "2️⃣ روی دکمه '🚀 Smart Import Wizard' کلیک کنید\n"
            "3️⃣ شیت مورد نظر را انتخاب کنید\n"
            "4️⃣ Field Mapping را انجام دهید\n"
            "5️⃣ Process را اجرا کنید\n\n"
            "آیا می‌خواهید به تب مدیریت BI بروید?"
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.Yes)
        
        result = msg.exec()
        
        if result == QMessageBox.StandardButton.Yes:
            # پیدا کردن MainWindow و تغییر تب به BI Management
            main_window = self.window()
            if hasattr(main_window, 'tabs'):
                # پیدا کردن index تب BI Management
                for i in range(main_window.tabs.count()):
                    tab_text = main_window.tabs.tabText(i)
                    if 'مدیریت BI' in tab_text or 'BI' in tab_text:
                        main_window.tabs.setCurrentIndex(i)
                        QMessageBox.information(
                            self,
                            "✅ تب تغییر کرد",
                            "حالا می‌توانید از دکمه '🚀 Smart Import Wizard' استفاده کنید."
                        )
                        return
                
                # اگر تب پیدا نشد
                QMessageBox.warning(
                    self,
                    "⚠️ تب یافت نشد",
                    "تب مدیریت BI یافت نشد.\n\n"
                    "لطفاً برنامه را مجدداً اجرا کنید یا از منوی ابزارها → Smart Import Wizard استفاده کنید."
                )
                return
        
        # نمایش دیالوگ تأیید و انتخاب گزینه‌ها
        from app.gui.dialogs.transfer_dialog import TransferToStage2Dialog
        
        dialog = TransferToStage2Dialog(self.selected_sheets, self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            # بعد از موفقیت، بروزرسانی
            self.load_sheets()
            QMessageBox.information(
                self, "✅ موفقیت",
                f"داده‌های {len(self.selected_sheets)} شیت با موفقیت به مرحله بعد منتقل شدند!\n\n"
                "💡 حالا می‌توانید در تب 'گزارش‌ساز هوشمند' گزارش‌های خود را ایجاد کنید."
            )
    
    def open_role_manager(self):
        """باز کردن مدیر نقش‌ها - هدایت به سیستم جدید"""
        try:
            from app.gui.financial.per_sheet_mapping_dialog import PerSheetFieldMappingDialog
            dialog = PerSheetFieldMappingDialog(self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"❌ خطا در باز کردن مدیر نقش‌ها:\n{str(e)}")
    
    def bulk_transfer_all_pending(self):
        """انتقال دسته‌جمعی تمام داده‌های منتقل نشده"""
        try:
            from app.models.financial import get_financial_session, SheetImport, RawData, TransferStatus
            from app.core.financial import DynamicDataProcessor
            
            session = get_financial_session()
            
            # پیدا کردن شیت‌هایی که داده منتقل نشده دارند
            sheets_with_pending = session.query(SheetImport).join(RawData).filter(
                RawData.transferred == False
            ).distinct().all()
            
            if not sheets_with_pending:
                QMessageBox.information(
                    self, "✅ تمام",
                    "تمام داده‌ها قبلاً منتقل شده‌اند!"
                )
                session.close()
                return
            
            # نمایش تأیید
            reply = QMessageBox.question(
                self,
                "⚡ انتقال دسته‌جمعی",
                f"🔄 {len(sheets_with_pending)} شیت با داده منتقل نشده پیدا شد.\n\n"
                f"آیا می‌خواهید همه را به سیستم نهایی منتقل کنید؟\n\n"
                f"⚠️ این فرآیند ممکن است چند دقیقه طول بکشد.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                session.close()
                return
            
            # پردازش هر شیت
            processor = DynamicDataProcessor(session)
            total_processed = 0
            total_errors = 0
            
            for sheet in sheets_with_pending:
                try:
                    logger.info(f"پردازش شیت: {sheet.sheet_name}")
                    stats = processor.process_sheet(sheet.id)
                    total_processed += stats['processed']
                    total_errors += stats['errors']
                except Exception as e:
                    logger.error(f"خطا در پردازش {sheet.sheet_name}: {e}")
                    total_errors += 1
            
            session.close()
            
            # بروزرسانی UI
            self.load_sheets()
            
            # نمایش نتیجه
            QMessageBox.information(
                self,
                "✅ انتقال دسته‌جمعی تکمیل شد",
                f"📊 آمار:\n\n"
                f"✅ پردازش شده: {total_processed}\n"
                f"❌ خطا: {total_errors}\n\n"
                f"💡 برای مشاهده جزئیات به گزارش‌ساز بروید."
            )
            
        except Exception as e:
            logger.error(f"خطا در انتقال دسته‌جمعی: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(
                self, "خطا",
                f"❌ خطا در انتقال دسته‌جمعی:\n{str(e)}"
            )


