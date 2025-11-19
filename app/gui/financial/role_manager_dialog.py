"""
Role Manager Dialog - مدیریت نقش‌های فیلدها
==========================================
کاربر می‌تواند نقش‌های دلخواه خود را تعریف کند
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QCheckBox, QSpinBox, QTextEdit, QComboBox, QGroupBox,
    QTabWidget, QWidget, QFormLayout, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIcon

from app.models.financial import (
    FieldRole, RolePreset, CustomField,
    get_financial_session, init_default_roles, init_default_presets
)


class RoleDefinitionDialog(QDialog):
    """
    دیالوگ تعریف یک نقش جدید
    """
    
    def __init__(self, parent=None, role=None):
        super().__init__(parent)
        self.role = role  # برای ویرایش
        self.is_edit_mode = role is not None
        
        self.setWindowTitle("تعریف نقش جدید" if not self.is_edit_mode else "ویرایش نقش")
        self.setModal(True)
        self.resize(600, 500)
        
        self.init_ui()
        
        if self.is_edit_mode:
            self.load_role_data()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # فرم اصلی
        form_layout = QFormLayout()
        
        # نام انگلیسی (name)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("identifier, value, transaction_id, ...")
        form_layout.addRow("نام (انگلیسی):", self.name_input)
        
        # برچسب فارسی
        self.label_fa_input = QLineEdit()
        self.label_fa_input.setPlaceholderText("شناسه، مقدار، شماره تراکنش، ...")
        form_layout.addRow("برچسب (فارسی):", self.label_fa_input)
        
        # برچسب انگلیسی (اختیاری)
        self.label_en_input = QLineEdit()
        self.label_en_input.setPlaceholderText("Identifier, Value, Transaction ID, ...")
        form_layout.addRow("برچسب (انگلیسی):", self.label_en_input)
        
        # دسته‌بندی
        self.category_combo = QComboBox()
        self.category_combo.addItems(["core", "business", "technical", "custom"])
        form_layout.addRow("دسته‌بندی:", self.category_combo)
        
        # توضیحات
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        self.description_input.setPlaceholderText("توضیح کامل این نقش...")
        form_layout.addRow("توضیحات:", self.description_input)
        
        layout.addLayout(form_layout)
        
        # گروه: استفاده در Unique Key
        unique_key_group = QGroupBox("استفاده در Unique Key")
        unique_key_layout = QVBoxLayout()
        
        self.used_in_unique_key_check = QCheckBox("این نقش در تولید Unique Key استفاده شود")
        unique_key_layout.addWidget(self.used_in_unique_key_check)
        
        priority_layout = QHBoxLayout()
        priority_layout.addWidget(QLabel("اولویت:"))
        self.unique_key_priority_spin = QSpinBox()
        self.unique_key_priority_spin.setMinimum(1)
        self.unique_key_priority_spin.setMaximum(100)
        self.unique_key_priority_spin.setValue(10)
        priority_layout.addWidget(self.unique_key_priority_spin)
        priority_layout.addStretch()
        unique_key_layout.addLayout(priority_layout)
        
        unique_key_group.setLayout(unique_key_layout)
        layout.addWidget(unique_key_group)
        
        # گروه: استفاده در گروه‌بندی
        grouping_group = QGroupBox("استفاده در گروه‌بندی")
        grouping_layout = QVBoxLayout()
        
        self.used_in_grouping_check = QCheckBox("این نقش در گروه‌بندی فروش‌ها استفاده شود")
        grouping_layout.addWidget(self.used_in_grouping_check)
        
        grouping_group.setLayout(grouping_layout)
        layout.addWidget(grouping_group)
        
        # دکمه‌ها
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        save_btn = QPushButton("💾 ذخیره")
        save_btn.clicked.connect(self.save_role)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("❌ لغو")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def load_role_data(self):
        """بارگذاری اطلاعات نقش برای ویرایش"""
        if not self.role:
            return
        
        self.name_input.setText(self.role.name)
        self.label_fa_input.setText(self.role.label_fa)
        self.label_en_input.setText(self.role.label_en or "")
        
        category_index = self.category_combo.findText(self.role.category or "custom")
        if category_index >= 0:
            self.category_combo.setCurrentIndex(category_index)
        
        self.description_input.setPlainText(self.role.description or "")
        
        self.used_in_unique_key_check.setChecked(self.role.used_in_unique_key)
        if self.role.unique_key_priority:
            self.unique_key_priority_spin.setValue(self.role.unique_key_priority)
        
        self.used_in_grouping_check.setChecked(self.role.used_in_grouping)
    
    def save_role(self):
        """ذخیره نقش"""
        name = self.name_input.text().strip()
        label_fa = self.label_fa_input.text().strip()
        
        if not name or not label_fa:
            QMessageBox.warning(self, "خطا", "نام و برچسب فارسی الزامی است")
            return
        
        self.role_data = {
            "name": name,
            "label_fa": label_fa,
            "label_en": self.label_en_input.text().strip() or None,
            "category": self.category_combo.currentText(),
            "description": self.description_input.toPlainText().strip() or None,
            "used_in_unique_key": self.used_in_unique_key_check.isChecked(),
            "unique_key_priority": self.unique_key_priority_spin.value() if self.used_in_unique_key_check.isChecked() else None,
            "used_in_grouping": self.used_in_grouping_check.isChecked(),
            "is_active": True,
            "is_system": False
        }
        
        self.accept()


class RoleManagerDialog(QDialog):
    """
    دیالوگ مدیریت نقش‌ها
    """
    
    roles_updated = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = None
        
        self.setWindowTitle("🎭 مدیریت نقش‌های فیلدها")
        self.setModal(True)
        self.resize(900, 600)
        
        self.init_ui()
        self.load_roles()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # راهنما
        info_label = QLabel(
            "💡 نقش‌ها تعیین می‌کنند که هر فیلد چه کاری انجام می‌دهد.\n"
            "شما می‌توانید نقش‌های دلخواه خود را تعریف کنید یا از نقش‌های پیش‌فرض استفاده کنید."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("background-color: #e3f2fd; padding: 10px; border-radius: 5px;")
        layout.addWidget(info_label)
        
        # تب‌ها
        tabs = QTabWidget()
        
        # تب 1: نقش‌ها
        roles_tab = QWidget()
        roles_layout = QVBoxLayout()
        
        # دکمه‌های عملیات
        btn_layout = QHBoxLayout()
        
        add_role_btn = QPushButton("➕ نقش جدید")
        add_role_btn.clicked.connect(self.add_role)
        btn_layout.addWidget(add_role_btn)
        
        edit_role_btn = QPushButton("✏️ ویرایش")
        edit_role_btn.clicked.connect(self.edit_role)
        btn_layout.addWidget(edit_role_btn)
        
        delete_role_btn = QPushButton("🗑️ حذف")
        delete_role_btn.clicked.connect(self.delete_role)
        btn_layout.addWidget(delete_role_btn)
        
        btn_layout.addStretch()
        
        init_defaults_btn = QPushButton("🔄 بارگذاری نقش‌های پیش‌فرض")
        init_defaults_btn.clicked.connect(self.init_default_roles)
        btn_layout.addWidget(init_defaults_btn)
        
        roles_layout.addLayout(btn_layout)
        
        # جدول نقش‌ها
        self.roles_table = QTableWidget()
        self.roles_table.setColumnCount(7)
        self.roles_table.setHorizontalHeaderLabels([
            "شناسه", "نام", "برچسب فارسی", "دسته", 
            "در Unique Key", "در گروه‌بندی", "وضعیت"
        ])
        self.roles_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.roles_table.horizontalHeader().setStretchLastSection(True)
        self.roles_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.roles_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.roles_table.doubleClicked.connect(self.edit_role)
        roles_layout.addWidget(self.roles_table)
        
        roles_tab.setLayout(roles_layout)
        tabs.addTab(roles_tab, "📋 نقش‌ها")
        
        # تب 2: پیش‌فرض‌ها
        presets_tab = QWidget()
        presets_layout = QVBoxLayout()
        
        presets_info = QLabel(
            "🎁 پیش‌فرض‌ها مجموعه‌ای از نقش‌های آماده برای شروع سریع هستند.\n"
            "می‌توانید از آن‌ها برای ایجاد نقش‌های جدید استفاده کنید."
        )
        presets_info.setWordWrap(True)
        presets_info.setStyleSheet("background-color: #fff3e0; padding: 10px; border-radius: 5px;")
        presets_layout.addWidget(presets_info)
        
        # جدول پیش‌فرض‌ها
        self.presets_table = QTableWidget()
        self.presets_table.setColumnCount(4)
        self.presets_table.setHorizontalHeaderLabels([
            "شناسه", "عنوان", "دسته", "تعداد نقش‌ها"
        ])
        self.presets_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        presets_layout.addWidget(self.presets_table)
        
        apply_preset_btn = QPushButton("✅ اعمال پیش‌فرض انتخاب شده")
        apply_preset_btn.clicked.connect(self.apply_preset)
        presets_layout.addWidget(apply_preset_btn)
        
        presets_tab.setLayout(presets_layout)
        tabs.addTab(presets_tab, "🎁 پیش‌فرض‌ها")
        
        layout.addWidget(tabs)
        
        # دکمه بستن
        close_btn = QPushButton("✅ بستن")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
    
    def load_roles(self):
        """بارگذاری نقش‌ها"""
        self.db = get_financial_session()
        
        roles = self.db.query(FieldRole).order_by(
            FieldRole.category,
            FieldRole.display_order
        ).all()
        
        self.roles_table.setRowCount(len(roles))
        
        for i, role in enumerate(roles):
            self.roles_table.setItem(i, 0, QTableWidgetItem(str(role.id)))
            self.roles_table.setItem(i, 1, QTableWidgetItem(role.name))
            self.roles_table.setItem(i, 2, QTableWidgetItem(role.label_fa))
            self.roles_table.setItem(i, 3, QTableWidgetItem(role.category or ""))
            
            # در Unique Key
            unique_key_item = QTableWidgetItem("✅" if role.used_in_unique_key else "❌")
            unique_key_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.roles_table.setItem(i, 4, unique_key_item)
            
            # در گروه‌بندی
            grouping_item = QTableWidgetItem("✅" if role.used_in_grouping else "❌")
            grouping_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.roles_table.setItem(i, 5, grouping_item)
            
            # وضعیت
            status_text = "فعال" if role.is_active else "غیرفعال"
            if role.is_system:
                status_text += " (سیستمی)"
            status_item = QTableWidgetItem(status_text)
            self.roles_table.setItem(i, 6, status_item)
            
            # رنگ‌بندی
            if not role.is_active:
                for j in range(7):
                    item = self.roles_table.item(i, j)
                    if item:
                        item.setForeground(QColor("#999999"))
    
    def add_role(self):
        """افزودن نقش جدید"""
        dialog = RoleDefinitionDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                role = FieldRole(**dialog.role_data)
                self.db.add(role)
                self.db.commit()
                
                QMessageBox.information(self, "موفق", f"نقش '{role.label_fa}' ایجاد شد")
                self.load_roles()
                self.roles_updated.emit()
                
            except Exception as e:
                self.db.rollback()
                QMessageBox.critical(self, "خطا", f"خطا در ایجاد نقش:\n{str(e)}")
    
    def edit_role(self):
        """ویرایش نقش"""
        selected = self.roles_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "هشدار", "لطفاً یک نقش را انتخاب کنید")
            return
        
        role_id = int(self.roles_table.item(selected, 0).text())
        role = self.db.query(FieldRole).get(role_id)
        
        if not role:
            return
        
        if role.is_system:
            reply = QMessageBox.question(
                self, 
                "تأیید", 
                "این نقش سیستمی است. آیا مطمئنید که می‌خواهید آن را ویرایش کنید؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        dialog = RoleDefinitionDialog(self, role)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                for key, value in dialog.role_data.items():
                    setattr(role, key, value)
                
                self.db.commit()
                QMessageBox.information(self, "موفق", "نقش بروز شد")
                self.load_roles()
                self.roles_updated.emit()
                
            except Exception as e:
                self.db.rollback()
                QMessageBox.critical(self, "خطا", f"خطا در بروزرسانی:\n{str(e)}")
    
    def delete_role(self):
        """حذف نقش"""
        selected = self.roles_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "هشدار", "لطفاً یک نقش را انتخاب کنید")
            return
        
        role_id = int(self.roles_table.item(selected, 0).text())
        role = self.db.query(FieldRole).get(role_id)
        
        if not role:
            return
        
        if role.is_system:
            QMessageBox.warning(self, "خطا", "نقش‌های سیستمی قابل حذف نیستند")
            return
        
        # بررسی استفاده در CustomField
        fields_count = self.db.query(CustomField).filter(
            CustomField.role_id == role_id
        ).count()
        
        if fields_count > 0:
            reply = QMessageBox.question(
                self,
                "تأیید",
                f"این نقش در {fields_count} فیلد استفاده شده است.\n"
                "آیا مطمئنید که می‌خواهید آن را حذف کنید؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        try:
            self.db.delete(role)
            self.db.commit()
            
            QMessageBox.information(self, "موفق", "نقش حذف شد")
            self.load_roles()
            self.roles_updated.emit()
            
        except Exception as e:
            self.db.rollback()
            QMessageBox.critical(self, "خطا", f"خطا در حذف:\n{str(e)}")
    
    def init_default_roles(self):
        """بارگذاری نقش‌های پیش‌فرض"""
        reply = QMessageBox.question(
            self,
            "تأیید",
            "آیا می‌خواهید نقش‌های پیش‌فرض را بارگذاری کنید؟\n"
            "(نقش‌های موجود حفظ می‌شوند)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            init_default_roles(self.db)
            init_default_presets(self.db)
            
            QMessageBox.information(self, "موفق", "نقش‌های پیش‌فرض بارگذاری شدند")
            self.load_roles()
            self.roles_updated.emit()
            
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در بارگذاری:\n{str(e)}")
    
    def apply_preset(self):
        """اعمال پیش‌فرض"""
        QMessageBox.information(self, "در حال توسعه", "این قابلیت به زودی اضافه می‌شود")
    
    def closeEvent(self, event):
        """بستن دیتابیس"""
        if self.db:
            self.db.close()
        event.accept()
