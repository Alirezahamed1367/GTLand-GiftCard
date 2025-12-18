"""
دیالوگ نگاشت ستون‌ها به نقش‌ها - بعد از تست ارتباط موفق
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox, QMessageBox,
    QHeaderView, QCheckBox, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from app.models.financial import get_financial_session


class ColumnRoleMappingDialog(QDialog):
    """
    دیالوگ نگاشت ستون‌ها به نقش‌ها
    """
    
    def __init__(self, column_headers, sample_data, parent=None):
        super().__init__(parent)
        self.column_headers = column_headers
        self.sample_data = sample_data
        self.role_mappings = {}  # {column_name: (role_id, is_active)}
        self.financial_db = get_financial_session()
        
        self.setWindowTitle("🔗 تنظیم نقش‌های ستون‌ها")
        self.setMinimumSize(1000, 700)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        self.init_ui()
        self.load_mapping_table()
    
    def init_ui(self):
        """ایجاد رابط کاربری"""
        layout = QVBoxLayout(self)
        
        # عنوان
        title = QLabel("🔗 تنظیم نقش‌های ستون‌ها")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #2196F3; padding: 15px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # توضیحات
        desc = QLabel(
            "📌 برای هر ستون از شیت Google، یک نقش انتخاب کنید\n"
            "📌 نقش‌ها مشخص می‌کنند که هر ستون چه کاربردی دارد (کد محصول، مقدار، نرخ، مشتری، تاریخ و ...)\n"
            "📌 نقش‌های ضروری: identifier (کد محصول), value (مقدار), rate (نرخ)\n"
            "📌 می‌توانید چند ستون برای یک نقش داشته باشید"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("""
            background: #E3F2FD;
            padding: 18px;
            border-radius: 8px;
            color: #1565C0;
            border-left: 5px solid #2196F3;
            font-size: 11pt;
            line-height: 1.6;
        """)
        layout.addWidget(desc)
        
        # جدول نگاشت
        self.mapping_table = QTableWidget()
        self.mapping_table.setColumnCount(4)
        self.mapping_table.setHorizontalHeaderLabels([
            "ستون شیت",
            "نمونه داده",
            "نقش",
            "فعال"
        ])
        self.mapping_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.mapping_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.mapping_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.mapping_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        # تنظیم ارتفاع ردیف‌ها - کاهش برای تراز بهتر
        self.mapping_table.verticalHeader().setDefaultSectionSize(45)
        
        self.mapping_table.setAlternatingRowColors(True)
        self.mapping_table.setStyleSheet("""
            QTableWidget {
                background: white;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 10pt;
                font-family: 'Segoe UI';
                gridline-color: #e0e0e0;
            }
            QTableWidget::item {
                padding: 8px;
                font-size: 10pt;
                border-bottom: 1px solid #e0e0e0;
            }
            QHeaderView::section {
                background: #f5f5f5;
                padding: 12px;
                border: none;
                font-weight: bold;
                font-size: 11pt;
            }
            QTableWidget::item:selected {
                background: #E3F2FD;
                color: #000;
            }
        """)
        
        layout.addWidget(self.mapping_table)
        
        # دکمه‌ها
        buttons_layout = QHBoxLayout()
        
        # دکمه نگاشت خودکار
        auto_map_btn = QPushButton("🤖 نگاشت خودکار")
        auto_map_btn.setToolTip("تشخیص خودکار نقش‌ها بر اساس نام ستون‌ها")
        auto_map_btn.setStyleSheet("""
            QPushButton {
                background: #FF9800;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px 25px;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #F57C00;
            }
        """)
        auto_map_btn.clicked.connect(self.auto_map_fields)
        buttons_layout.addWidget(auto_map_btn)
        
        # دکمه پاک کردن همه
        clear_btn = QPushButton("🗑️ پاک کردن همه")
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #9E9E9E;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px 25px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background: #757575;
            }
        """)
        clear_btn.clicked.connect(self.clear_all_mappings)
        buttons_layout.addWidget(clear_btn)
        
        buttons_layout.addStretch()
        
        # دکمه ذخیره
        save_btn = QPushButton("💾 ذخیره و بستن")
        save_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px 40px;
                font-size: 12pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #45a049;
            }
        """)
        save_btn.clicked.connect(self.save_and_close)
        buttons_layout.addWidget(save_btn)
        
        # دکمه انصراف
        cancel_btn = QPushButton("❌ انصراف")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #f44336;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px 30px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background: #d32f2f;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_mapping_table(self):
        """بارگذاری جدول نگاشت"""
        self.mapping_table.setRowCount(len(self.column_headers))
        
        # دریافت لیست نقش‌ها
        roles = self.financial_db.query(FieldRole).filter(
            FieldRole.is_active == True
        ).order_by(FieldRole.display_order).all()
        
        for i, column_name in enumerate(self.column_headers):
            # ستون 0: نام ستون
            name_item = QTableWidgetItem(column_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            name_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.mapping_table.setItem(i, 0, name_item)
            
            # ستون 1: نمونه داده
            sample = self.sample_data[i] if i < len(self.sample_data) else ""
            sample_item = QTableWidgetItem(str(sample)[:100])
            sample_item.setFlags(sample_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            sample_item.setForeground(QColor("#555"))
            sample_item.setFont(QFont("Segoe UI", 9))
            sample_item.setToolTip(str(sample))
            self.mapping_table.setItem(i, 1, sample_item)
            
            # ستون 2: انتخاب نقش
            role_combo = QComboBox()
            role_combo.addItem("-- بدون نقش --", None)
            
            for role in roles:
                role_combo.addItem(
                    f"{role.label_fa} ({role.name})",
                    role.id
                )
            
            role_combo.setStyleSheet("""
                QComboBox {
                    padding: 6px 10px;
                    border: 2px solid #ccc;
                    border-radius: 4px;
                    font-size: 10pt;
                    font-family: 'Segoe UI';
                    background: white;
                    min-height: 28px;
                    max-height: 28px;
                }
                QComboBox:hover {
                    border: 2px solid #2196F3;
                }
                QComboBox:focus {
                    border: 2px solid #1976D2;
                    background: #E3F2FD;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 25px;
                }
                QComboBox::down-arrow {
                    width: 0;
                    height: 0;
                    border-left: 4px solid transparent;
                    border-right: 4px solid transparent;
                    border-top: 5px solid #666;
                }
                QComboBox QAbstractItemView {
                    border: 2px solid #2196F3;
                    background: white;
                    selection-background-color: #E3F2FD;
                    selection-color: #000;
                    font-size: 10pt;
                    padding: 5px;
                }
                QComboBox QAbstractItemView::item {
                    padding: 8px;
                    min-height: 30px;
                }
                QComboBox QAbstractItemView::item:hover {
                    background: #BBDEFB;
                }
            """)
            
            self.mapping_table.setCellWidget(i, 2, role_combo)
            
            # ستون 3: چک‌باکس فعال
            active_check = QCheckBox()
            active_check.setChecked(True)
            active_check.setStyleSheet("""
                QCheckBox {
                    spacing: 8px;
                }
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                    border: 2px solid #999;
                    border-radius: 3px;
                    background: white;
                }
                QCheckBox::indicator:checked {
                    background: #4CAF50;
                    border: 2px solid #4CAF50;
                }
            """)
            
            check_widget = QWidget()
            check_layout = QHBoxLayout(check_widget)
            check_layout.addWidget(active_check)
            check_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            check_layout.setContentsMargins(0, 0, 0, 0)
            
            self.mapping_table.setCellWidget(i, 3, check_widget)
    
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
            'sold date': 'date',
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
        
        for i in range(self.mapping_table.rowCount()):
            column_name = self.mapping_table.item(i, 0).text().lower().strip()
            
            # جستجو در نقشه
            role_name = None
            for key, value in common_mappings.items():
                if key in column_name or column_name in key:
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
                            
                            # رنگ‌آمیزی ردیف
                            self.mapping_table.item(i, 0).setBackground(QColor("#E8F5E9"))
                            self.mapping_table.item(i, 1).setBackground(QColor("#E8F5E9"))
                            break
        
        QMessageBox.information(
            self,
            "نگاشت خودکار",
            f"✅ {mapped_count} ستون به طور خودکار نگاشت شدند\n\n"
            f"📊 کل ستون‌ها: {self.mapping_table.rowCount()}\n"
            f"✓ نگاشت شده: {mapped_count}\n"
            f"⚠ باقی‌مانده: {self.mapping_table.rowCount() - mapped_count}\n\n"
            "لطفاً نگاشت‌ها را بررسی و در صورت نیاز اصلاح کنید."
        )
    
    def clear_all_mappings(self):
        """پاک کردن همه نگاشت‌ها"""
        reply = QMessageBox.question(
            self,
            "تأیید",
            "آیا از پاک کردن همه نگاشت‌ها اطمینان دارید؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for i in range(self.mapping_table.rowCount()):
                role_combo = self.mapping_table.cellWidget(i, 2)
                if role_combo:
                    role_combo.setCurrentIndex(0)  # بدون نقش
                
                # حذف رنگ
                self.mapping_table.item(i, 0).setBackground(QColor("white"))
                self.mapping_table.item(i, 1).setBackground(QColor("white"))
    
    def save_and_close(self):
        """ذخیره نگاشت‌ها و بستن دیالوگ"""
        # استخراج نگاشت‌ها
        self.role_mappings.clear()
        mapped_count = 0
        required_roles = {}  # {role_name: [columns]}
        
        for i in range(self.mapping_table.rowCount()):
            column_name = self.mapping_table.item(i, 0).text()
            role_combo = self.mapping_table.cellWidget(i, 2)
            active_widget = self.mapping_table.cellWidget(i, 3)
            
            if not role_combo:
                continue
            
            role_id = role_combo.currentData()
            
            # اگر نقش انتخاب شده
            if role_id is not None:
                # وضعیت فعال
                active_check = active_widget.findChild(QCheckBox)
                is_active = active_check.isChecked() if active_check else True
                
                self.role_mappings[column_name] = (role_id, is_active)
                mapped_count += 1
                
                # بررسی نقش‌های ضروری
                role_name = role_combo.currentText().split('(')[1].split(')')[0] if '(' in role_combo.currentText() else ''
                if role_name in ['identifier', 'value', 'rate'] and is_active:
                    if role_name not in required_roles:
                        required_roles[role_name] = []
                    required_roles[role_name].append(column_name)
        
        # بررسی نقش‌های ضروری
        missing_roles = []
        if 'identifier' not in required_roles:
            missing_roles.append('identifier (کد محصول)')
        if 'value' not in required_roles:
            missing_roles.append('value (مقدار)')
        if 'rate' not in required_roles:
            missing_roles.append('rate (نرخ)')
        
        if missing_roles:
            QMessageBox.critical(
                self,
                "❌ نقش‌های ضروری تنظیم نشده",
                f"⚠️ برای ذخیره شیت، باید نقش‌های زیر حتماً تنظیم شوند:\n\n"
                + "\n".join([f"  • {role}" for role in missing_roles]) +
                "\n\n📌 لطفاً برای حداقل یک ستون از هر نقش، آن نقش را انتخاب کنید."
            )
            return
        
        if mapped_count == 0:
            QMessageBox.warning(
                self,
                "هشدار",
                "⚠️ هیچ ستونی به نقش نگاشت نشده است!\n\n"
                "لطفاً حداقل نقش‌های ضروری را تنظیم کنید."
            )
            return
        else:
            # نمایش پیام موفقیت قبل از بستن
            QMessageBox.information(
                self,
                "ذخیره موفق",
                f"✅ نگاشت ستون‌ها با موفقیت انجام شد!\n\n"
                f"📊 کل ستون‌ها: {self.mapping_table.rowCount()}\n"
                f"✓ نگاشت شده: {mapped_count}\n"
                f"⚠ بدون نقش: {self.mapping_table.rowCount() - mapped_count}\n\n"
                f"✅ نقش‌های ضروری: identifier({len(required_roles.get('identifier', []))}), "
                f"value({len(required_roles.get('value', []))}), rate({len(required_roles.get('rate', []))})"
            )
        
        # بستن دیالوگ
        self.accept()
    
    def get_mappings(self):
        """دریافت نگاشت‌ها"""
        return self.role_mappings
    
    def closeEvent(self, event):
        """بستن دیتابیس"""
        if hasattr(self, 'financial_db'):
            self.financial_db.close()
        event.accept()
