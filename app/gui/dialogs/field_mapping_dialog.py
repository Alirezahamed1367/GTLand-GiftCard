"""
Field Mapping Dialog - نگاشت ستون‌ها به نقش‌ها
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox, QMessageBox,
    QHeaderView, QGroupBox, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from app.models.financial import get_financial_session, FieldRole, FieldMapping
from app.core.database import DatabaseManager
from app.core.google_sheets import GoogleSheetExtractor


class FieldMappingDialog(QDialog):
    """
    دیالوگ نگاشت ستون‌های شیت به نقش‌ها
    """
    
    mapping_updated = pyqtSignal()
    
    def __init__(self, sheet_config_id, parent=None):
        super().__init__(parent)
        self.sheet_config_id = sheet_config_id
        self.db_manager = DatabaseManager()
        self.financial_db = get_financial_session()
        
        # گرفتن اطلاعات شیت
        self.sheet_config = self.db_manager.get_sheet_config(sheet_config_id)
        if not self.sheet_config:
            QMessageBox.critical(self, "خطا", "شیت یافت نشد!")
            self.reject()
            return
        
        self.setWindowTitle(f"🔗 نگاشت ستون‌ها - {self.sheet_config.name}")
        self.setMinimumSize(900, 600)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        self.column_headers = []
        self.sample_data = []
        
        self.init_ui()
        self.load_sheet_columns()
        self.load_existing_mappings()
    
    def init_ui(self):
        """ایجاد رابط کاربری"""
        layout = QVBoxLayout(self)
        
        # عنوان
        title = QLabel(f"🔗 نگاشت ستون‌های شیت به نقش‌ها")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #2196F3; padding: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # توضیحات
        desc_group = QGroupBox("📌 راهنما")
        desc_layout = QVBoxLayout(desc_group)
        
        desc = QLabel(
            "• برای هر ستون از شیت، یک نقش انتخاب کنید\n"
            "• نقش‌ها مشخص می‌کنند که هر ستون چه کاربردی دارد\n"
            "• نقش‌های ضروری: identifier (کد محصول), value (مقدار), rate (نرخ)\n"
            "• می‌توانید چند ستون برای یک نقش داشته باشید"
        )
        desc.setStyleSheet("color: #555; padding: 5px;")
        desc_layout.addWidget(desc)
        
        layout.addWidget(desc_group)
        
        # جدول نگاشت
        self.mapping_table = QTableWidget()
        self.mapping_table.setColumnCount(5)
        self.mapping_table.setHorizontalHeaderLabels([
            "ستون شیت",
            "نمونه داده",
            "نقش",
            "فعال",
            "عملیات"
        ])
        self.mapping_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.mapping_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.mapping_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.mapping_table.setAlternatingRowColors(True)
        self.mapping_table.setStyleSheet("""
            QTableWidget {
                background: white;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background: #f5f5f5;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.mapping_table)
        
        # دکمه‌ها
        buttons_layout = QHBoxLayout()
        
        auto_map_btn = QPushButton("🤖 نگاشت خودکار")
        auto_map_btn.setToolTip("تشخیص خودکار نقش‌ها بر اساس نام ستون‌ها")
        auto_map_btn.setStyleSheet("""
            QPushButton {
                background: #FF9800;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background: #F57C00;
            }
        """)
        auto_map_btn.clicked.connect(self.auto_map_fields)
        buttons_layout.addWidget(auto_map_btn)
        
        buttons_layout.addStretch()
        
        save_btn = QPushButton("💾 ذخیره نگاشت")
        save_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 30px;
                font-size: 12pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #45a049;
            }
        """)
        save_btn.clicked.connect(self.save_mappings)
        buttons_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("❌ انصراف")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 30px;
                font-size: 12pt;
            }
            QPushButton:hover {
                background: #5a6268;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_sheet_columns(self):
        """بارگذاری ستون‌های شیت از Google Sheets"""
        try:
            # دریافت URL شیت
            sheet_url = self.sheet_config.sheet_url
            worksheet_name = self.sheet_config.worksheet_name or 'Sheet1'
            
            if not sheet_url:
                QMessageBox.warning(
                    self,
                    "هشدار",
                    "URL شیت تنظیم نشده است!\n"
                    "لطفاً ابتدا در بخش 'شیت‌ها' URL شیت را تنظیم کنید."
                )
                self.reject()
                return
            
            # دریافت داده از Google Sheets
            gs_extractor = GoogleSheetExtractor()
            sheet_data = gs_extractor.extract_ready_rows(
                sheet_url=sheet_url,
                worksheet_name=worksheet_name,
                ready_column=None,
                extracted_column=None,
                columns_to_extract=None,
                skip_rows=0
            )
            
            if not sheet_data or len(sheet_data) < 1:
                QMessageBox.warning(self, "هشدار", "شیت خالی است یا قابل دسترسی نیست")
                self.reject()
                return
            
            # ردیف اول = headers
            self.column_headers = sheet_data[0]
            
            # ردیف دوم = نمونه داده (اگر وجود داره)
            if len(sheet_data) > 1:
                self.sample_data = sheet_data[1]
            else:
                self.sample_data = [""] * len(self.column_headers)
            
            # ایجاد ردیف‌های جدول
            self.create_mapping_rows()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "خطا",
                f"❌ خطا در دریافت ستون‌های شیت:\n{str(e)}"
            )
            self.reject()
    
    def create_mapping_rows(self):
        """ایجاد ردیف‌های جدول نگاشت"""
        self.mapping_table.setRowCount(len(self.column_headers))
        
        # دریافت لیست نقش‌ها
        roles = self.financial_db.query(FieldRole).filter(
            FieldRole.is_active == True
        ).order_by(FieldRole.display_order).all()
        
        for i, column_name in enumerate(self.column_headers):
            # ستون 0: نام ستون
            name_item = QTableWidgetItem(column_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.mapping_table.setItem(i, 0, name_item)
            
            # ستون 1: نمونه داده
            sample = self.sample_data[i] if i < len(self.sample_data) else ""
            sample_item = QTableWidgetItem(str(sample)[:50])
            sample_item.setFlags(sample_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            sample_item.setForeground(QColor("#666"))
            self.mapping_table.setItem(i, 1, sample_item)
            
            # ستون 2: انتخاب نقش
            role_combo = QComboBox()
            role_combo.addItem("-- بدون نقش --", None)
            
            for role in roles:
                role_combo.addItem(
                    f"{role.label_fa} ({role.name})",
                    role.id
                )
            
            self.mapping_table.setCellWidget(i, 2, role_combo)
            
            # ستون 3: چک‌باکس فعال
            active_check = QCheckBox()
            active_check.setChecked(True)
            active_check.setStyleSheet("QCheckBox { margin-left: 50%; }")
            
            check_widget = QWidget()
            check_layout = QHBoxLayout(check_widget)
            check_layout.addWidget(active_check)
            check_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            check_layout.setContentsMargins(0, 0, 0, 0)
            
            self.mapping_table.setCellWidget(i, 3, check_widget)
            
            # ستون 4: دکمه پاک کردن
            clear_btn = QPushButton("🗑️")
            clear_btn.setToolTip("پاک کردن نقش")
            clear_btn.clicked.connect(lambda checked, row=i: self.clear_role(row))
            clear_btn.setStyleSheet("""
                QPushButton {
                    background: #f44336;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    background: #d32f2f;
                }
            """)
            
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.addWidget(clear_btn)
            btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            
            self.mapping_table.setCellWidget(i, 4, btn_widget)
    
    def load_existing_mappings(self):
        """بارگذاری نگاشت‌های موجود"""
        try:
            # دریافت CustomField های موجود برای این شیت
            sheet_name = self.sheet_config.name
            
            # در واقع باید از جدول field_mappings بخونیم
            # ولی اول باید ببینیم آیا custom_field هایی با نام ستون‌ها وجود داره
            
            for i, column_name in enumerate(self.column_headers):
                # پیدا کردن custom_field با این نام
                custom_field = self.financial_db.query(CustomField).filter(
                    CustomField.name == column_name,
                    CustomField.is_active == True
                ).first()
                
                if custom_field and custom_field.role_id:
                    # انتخاب نقش مربوطه
                    role_combo = self.mapping_table.cellWidget(i, 2)
                    if role_combo:
                        for j in range(role_combo.count()):
                            if role_combo.itemData(j) == custom_field.role_id:
                                role_combo.setCurrentIndex(j)
                                break
        
        except Exception as e:
            print(f"خطا در بارگذاری نگاشت‌های موجود: {e}")
    
    def auto_map_fields(self):
        """نگاشت خودکار بر اساس نام ستون‌ها"""
        # نقشه نام‌های متداول
        common_mappings = {
            'code': 'identifier',
            'cod': 'identifier',
            'کد': 'identifier',
            'شناسه': 'identifier',
            'id': 'identifier',
            
            'full data': 'value',
            'value': 'value',
            'مقدار': 'value',
            'تعداد': 'value',
            'amount': 'value',
            
            'rate': 'rate',
            'نرخ': 'rate',
            'price': 'rate',
            'قیمت': 'rate',
            
            'customer': 'customer',
            'مشتری': 'customer',
            'buyer': 'customer',
            'خریدار': 'customer',
            
            'date': 'date',
            'تاریخ': 'date',
            'sold_date': 'date',
            'purchase_date': 'date',
            
            'tr_id': 'transaction_id',
            'transaction_id': 'transaction_id',
            'تراکنش': 'transaction_id',
            'شماره': 'transaction_id',
        }
        
        # دریافت نقش‌ها
        roles = self.financial_db.query(FieldRole).filter(
            FieldRole.is_active == True
        ).all()
        
        role_map = {role.name: role.id for role in roles}
        
        # اعمال نگاشت خودکار
        mapped_count = 0
        
        for i, column_name in enumerate(self.column_headers):
            column_lower = column_name.lower().strip()
            
            # جستجو در نقشه
            role_name = None
            for key, value in common_mappings.items():
                if key in column_lower or column_lower in key:
                    role_name = value
                    break
            
            if role_name and role_name in role_map:
                role_id = role_map[role_name]
                
                # انتخاب در combo
                role_combo = self.mapping_table.cellWidget(i, 2)
                if role_combo:
                    for j in range(role_combo.count()):
                        if role_combo.itemData(j) == role_id:
                            role_combo.setCurrentIndex(j)
                            mapped_count += 1
                            break
        
        QMessageBox.information(
            self,
            "نگاشت خودکار",
            f"✅ {mapped_count} ستون به طور خودکار نگاشت شدند\n\n"
            "لطفاً نگاشت‌ها را بررسی و در صورت نیاز اصلاح کنید."
        )
    
    def clear_role(self, row):
        """پاک کردن نقش یک ردیف"""
        role_combo = self.mapping_table.cellWidget(row, 2)
        if role_combo:
            role_combo.setCurrentIndex(0)  # بدون نقش
    
    def save_mappings(self):
        """ذخیره نگاشت‌ها"""
        try:
            # حذف CustomField های قبلی این شیت
            # (در واقع باید update کنیم نه حذف، ولی برای سادگی حذف می‌کنیم)
            
            saved_count = 0
            errors = []
            
            for i in range(self.mapping_table.rowCount()):
                column_name = self.mapping_table.item(i, 0).text()
                role_combo = self.mapping_table.cellWidget(i, 2)
                active_widget = self.mapping_table.cellWidget(i, 3)
                
                if not role_combo:
                    continue
                
                role_id = role_combo.currentData()
                
                # اگر نقش انتخاب نشده، رد کن
                if role_id is None:
                    continue
                
                # وضعیت فعال/غیرفعال
                active_check = active_widget.findChild(QCheckBox)
                is_active = active_check.isChecked() if active_check else True
                
                try:
                    # پیدا یا ایجاد CustomField
                    custom_field = self.financial_db.query(CustomField).filter(
                        CustomField.name == column_name
                    ).first()
                    
                    if custom_field:
                        # بروزرسانی
                        custom_field.role_id = role_id
                        custom_field.is_active = is_active
                    else:
                        # ایجاد جدید
                        custom_field = CustomField(
                            name=column_name,
                            label_fa=column_name,
                            role_id=role_id,
                            data_type='text',
                            is_active=is_active
                        )
                        self.financial_db.add(custom_field)
                    
                    saved_count += 1
                    
                except Exception as e:
                    errors.append(f"{column_name}: {str(e)}")
            
            # Commit
            self.financial_db.commit()
            
            if errors:
                QMessageBox.warning(
                    self,
                    "ذخیره با خطا",
                    f"✅ {saved_count} نگاشت ذخیره شد\n\n"
                    f"❌ خطاها:\n" + "\n".join(errors[:5])
                )
            else:
                QMessageBox.information(
                    self,
                    "موفق",
                    f"✅ {saved_count} نگاشت با موفقیت ذخیره شد!\n\n"
                    "حالا می‌توانید داده‌ها را به مرحله بعد منتقل کنید."
                )
                
                self.mapping_updated.emit()
                self.accept()
        
        except Exception as e:
            self.financial_db.rollback()
            QMessageBox.critical(
                self,
                "خطا",
                f"❌ خطا در ذخیره نگاشت‌ها:\n{str(e)}"
            )
    
    def closeEvent(self, event):
        """بستن پنجره"""
        self.financial_db.close()
        event.accept()
