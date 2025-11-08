"""
Dialog مدیریت Template های Export
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QScreen

from app.core.database import db_manager
from app.core.logger import app_logger
from app.models import ExportTemplate
from app.utils.ui_constants import (
    FONT_SIZE_TITLE, FONT_SIZE_LABEL, BUTTON_HEIGHT_MEDIUM,
    COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER, COLOR_TEXT_SECONDARY,
    get_button_style, get_responsive_dialog_size
)


class TemplateManagerDialog(QDialog):
    """Dialog مدیریت Template های Export"""
    
    def __init__(self, parent=None, template=None):
        super().__init__(parent)
        self.selected_template = None
        self.init_ui()
        self.center_on_screen()
        self.load_templates()
    
    def center_on_screen(self):
        """مرکز کردن پنجره"""
        screen = QScreen.availableGeometry(self.screen())
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    def init_ui(self):
        """راه‌اندازی رابط کاربری"""
        self.setWindowTitle("مدیریت Template ها")
        
        # محاسبه سایز responsive
        screen = self.screen().availableGeometry()
        width, height = get_responsive_dialog_size(screen, "normal")
        self.resize(width, height)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # عنوان
        title_label = QLabel("📋 مدیریت Template های Export")
        title_font = QFont()
        title_font.setPointSize(FONT_SIZE_TITLE)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # توضیحات
        desc_label = QLabel("Template ها الگوهای از پیش تعریف شده برای Export داده‌ها به Excel هستند")
        desc_label.setStyleSheet("color: #666; padding: 5px;")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)
        
        # جدول Template ها
        self.create_table()
        layout.addWidget(self.templates_table)
        
        # دکمه‌های عملیات
        buttons_layout = self.create_buttons()
        layout.addLayout(buttons_layout)
    
    def create_table(self):
        """ایجاد جدول Template ها"""
        self.templates_table = QTableWidget()
        self.templates_table.setColumnCount(6)
        self.templates_table.setHorizontalHeaderLabels([
            "ID", "نام Template", "توضیحات", "فایل", "نوع", "عملیات"
        ])
        
        # تنظیمات جدول
        self.templates_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.templates_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.templates_table.setAlternatingRowColors(True)
        self.templates_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        # تنظیم عرض ستون‌ها
        header = self.templates_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)           # نام
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)           # توضیحات
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)           # فایل
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # پیش‌فرض
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # عملیات
        
        # استایل
        self.templates_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background: #f5f5f5;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
    
    def create_buttons(self) -> QHBoxLayout:
        """ایجاد دکمه‌ها"""
        layout = QHBoxLayout()
        
        # دکمه Template جدید
        new_btn = QPushButton("➕ Template جدید")
        new_btn.setMinimumHeight(BUTTON_HEIGHT_MEDIUM)
        new_btn.setStyleSheet(get_button_style(COLOR_SUCCESS))
        new_btn.clicked.connect(self.add_template)
        layout.addWidget(new_btn)
        
        layout.addStretch()
        
        # دکمه بستن
        close_btn = QPushButton("بستن")
        close_btn.setMinimumHeight(BUTTON_HEIGHT_MEDIUM)
        close_btn.setMinimumWidth(120)
        close_btn.setStyleSheet(get_button_style(COLOR_TEXT_SECONDARY))
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        return layout
    
    def load_templates(self):
        """بارگذاری Template ها"""
        try:
            with db_manager.get_session() as session:
                templates = session.query(ExportTemplate).filter(
                    ExportTemplate.is_active == True
                ).order_by(
                    ExportTemplate.created_at.desc()
                ).all()
                
                self.templates_table.setRowCount(len(templates))
                
                for row, template in enumerate(templates):
                    # ID
                    id_item = QTableWidgetItem(str(template.id))
                    id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.templates_table.setItem(row, 0, id_item)
                    
                    # نام
                    name_item = QTableWidgetItem(template.name)
                    self.templates_table.setItem(row, 1, name_item)
                    
                    # توضیحات
                    desc = template.description or "-"
                    desc_item = QTableWidgetItem(desc[:50] + "..." if len(desc) > 50 else desc)
                    self.templates_table.setItem(row, 2, desc_item)
                    
                    # فایل
                    from pathlib import Path
                    file_name = Path(template.template_path).name if template.template_path else "-"
                    file_item = QTableWidgetItem(file_name)
                    self.templates_table.setItem(row, 3, file_item)
                    
                    # نوع
                    type_item = QTableWidgetItem(template.template_type or "-")
                    type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.templates_table.setItem(row, 4, type_item)
                    
                    # دکمه‌های عملیات
                    actions_widget = self.create_action_buttons(template)
                    self.templates_table.setCellWidget(row, 5, actions_widget)
                
                # آپدیت لیبل تعداد
                self.update_count_label(len(templates))
                
        except Exception as e:
            app_logger.error(f"Error loading templates: {e}")
            QMessageBox.critical(self, "Error", f"Error loading templates:\n{str(e)}")
    
    def create_action_buttons(self, template):
        """ایجاد دکمه‌های عملیات برای هر سطر"""
        widget = QDialog()
        widget.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)
        
        # دکمه ویرایش
        edit_btn = QPushButton("✏️")
        edit_btn.setToolTip("ویرایش")
        edit_btn.setMaximumWidth(35)
        edit_btn.setStyleSheet("""
            QPushButton {
                background: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background: #1976D2;
            }
        """)
        edit_btn.clicked.connect(lambda: self.edit_template(template))
        layout.addWidget(edit_btn)
        
        # دکمه حذف
        delete_btn = QPushButton("🗑️")
        delete_btn.setToolTip("حذف")
        delete_btn.setMaximumWidth(35)
        delete_btn.setStyleSheet("""
            QPushButton {
                background: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background: #d32f2f;
            }
        """)
        delete_btn.clicked.connect(lambda: self.delete_template(template))
        layout.addWidget(delete_btn)
        
        return widget
    
    def update_count_label(self, count):
        """آپدیت لیبل تعداد"""
        # می‌تونیم بعداً یه status bar اضافه کنیم
        pass
    
    def add_template(self):
        """افزودن Template جدید"""
        try:
            from PyQt6.QtWidgets import QFileDialog, QInputDialog
            import shutil
            from pathlib import Path
            
            # انتخاب فایل Excel
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "انتخاب فایل Excel Template",
                "",
                "Excel Files (*.xlsx *.xls)"
            )
            
            if not file_path:
                return  # کاربر لغو کرد
            
            # دریافت نام Template
            name, ok = QInputDialog.getText(
                self,
                "نام Template",
                "لطفاً نام Template را وارد کنید:",
                text=Path(file_path).stem
            )
            
            if not ok or not name.strip():
                return
            
            name = name.strip()
            
            # دریافت نوع Template
            template_type, ok = QInputDialog.getItem(
                self,
                "نوع Template",
                "نوع Template را انتخاب کنید:",
                ["type1", "type2", "type3", "custom"],
                0,
                True
            )
            
            if not ok:
                template_type = "custom"
            
            # کپی فایل به پوشه templates
            templates_dir = Path("templates")
            templates_dir.mkdir(exist_ok=True)
            
            file_name = Path(file_path).name
            dest_path = templates_dir / file_name
            
            # اگر فایل وجود دارد، نام جدید بگذار
            counter = 1
            while dest_path.exists():
                stem = Path(file_path).stem
                suffix = Path(file_path).suffix
                dest_path = templates_dir / f"{stem}_{counter}{suffix}"
                counter += 1
            
            shutil.copy2(file_path, dest_path)
            
            # ذخیره در دیتابیس
            with db_manager.get_session() as session:
                new_template = ExportTemplate(
                    name=name,
                    template_type=template_type,
                    template_path=str(dest_path),
                    description=f"Template {name}",
                    is_active=True
                )
                session.add(new_template)
                session.commit()
            
            QMessageBox.information(
                self,
                "Success",
                f"Template '{name}' successfully added!"
            )
            
            # رفرش جدول
            self.load_templates()
            
        except Exception as e:
            app_logger.error(f"Error adding template: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(
                self,
                "خطا",
                f"Error adding template:\n{str(e)}"
            )
    
    def edit_template(self, template):
        """ویرایش Template"""
        from PyQt6.QtWidgets import QInputDialog
        
        # ویرایش نام
        new_name, ok = QInputDialog.getText(
            self,
            "ویرایش نام Template",
            "نام جدید:",
            text=template.name
        )
        
        if not ok or not new_name.strip():
            return
        
        new_name = new_name.strip()
        
        # ویرایش نوع
        current_type = template.template_type or "custom"
        new_type, ok = QInputDialog.getItem(
            self,
            "ویرایش نوع Template",
            "نوع Template:",
            ["type1", "type2", "type3", "custom"],
            ["type1", "type2", "type3", "custom"].index(current_type) if current_type in ["type1", "type2", "type3", "custom"] else 3,
            True
        )
        
        if not ok:
            new_type = current_type
        
        # ویرایش توضیحات
        new_desc, ok = QInputDialog.getMultiLineText(
            self,
            "ویرایش توضیحات",
            "توضیحات:",
            template.description or ""
        )
        
        if not ok:
            new_desc = template.description
        
        try:
            # ذخیره تغییرات
            with db_manager.get_session() as session:
                session.query(ExportTemplate).filter(
                    ExportTemplate.id == template.id
                ).update({
                    "name": new_name,
                    "template_type": new_type,
                    "description": new_desc
                })
                session.commit()
            
            QMessageBox.information(
                self,
                "موفقیت",
                f"Template '{new_name}' updated successfully"
            )
            
            # رفرش جدول
            self.load_templates()
            
        except Exception as e:
            app_logger.error(f"Error editing template: {e}")
            QMessageBox.critical(
                self,
                "خطا",
                f"Error editing template:\n{str(e)}"
            )
    
    def delete_template(self, template):
        """حذف Template"""
        reply = QMessageBox.question(
            self,
            "تایید حذف",
            f"آیا از حذف Template '{template.name}' اطمینان دارید؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with db_manager.get_session() as session:
                    # حذف از دیتابیس
                    session.query(ExportTemplate).filter(
                        ExportTemplate.id == template.id
                    ).delete()
                    session.commit()
                
                QMessageBox.information(self, "Success", "Template deleted successfully")
                self.load_templates()  # رفرش جدول
                
            except Exception as e:
                app_logger.error(f"Error deleting template: {e}")
                QMessageBox.critical(self, "Error", f"Error deleting template:\n{str(e)}")


