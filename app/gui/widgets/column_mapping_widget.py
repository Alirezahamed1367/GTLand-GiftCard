"""
ویجت پیشرفته Mapping ستون‌ها با قابلیت Drag & Drop
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QListWidget, QListWidgetItem,
    QComboBox, QLineEdit, QTextEdit, QSplitter,
    QGroupBox, QScrollArea, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal, QMimeData
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QDrag, QCursor
import json


class DraggableColumnItem(QListWidgetItem):
    """آیتم قابل کشیدن برای ستون‌ها"""
    
    def __init__(self, column_name, column_type="text", source_sheet=None):
        super().__init__(f"📊 {column_name}")
        self.column_name = column_name
        self.column_type = column_type
        self.source_sheet = source_sheet
        self.setFlags(self.flags() | Qt.ItemFlag.ItemIsDragEnabled)
        
        # رنگ‌بندی بر اساس نوع
        if column_type == "number":
            self.setForeground(QColor("#2196F3"))  # آبی
        elif column_type == "date":
            self.setForeground(QColor("#4CAF50"))  # سبز
        elif column_type == "text":
            self.setForeground(QColor("#FF9800"))  # نارنجی


class DroppableColumnList(QListWidget):
    """لیست قابل Drop برای ستون‌های Excel"""
    
    columnMapped = pyqtSignal(str, str, object)  # excel_col, source_col, source_sheet (can be int or str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.DragDropMode.DropOnly)
        self.mappings = {}  # {excel_col: {source_col, source_sheet, formula}}
        
        # استایل
        self.setStyleSheet("""
            QListWidget {
                background-color: #f5f5f5;
                border: 2px dashed #2196F3;
                border-radius: 8px;
                padding: 10px;
                font-size: 12pt;
            }
            QListWidget::item {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                margin: 4px;
            }
            QListWidget::item:selected {
                background-color: #E3F2FD;
                border: 2px solid #2196F3;
            }
        """)
    
    def dragEnterEvent(self, event):
        """هنگام ورود Drag"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dragMoveEvent(self, event):
        """هنگام حرکت Drag"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        """هنگام Drop کردن"""
        try:
            if not event.mimeData().hasText():
                return
            
            # دریافت اطلاعات ستون مبدا
            data = json.loads(event.mimeData().text())
            source_col = data.get('column_name')
            source_sheet = data.get('source_sheet')
            
            if not source_col or not source_sheet:
                return
            
            # پیدا کردن آیتم Excel که روی آن Drop شده
            # استفاده از pos() به جای position().toPoint() برای سازگاری
            try:
                pos = event.position().toPoint()
            except:
                pos = event.pos()
            
            item = self.itemAt(pos)
            if item:
                excel_col = item.data(Qt.ItemDataRole.UserRole)
                
                # ذخیره mapping
                self.mappings[excel_col] = {
                    'source_column': source_col,
                    'source_sheet': source_sheet,
                    'formula': None
                }
                
                # به‌روزرسانی نمایش
                item.setText(f"✅ {excel_col} ← {source_col}")
                item.setForeground(QColor("#4CAF50"))
                
                # ارسال سیگنال
                self.columnMapped.emit(excel_col, source_col, source_sheet)
                
                event.acceptProposedAction()
        
        except Exception as e:
            print(f"Error in dropEvent: {e}")
            import traceback
            traceback.print_exc()


class SourceColumnsList(QListWidget):
    """لیست ستون‌های مبدا (Google Sheets)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setDragDropMode(QListWidget.DragDropMode.DragOnly)
        
        # استایل
        self.setStyleSheet("""
            QListWidget {
                background-color: #E8F5E9;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                padding: 10px;
                font-size: 12pt;
            }
            QListWidget::item {
                background-color: white;
                border: 1px solid #4CAF50;
                border-radius: 4px;
                padding: 8px;
                margin: 4px;
            }
            QListWidget::item:hover {
                background-color: #C8E6C9;
            }
        """)
    
    def startDrag(self, supportedActions):
        """شروع Drag"""
        try:
            item = self.currentItem()
            if not item:
                return
            
            drag = QDrag(self)
            mime_data = QMimeData()
            
            # دریافت نام ستون و sheet
            column_name = item.data(Qt.ItemDataRole.UserRole)
            current_sheet = self.property('current_sheet')
            
            if not column_name or not current_sheet:
                print(f"Warning: Missing data - column: {column_name}, sheet: {current_sheet}")
                return
            
            # ارسال اطلاعات به صورت JSON
            data = {
                'column_name': column_name,
                'source_sheet': current_sheet
            }
            mime_data.setText(json.dumps(data))
            drag.setMimeData(mime_data)
            
            # شروع Drag
            drag.exec(Qt.DropAction.CopyAction)
        
        except Exception as e:
            print(f"Error in startDrag: {e}")
            import traceback
            traceback.print_exc()


class ColumnMappingWidget(QWidget):
    """
    ویجت اصلی Mapping ستون‌ها
    
    قابلیت‌ها:
    - انتخاب Google Sheet مبدا
    - Drag & Drop ستون‌ها
    - Formula Builder برای تبدیل داده‌ها
    - پیش‌نمایش mapping
    """
    
    def __init__(self, parent=None, excel_columns=None, available_sheets=None):
        super().__init__(parent)
        self.excel_columns = excel_columns or []  # ['A', 'B', 'C', ...]
        self.available_sheets = available_sheets or {}  # {sheet_id: {name, columns}}
        self.mappings = {}
        
        self.init_ui()
    
    def init_ui(self):
        """راه‌اندازی رابط کاربری"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        
        # بررسی داده‌های ورودی
        if not self.excel_columns:
            error_label = QLabel("⚠️ خطا: هیچ ستون Excel ای یافت نشد")
            error_label.setStyleSheet("color: red; font-size: 14pt; padding: 20px;")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            main_layout.addWidget(error_label)
            return
        
        if not self.available_sheets:
            error_label = QLabel("⚠️ خطا: هیچ Google Sheet ای یافت نشد")
            error_label.setStyleSheet("color: red; font-size: 14pt; padding: 20px;")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            main_layout.addWidget(error_label)
            return
        
        # عنوان
        title_label = QLabel("🔗 Mapping ستون‌های Google Sheet به Excel")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #1976D2; padding: 10px;")
        main_layout.addWidget(title_label)
        
        # توضیحات
        help_label = QLabel("💡 ستون‌های Google Sheet را بکشید و روی ستون‌های Excel رها کنید")
        help_label.setStyleSheet("color: #666; padding: 5px; background: #FFF9C4; border-radius: 5px;")
        help_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(help_label)
        
        # انتخاب Google Sheet
        sheet_group = QGroupBox("📄 انتخاب Google Sheet مبدا")
        sheet_layout = QHBoxLayout(sheet_group)
        
        self.sheet_combo = QComboBox()
        self.sheet_combo.setMinimumHeight(40)
        self.sheet_combo.setStyleSheet("""
            QComboBox {
                font-size: 12pt;
                padding: 8px;
                border: 2px solid #4CAF50;
                border-radius: 5px;
            }
        """)
        for sheet_id, sheet_info in self.available_sheets.items():
            self.sheet_combo.addItem(f"📊 {sheet_info['name']}", sheet_id)
        self.sheet_combo.currentIndexChanged.connect(self.on_sheet_changed)
        sheet_layout.addWidget(self.sheet_combo)
        
        main_layout.addWidget(sheet_group)
        
        # Splitter برای تقسیم صفحه
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # سمت راست: ستون‌های Google Sheet (مبدا)
        source_group = self.create_source_panel()
        splitter.addWidget(source_group)
        
        # سمت چپ: ستون‌های Excel (مقصد)
        target_group = self.create_target_panel()
        splitter.addWidget(target_group)
        
        splitter.setSizes([400, 400])
        main_layout.addWidget(splitter, 1)
        
        # دکمه‌های عملیات
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        # دکمه پاک کردن همه
        clear_btn = QPushButton("🗑️ پاک کردن همه Mapping ها")
        clear_btn.setMinimumHeight(45)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-size: 12pt;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        clear_btn.clicked.connect(self.clear_all_mappings)
        buttons_layout.addWidget(clear_btn)
        
        # دکمه پیش‌نمایش
        preview_btn = QPushButton("👁️ پیش‌نمایش Mapping")
        preview_btn.setMinimumHeight(45)
        preview_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 12pt;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        preview_btn.clicked.connect(self.show_preview)
        buttons_layout.addWidget(preview_btn)
        
        main_layout.addLayout(buttons_layout)
        
        # بارگذاری اولیه
        if self.sheet_combo.count() > 0:
            self.on_sheet_changed(0)
    
    def create_source_panel(self):
        """پنل ستون‌های Google Sheet"""
        group = QGroupBox("📊 ستون‌های Google Sheet (بکشید)")
        layout = QVBoxLayout(group)
        
        # لیست ستون‌های مبدا
        self.source_list = SourceColumnsList()
        layout.addWidget(self.source_list)
        
        # اطلاعات
        info_label = QLabel("💡 ستون‌ها را بگیرید و بکشید")
        info_label.setStyleSheet("color: #666; font-size: 10pt; padding: 5px;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)
        
        return group
    
    def create_target_panel(self):
        """پنل ستون‌های Excel"""
        group = QGroupBox("📄 ستون‌های فایل Excel (رها کنید)")
        layout = QVBoxLayout(group)
        
        # لیست ستون‌های مقصد
        self.target_list = DroppableColumnList()
        self.target_list.columnMapped.connect(self.on_column_mapped)
        
        # افزودن ستون‌های Excel
        for col in self.excel_columns:
            item = QListWidgetItem(f"⬜ {col}")
            item.setData(Qt.ItemDataRole.UserRole, col)
            self.target_list.addItem(item)
        
        layout.addWidget(self.target_list)
        
        # دکمه افزودن Formula
        formula_btn = QPushButton("⚡ افزودن Formula به ستون انتخابی")
        formula_btn.setMinimumHeight(40)
        formula_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-size: 11pt;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        formula_btn.clicked.connect(self.add_formula_to_selected)
        layout.addWidget(formula_btn)
        
        return group
    
    def on_sheet_changed(self, index):
        """تغییر Google Sheet انتخابی"""
        sheet_id = self.sheet_combo.currentData()
        if not sheet_id or sheet_id not in self.available_sheets:
            return
        
        sheet_info = self.available_sheets[sheet_id]
        columns = sheet_info.get('columns', [])
        
        # پاک کردن لیست قبلی
        self.source_list.clear()
        
        # افزودن ستون‌های جدید
        self.source_list.setProperty('current_sheet', sheet_id)
        for col_name in columns:
            item = QListWidgetItem()
            item.setText(f"📊 {col_name}")
            item.setData(Qt.ItemDataRole.UserRole, col_name)
            self.source_list.addItem(item)
    
    def on_column_mapped(self, excel_col, source_col, source_sheet):
        """هنگام Mapping یک ستون"""
        self.mappings[excel_col] = {
            'source_column': source_col,
            'source_sheet': source_sheet,
            'formula': None
        }
        
        # به‌روزرسانی mapping در target_list
        self.target_list.mappings = self.mappings
    
    def add_formula_to_selected(self):
        """افزودن Formula به ستون انتخابی"""
        current_item = self.target_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "هشدار", "لطفاً یک ستون Excel انتخاب کنید")
            return
        
        excel_col = current_item.data(Qt.ItemDataRole.UserRole)
        if excel_col not in self.mappings:
            QMessageBox.warning(self, "هشدار", "ابتدا یک ستون Google Sheet را به این ستون Map کنید")
            return
        
        # نمایش دیالوگ Formula Builder
        from app.gui.dialogs.formula_builder_dialog import FormulaBuilderDialog
        dialog = FormulaBuilderDialog(
            self,
            current_mapping=self.mappings[excel_col]
        )
        
        if dialog.exec():
            formula = dialog.get_formula()
            self.mappings[excel_col]['formula'] = formula
            
            # به‌روزرسانی نمایش
            source_col = self.mappings[excel_col]['source_column']
            current_item.setText(f"⚡ {excel_col} ← {source_col} [+Formula]")
            current_item.setForeground(QColor("#FF9800"))
    
    def clear_all_mappings(self):
        """پاک کردن همه Mapping ها"""
        reply = QMessageBox.question(
            self,
            "تأیید",
            "آیا مطمئن هستید که می‌خواهید همه Mapping ها را پاک کنید؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.mappings.clear()
            self.target_list.mappings.clear()
            
            # بازنشانی نمایش
            for i in range(self.target_list.count()):
                item = self.target_list.item(i)
                excel_col = item.data(Qt.ItemDataRole.UserRole)
                item.setText(f"⬜ {excel_col}")
                item.setForeground(QColor("#000000"))
    
    def show_preview(self):
        """نمایش پیش‌نمایش Mapping ها"""
        if not self.mappings:
            QMessageBox.information(self, "اطلاعات", "هیچ Mapping ای تعریف نشده است")
            return
        
        # ساخت متن پیش‌نمایش
        preview_text = "📋 **پیش‌نمایش Mapping ها:**\n\n"
        
        for excel_col, mapping in self.mappings.items():
            source_col = mapping['source_column']
            source_sheet = mapping['source_sheet']
            sheet_name = self.available_sheets[source_sheet]['name']
            formula = mapping.get('formula')
            
            preview_text += f"✅ **{excel_col}** ← `{source_col}` از `{sheet_name}`\n"
            if formula:
                preview_text += f"   ⚡ Formula: `{formula}`\n"
            preview_text += "\n"
        
        # نمایش در MessageBox
        msg = QMessageBox(self)
        msg.setWindowTitle("پیش‌نمایش Mapping")
        msg.setText(preview_text)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()
    
    def get_mappings(self):
        """دریافت Mapping های ایجاد شده"""
        return self.mappings
    
    def set_mappings(self, mappings):
        """تنظیم Mapping ها (برای ویرایش)"""
        self.mappings = mappings
        self.target_list.mappings = mappings
        
        # به‌روزرسانی نمایش
        for excel_col, mapping in mappings.items():
            source_col = mapping['source_column']
            has_formula = mapping.get('formula') is not None
            
            # پیدا کردن آیتم مربوطه
            for i in range(self.target_list.count()):
                item = self.target_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == excel_col:
                    if has_formula:
                        item.setText(f"⚡ {excel_col} ← {source_col} [+Formula]")
                        item.setForeground(QColor("#FF9800"))
                    else:
                        item.setText(f"✅ {excel_col} ← {source_col}")
                        item.setForeground(QColor("#4CAF50"))
                    break
