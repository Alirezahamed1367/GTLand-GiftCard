"""
دیالوگ تعریف نقش ستون‌ها (Field Mapping)
کاربر مشخص می‌کند هر ستون چه نقشی دارد
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QMessageBox, QHeaderView,
    QGroupBox, QLineEdit, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from sqlalchemy.orm import Session
from app.models.financial import (
    SheetImport, FieldMapping, RawData,
    TargetField, DataType, SheetType
)
from typing import List, Dict
import json


class FieldMappingDialog(QDialog):
    """
    دیالوگ تعریف نقش ستون‌ها
    
    کاربر:
    1. شیت را انتخاب می‌کند
    2. نوع شیت را تعیین می‌کند (خرید/فروش/بونوس)
    3. برای فروش: پلتفرم را مشخص می‌کند
    4. برای هر ستون: نقش آن را تعیین می‌کند
    """
    
    mapping_saved = pyqtSignal(int)  # sheet_import_id
    
    def __init__(self, session: Session, sheet_import_id: int = None, parent=None):
        super().__init__(parent)
        self.session = session
        self.sheet_import_id = sheet_import_id
        self.sheet_import = None
        self.columns = []
        self.mappings = []  # List[Dict]
        
        self.setWindowTitle("🗺️ تعریف نقش ستون‌ها (Field Mapping)")
        self.setMinimumSize(900, 600)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        """ایجاد رابط کاربری"""
        layout = QVBoxLayout()
        
        # ═══ بخش اطلاعات شیت ═══
        sheet_info_group = QGroupBox("📋 اطلاعات شیت")
        sheet_info_layout = QVBoxLayout()
        
        # نام شیت
        h1 = QHBoxLayout()
        h1.addWidget(QLabel("نام شیت:"))
        self.sheet_name_label = QLabel("---")
        self.sheet_name_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        h1.addWidget(self.sheet_name_label)
        h1.addStretch()
        sheet_info_layout.addLayout(h1)
        
        # نوع شیت
        h2 = QHBoxLayout()
        h2.addWidget(QLabel("نوع شیت:"))
        self.sheet_type_combo = QComboBox()
        self.sheet_type_combo.addItems([
            "🛒 خرید (Purchase)",
            "💰 فروش (Sale)",
            "🎁 بونوس (Bonus)",
            "📦 سایر (Other)"
        ])
        self.sheet_type_combo.currentIndexChanged.connect(self.on_sheet_type_changed)
        h2.addWidget(self.sheet_type_combo)
        h2.addStretch()
        sheet_info_layout.addLayout(h2)
        
        # پلتفرم (فقط برای فروش)
        h3 = QHBoxLayout()
        h3.addWidget(QLabel("پلتفرم فروش:"))
        self.platform_input = QLineEdit()
        self.platform_input.setPlaceholderText("مثلاً: roblox, apple, nintendo, pubg")
        self.platform_input.setMaximumWidth(300)
        h3.addWidget(self.platform_input)
        h3.addStretch()
        self.platform_label = h3.itemAt(0).widget()
        sheet_info_layout.addLayout(h3)
        
        sheet_info_group.setLayout(sheet_info_layout)
        layout.addWidget(sheet_info_group)
        
        # ═══ جدول Mapping ═══
        mapping_group = QGroupBox("🗺️ تعریف نقش ستون‌ها")
        mapping_layout = QVBoxLayout()
        
        # راهنما
        help_label = QLabel(
            "⚠️ برای هر ستون، نقش آن را انتخاب کنید. "
            "ستون‌هایی که نیازی نیستید را 'نادیده' انتخاب کنید."
        )
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: #7f8c8d; padding: 5px;")
        mapping_layout.addWidget(help_label)
        
        # جدول
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "ستون در شیت",
            "نقش در سیستم",
            "نوع داده",
            "اجباری؟",
            "نمونه داده"
        ])
        
        # تنظیمات جدول
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        
        mapping_layout.addWidget(self.table)
        mapping_group.setLayout(mapping_layout)
        layout.addWidget(mapping_group)
        
        # ═══ دکمه‌ها ═══
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.auto_map_btn = QPushButton("🤖 تشخیص خودکار")
        self.auto_map_btn.clicked.connect(self.auto_detect_mappings)
        button_layout.addWidget(self.auto_map_btn)
        
        self.save_btn = QPushButton("💾 ذخیره Mapping")
        self.save_btn.clicked.connect(self.save_mappings)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 20px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        button_layout.addWidget(self.save_btn)
        
        cancel_btn = QPushButton("❌ انصراف")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_data(self):
        """بارگذاری داده‌ها"""
        if not self.sheet_import_id:
            return
        
        # بارگذاری SheetImport
        self.sheet_import = self.session.query(SheetImport).get(self.sheet_import_id)
        if not self.sheet_import:
            QMessageBox.warning(self, "خطا", "شیت یافت نشد!")
            self.reject()
            return
        
        # نمایش اطلاعات
        self.sheet_name_label.setText(self.sheet_import.sheet_name)
        
        # تنظیم نوع شیت
        type_map = {
            SheetType.PURCHASE: 0,
            SheetType.SALE: 1,
            SheetType.BONUS: 2,
            SheetType.OTHER: 3
        }
        self.sheet_type_combo.setCurrentIndex(type_map.get(self.sheet_import.sheet_type, 3))
        
        # تنظیم پلتفرم
        if self.sheet_import.platform:
            self.platform_input.setText(self.sheet_import.platform)
        
        # استخراج ستون‌ها از اولین RawData
        first_row = self.session.query(RawData).filter_by(
            sheet_import_id=self.sheet_import_id
        ).first()
        
        if not first_row:
            QMessageBox.warning(self, "خطا", "داده‌ای در این شیت یافت نشد!")
            self.reject()
            return
        
        self.columns = list(first_row.data.keys())
        
        # بارگذاری Mappings موجود
        existing_mappings = self.session.query(FieldMapping).filter_by(
            sheet_import_id=self.sheet_import_id
        ).all()
        
        existing_map = {m.source_column: m for m in existing_mappings}
        
        # پر کردن جدول
        self.table.setRowCount(len(self.columns))
        
        for i, col in enumerate(self.columns):
            # ستون 0: نام ستون
            item = QTableWidgetItem(col)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(i, 0, item)
            
            # ستون 1: نقش (ComboBox)
            target_combo = QComboBox()
            target_combo.addItems([
                "🚫 نادیده (Ignore)",
                "🏷️ Label (account_id)",
                "📧 ایمیل (email)",
                "🏪 تامین‌کننده (supplier)",
                "💰 مقدار گلد (gold_quantity)",
                "📊 نرخ خرید (purchase_rate)",
                "💵 هزینه خرید (purchase_cost)",
                "📅 تاریخ خرید (purchase_date)",
                "🎁 بونوس سیلور (silver_bonus)",
                "📦 مقدار فروش (sale_quantity)",
                "💲 نرخ فروش (sale_rate)",
                "🔤 نوع فروش (sale_type)",
                "👤 کد مشتری (customer_code)",
                "📅 تاریخ فروش (sale_date)",
                "💸 سود پرسنل (staff_profit)",
                "📝 یادداشت (notes)",
                "✅ وضعیت (status)"
            ])
            
            # اگر mapping موجود باشد
            if col in existing_map:
                mapping = existing_map[col]
                # پیدا کردن index مناسب
                for idx in range(target_combo.count()):
                    if mapping.target_field.value in target_combo.itemText(idx):
                        target_combo.setCurrentIndex(idx)
                        break
            
            self.table.setCellWidget(i, 1, target_combo)
            
            # ستون 2: نوع داده (ComboBox)
            type_combo = QComboBox()
            type_combo.addItems([
                "📝 متن (text)",
                "🔢 عدد اعشاری (decimal)",
                "🔢 عدد صحیح (integer)",
                "📅 تاریخ (date)",
                "☑️ بله/خیر (boolean)"
            ])
            
            if col in existing_map:
                mapping = existing_map[col]
                type_map = {
                    DataType.TEXT: 0,
                    DataType.DECIMAL: 1,
                    DataType.INTEGER: 2,
                    DataType.DATE: 3,
                    DataType.BOOLEAN: 4
                }
                type_combo.setCurrentIndex(type_map.get(mapping.data_type, 0))
            
            self.table.setCellWidget(i, 2, type_combo)
            
            # ستون 3: اجباری (CheckBox)
            required_check = QCheckBox()
            if col in existing_map:
                required_check.setChecked(existing_map[col].is_required)
            
            cell_widget = QWidget()
            cell_layout = QHBoxLayout(cell_widget)
            cell_layout.addWidget(required_check)
            cell_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cell_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(i, 3, cell_widget)
            
            # ستون 4: نمونه داده
            sample = str(first_row.data.get(col, ""))[:50]
            sample_item = QTableWidgetItem(sample)
            sample_item.setFlags(sample_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            sample_item.setForeground(Qt.GlobalColor.gray)
            self.table.setItem(i, 4, sample_item)
    
    def on_sheet_type_changed(self, index):
        """تغییر نوع شیت"""
        # نمایش/مخفی کردن فیلد پلتفرم
        is_sale = index == 1  # Sale
        self.platform_label.setVisible(is_sale)
        self.platform_input.setVisible(is_sale)
    
    def auto_detect_mappings(self):
        """تشخیص خودکار نقش ستون‌ها"""
        # الگوهای شناخته شده
        patterns = {
            'label': ['label', 'account', 'account_id', 'لیبل', 'اکانت'],
            'email': ['email', 'ایمیل', 'mail'],
            'supplier': ['supplier', 'تامین کننده', 'vendor'],
            'gold_quantity': ['gold', 'gold_quantity', 'طلا', 'مقدار طلا', 'گلد'],
            'purchase_rate': ['purchase_rate', 'rate', 'نرخ خرید', 'ریت'],
            'purchase_cost': ['cost', 'purchase_cost', 'price', 'هزینه', 'قیمت'],
            'silver_bonus': ['silver', 'bonus', 'سیلور', 'بونوس', 'free'],
            'sale_quantity': ['sold', 'sale_quantity', 'فروش', 'مقدار فروش'],
            'sale_rate': ['sale_rate', 'sell_rate', 'نرخ فروش'],
            'customer_code': ['customer', 'مشتری', 'buyer'],
            'staff_profit': ['profit', 'سود', 'سود پرسنل']
        }
        
        matched = 0
        
        for i in range(self.table.rowCount()):
            col_name = self.table.item(i, 0).text().lower()
            target_combo = self.table.cellWidget(i, 1)
            
            # جستجوی الگو
            for target_field, keywords in patterns.items():
                if any(keyword in col_name for keyword in keywords):
                    # پیدا کردن index در ComboBox
                    for idx in range(target_combo.count()):
                        if target_field in target_combo.itemText(idx):
                            target_combo.setCurrentIndex(idx)
                            matched += 1
                            break
                    break
        
        QMessageBox.information(
            self,
            "تشخیص خودکار",
            f"✅ {matched} ستون به صورت خودکار تشخیص داده شد.\n\n"
            "لطفاً سایر ستون‌ها را دستی بررسی کنید."
        )
    
    def save_mappings(self):
        """ذخیره Mappings"""
        try:
            # بررسی نوع شیت
            type_map = [SheetType.PURCHASE, SheetType.SALE, SheetType.BONUS, SheetType.OTHER]
            sheet_type = type_map[self.sheet_type_combo.currentIndex()]
            
            # بررسی پلتفرم (برای فروش)
            platform = None
            if sheet_type == SheetType.SALE:
                platform = self.platform_input.text().strip()
                if not platform:
                    QMessageBox.warning(self, "خطا", "لطفاً پلتفرم فروش را مشخص کنید!")
                    return
            
            # به‌روزرسانی SheetImport
            self.sheet_import.sheet_type = sheet_type
            self.sheet_import.platform = platform
            
            # حذف Mappings قدیمی
            self.session.query(FieldMapping).filter_by(
                sheet_import_id=self.sheet_import_id
            ).delete()
            
            # ایجاد Mappings جدید
            target_field_map = {
                'ignore': TargetField.IGNORE,
                'account_id': TargetField.ACCOUNT_ID,
                'email': TargetField.EMAIL,
                'supplier': TargetField.SUPPLIER,
                'gold_quantity': TargetField.GOLD_QUANTITY,
                'purchase_rate': TargetField.PURCHASE_RATE,
                'purchase_cost': TargetField.PURCHASE_COST,
                'purchase_date': TargetField.PURCHASE_DATE,
                'silver_bonus': TargetField.SILVER_BONUS,
                'sale_quantity': TargetField.SALE_QUANTITY,
                'sale_rate': TargetField.SALE_RATE,
                'sale_type': TargetField.SALE_TYPE,
                'customer_code': TargetField.CUSTOMER_CODE,
                'sale_date': TargetField.SALE_DATE,
                'staff_profit': TargetField.STAFF_PROFIT,
                'notes': TargetField.NOTES,
                'status': TargetField.STATUS
            }
            
            data_type_map = [
                DataType.TEXT,
                DataType.DECIMAL,
                DataType.INTEGER,
                DataType.DATE,
                DataType.BOOLEAN
            ]
            
            created = 0
            for i in range(self.table.rowCount()):
                source_column = self.table.item(i, 0).text()
                target_combo = self.table.cellWidget(i, 1)
                type_combo = self.table.cellWidget(i, 2)
                required_widget = self.table.cellWidget(i, 3)
                required_check = required_widget.findChild(QCheckBox)
                
                # استخراج target_field
                target_text = target_combo.currentText()
                target_key = None
                for key in target_field_map.keys():
                    if key in target_text:
                        target_key = key
                        break
                
                if not target_key:
                    continue
                
                target_field = target_field_map[target_key]
                
                # اگر ignore باشد، skip
                if target_field == TargetField.IGNORE:
                    continue
                
                # ایجاد FieldMapping
                mapping = FieldMapping(
                    sheet_import_id=self.sheet_import_id,
                    source_column=source_column,
                    target_field=target_field,
                    data_type=data_type_map[type_combo.currentIndex()],
                    is_required=required_check.isChecked()
                )
                self.session.add(mapping)
                created += 1
            
            self.session.commit()
            
            QMessageBox.information(
                self,
                "موفقیت",
                f"✅ {created} فیلد با موفقیت Map شد!\n\n"
                "اکنون می‌توانید داده‌ها را پردازش کنید."
            )
            
            self.mapping_saved.emit(self.sheet_import_id)
            self.accept()
            
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "خطا", f"❌ خطا در ذخیره:\n{str(e)}")
