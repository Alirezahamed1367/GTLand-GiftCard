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
        """انتقال داده‌ها به مرحله بعدی (Stage 2) با پردازش نقش‌ها"""
        if not self.selected_sheets:
            QMessageBox.warning(self, "هشدار", "⚠️ لطفاً حداقل یک شیت انتخاب کنید")
            return
        
        # بررسی نقش‌ها و نگاشت ستون‌های هر شیت
        try:
            from app.models.financial import get_financial_session, FieldRole
            from app.core.google_sheets import GoogleSheetExtractor
            
            db = get_financial_session()
            
            # بررسی وجود نقش‌های پایه
            roles_count = db.query(FieldRole).filter(FieldRole.is_active == True).count()
            
            if roles_count == 0:
                QMessageBox.warning(
                    self, "⚠️ نقش‌ها تعریف نشده",
                    "❌ نقش‌های پایه تعریف نشده است!\n\n"
                    "لطفاً ابتدا از منوی 'ابزارها' → 'تنظیمات مالی' → 'مدیریت نقش‌ها'\n"
                    "نقش‌های پایه را تعریف کنید."
                )
                db.close()
                return
            
            # 🔍 بررسی دقیق هر شیت انتخابی
            sheets_without_mapping = []
            sheets_missing_roles = []  # {sheet_name: [missing_roles]}
            
            extractor = GoogleSheetExtractor()
            
            for sheet_id in self.selected_sheets:
                sheet_config = self.db_manager.get_sheet_config(sheet_id)
                if not sheet_config:
                    continue
                
                # دریافت ستون‌های شیت
                try:
                    headers = extractor.get_headers(sheet_config.sheet_url, sheet_config.worksheet_name)
                except Exception as e:
                    print(f"❌ خطا در دریافت ستون‌های شیت {sheet_config.name}: {e}")
                    continue
                
                if not headers:
                    continue
                
                # بررسی نگاشت هر ستون
                mapped_columns = db.query(CustomField).filter(
                    CustomField.name.in_(headers),
                    CustomField.is_active == True
                ).all()
                
                if not mapped_columns:
                    sheets_without_mapping.append(sheet_config.name)
                    continue
                
                # بررسی نقش‌های ضروری
                mapped_roles = set()
                for field in mapped_columns:
                    if field.role_id:
                        role = db.query(FieldRole).filter(FieldRole.id == field.role_id).first()
                        if role:
                            mapped_roles.add(role.name)
                
                required_roles = {'identifier', 'value', 'rate'}
                missing = required_roles - mapped_roles
                
                if missing:
                    sheets_missing_roles.append({
                        'name': sheet_config.name,
                        'missing': list(missing)
                    })
            
            db.close()
            
            # گزارش مشکلات
            if sheets_without_mapping or sheets_missing_roles:
                error_msg = "❌ برخی شیت‌ها نگاشت ستون کامل ندارند:\n\n"
                
                if sheets_without_mapping:
                    error_msg += "🔴 شیت‌های بدون نگاشت:\n"
                    for sheet_name in sheets_without_mapping:
                        error_msg += f"  • {sheet_name}\n"
                    error_msg += "\n"
                
                if sheets_missing_roles:
                    error_msg += "🟡 شیت‌هایی که نقش‌های ضروری ندارند:\n"
                    for sheet_info in sheets_missing_roles:
                        missing_fa = []
                        for role in sheet_info['missing']:
                            if role == 'identifier':
                                missing_fa.append('کد محصول')
                            elif role == 'value':
                                missing_fa.append('مقدار')
                            elif role == 'rate':
                                missing_fa.append('نرخ')
                        error_msg += f"  • {sheet_info['name']}: {', '.join(missing_fa)}\n"
                    error_msg += "\n"
                
                error_msg += (
                    "📌 برای رفع مشکل:\n"
                    "  1️⃣ به تب 'مدیریت شیت‌ها' بروید\n"
                    "  2️⃣ شیت مشکل‌دار را ویرایش کنید\n"
                    "  3️⃣ دکمه 'تست ارتباط' را بزنید\n"
                    "  4️⃣ نقش‌های ضروری را تنظیم کنید\n"
                    "  5️⃣ ذخیره کنید\n\n"
                    "آیا می‌خواهید الان به تب 'مدیریت شیت‌ها' بروید؟"
                )
                
                reply = QMessageBox.question(
                    self, "⚠️ نقش‌های ستون‌ها ناقص",
                    error_msg,
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    main_window = self.window()
                    if hasattr(main_window, 'tabs'):
                        main_window.tabs.setCurrentIndex(0)
                
                return
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "خطا", f"❌ خطا در بررسی نقش‌ها:\n{str(e)}")
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
        """باز کردن مدیر نقش‌ها"""
        try:
            from app.gui.financial.role_manager_dialog import RoleManagerDialog
            dialog = RoleManagerDialog(self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"❌ خطا در باز کردن مدیر نقش‌ها:\n{str(e)}")

