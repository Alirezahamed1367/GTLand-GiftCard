"""
Conflict Resolution Dialog - مدیریت تداخل‌ها
==========================================
مدیریت موارد زیر:
- Extracted checkbox برداشته شده
- داده تغییر کرده
- Duplicate key
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QTextEdit, QMessageBox,
    QGroupBox, QRadioButton, QHeaderView, QComboBox, QTabWidget, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from datetime import datetime

from app.models.financial import RawData, get_financial_session


class ConflictDetailDialog(QDialog):
    """
    دیالوگ نمایش جزئیات یک تداخل
    """
    
    def __init__(self, parent=None, raw_data=None):
        super().__init__(parent)
        self.raw_data = raw_data
        
        self.setWindowTitle("جزئیات تداخل")
        self.setModal(True)
        self.resize(800, 600)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        if not self.raw_data:
            layout.addWidget(QLabel("❌ داده یافت نشد"))
            self.setLayout(layout)
            return
        
        # اطلاعات کلی
        info_group = QGroupBox("اطلاعات تداخل")
        info_layout = QVBoxLayout()
        
        info_layout.addWidget(QLabel(f"<b>نوع تداخل:</b> {self.raw_data.conflict_type}"))
        info_layout.addWidget(QLabel(f"<b>شیت:</b> {self.raw_data.sheet_name}"))
        info_layout.addWidget(QLabel(f"<b>ردیف:</b> {self.raw_data.row_number}"))
        info_layout.addWidget(QLabel(f"<b>زمان تشخیص:</b> {self.raw_data.change_detected_at}"))
        info_layout.addWidget(QLabel(f"<b>دلیل:</b> {self.raw_data.change_reason}"))
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # مقایسه داده‌ها
        if self.raw_data.previous_data:
            compare_group = QGroupBox("مقایسه داده‌ها")
            compare_layout = QVBoxLayout()
            
            # تب‌ها
            tabs = QTabWidget()
            
            # تب داده فعلی
            current_tab = QTextEdit()
            current_tab.setReadOnly(True)
            current_tab.setPlainText(self._format_json(self.raw_data.data))
            tabs.addTab(current_tab, "✅ داده فعلی")
            
            # تب داده قبلی
            previous_tab = QTextEdit()
            previous_tab.setReadOnly(True)
            previous_tab.setPlainText(self._format_json(self.raw_data.previous_data))
            tabs.addTab(previous_tab, "📜 داده قبلی")
            
            # تب تغییرات
            changes_tab = QTextEdit()
            changes_tab.setReadOnly(True)
            has_changed, changes = self.raw_data.detect_changes(self.raw_data.data)
            changes_text = self._format_changes(changes)
            changes_tab.setHtml(changes_text)
            tabs.addTab(changes_tab, "🔍 تغییرات")
            
            compare_layout.addWidget(tabs)
            compare_group.setLayout(compare_layout)
            layout.addWidget(compare_group)
        
        # راه‌حل‌ها
        solution_group = QGroupBox("راه‌حل")
        solution_layout = QVBoxLayout()
        
        self.keep_new_radio = QRadioButton("✅ نگه داشتن داده جدید (از شیت)")
        self.keep_old_radio = QRadioButton("📜 بازگردانی به داده قبلی")
        self.delete_radio = QRadioButton("🗑️ حذف این ردیف")
        self.reprocess_radio = QRadioButton("🔄 پردازش مجدد")
        
        self.keep_new_radio.setChecked(True)
        
        solution_layout.addWidget(self.keep_new_radio)
        solution_layout.addWidget(self.keep_old_radio)
        solution_layout.addWidget(self.delete_radio)
        solution_layout.addWidget(self.reprocess_radio)
        
        solution_group.setLayout(solution_layout)
        layout.addWidget(solution_group)
        
        # دکمه‌ها
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        apply_btn = QPushButton("✅ اعمال راه‌حل")
        apply_btn.clicked.connect(self.apply_solution)
        btn_layout.addWidget(apply_btn)
        
        cancel_btn = QPushButton("❌ لغو")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def _format_json(self, data):
        """قالب‌بندی JSON"""
        import json
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def _format_changes(self, changes):
        """قالب‌بندی تغییرات"""
        if not changes:
            return "<p>هیچ تغییری یافت نشد</p>"
        
        html = "<table border='1' cellpadding='5' style='border-collapse: collapse; width: 100%;'>"
        html += "<tr><th>فیلد</th><th>مقدار قبلی</th><th>مقدار جدید</th></tr>"
        
        for field, change in changes.items():
            html += f"<tr>"
            html += f"<td><b>{field}</b></td>"
            html += f"<td style='background-color: #ffebee;'>{change['old']}</td>"
            html += f"<td style='background-color: #e8f5e9;'>{change['new']}</td>"
            html += f"</tr>"
        
        html += "</table>"
        return html
    
    def apply_solution(self):
        """اعمال راه‌حل"""
        db = get_financial_session()
        
        try:
            if self.keep_new_radio.isChecked():
                # نگه داشتن داده جدید
                self.raw_data.has_conflict = False
                self.raw_data.conflict_resolved = True
                self.raw_data.conflict_resolution = 'keep_new'
                
            elif self.keep_old_radio.isChecked():
                # بازگردانی به داده قبلی
                if self.raw_data.previous_data:
                    self.raw_data.data = self.raw_data.previous_data
                    self.raw_data.data_hash = RawData.generate_data_hash(self.raw_data.previous_data)
                    self.raw_data.has_conflict = False
                    self.raw_data.conflict_resolved = True
                    self.raw_data.conflict_resolution = 'revert_to_old'
                
            elif self.delete_radio.isChecked():
                # حذف نرم‌افزاری
                self.raw_data.is_deleted = True
                self.raw_data.deleted_at = datetime.now()
                self.raw_data.deleted_reason = 'user_deleted_conflict'
                self.raw_data.has_conflict = False
                self.raw_data.conflict_resolved = True
                self.raw_data.conflict_resolution = 'deleted'
                
            elif self.reprocess_radio.isChecked():
                # پردازش مجدد
                self.raw_data.is_processed = False
                self.raw_data.processed_at = None
                self.raw_data.has_conflict = False
                self.raw_data.conflict_resolved = True
                self.raw_data.conflict_resolution = 'reprocess'
            
            db.commit()
            QMessageBox.information(self, "موفق", "راه‌حل اعمال شد")
            self.accept()
            
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "خطا", f"خطا در اعمال راه‌حل:\n{str(e)}")
        finally:
            db.close()


class ConflictResolutionDialog(QDialog):
    """
    دیالوگ مدیریت تمام تداخل‌ها
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = None
        
        self.setWindowTitle("⚠️ مدیریت تداخل‌ها")
        self.setModal(True)
        self.resize(1000, 600)
        
        self.init_ui()
        self.load_conflicts()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # راهنما
        info_label = QLabel(
            "⚠️ تداخل‌ها زمانی رخ می‌دهند که:\n"
            "• تیک Extracted برداشته شود\n"
            "• داده در شیت تغییر کند\n"
            "• Unique Key تکراری باشد"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("background-color: #fff3cd; padding: 10px; border-radius: 5px;")
        layout.addWidget(info_label)
        
        # فیلتر
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("نوع تداخل:"))
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            "همه",
            "extracted_removed",
            "data_mismatch",
            "duplicate_key"
        ])
        self.filter_combo.currentTextChanged.connect(self.load_conflicts)
        filter_layout.addWidget(self.filter_combo)
        
        filter_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 بروزرسانی")
        refresh_btn.clicked.connect(self.load_conflicts)
        filter_layout.addWidget(refresh_btn)
        
        layout.addLayout(filter_layout)
        
        # جدول تداخل‌ها
        self.conflicts_table = QTableWidget()
        self.conflicts_table.setColumnCount(7)
        self.conflicts_table.setHorizontalHeaderLabels([
            "شناسه", "شیت", "ردیف", "نوع تداخل", 
            "دلیل", "زمان تشخیص", "وضعیت"
        ])
        self.conflicts_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.conflicts_table.horizontalHeader().setStretchLastSection(True)
        self.conflicts_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.conflicts_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.conflicts_table.doubleClicked.connect(self.show_conflict_detail)
        layout.addWidget(self.conflicts_table)
        
        # دکمه‌های عملیات
        btn_layout = QHBoxLayout()
        
        detail_btn = QPushButton("🔍 جزئیات")
        detail_btn.clicked.connect(self.show_conflict_detail)
        btn_layout.addWidget(detail_btn)
        
        resolve_all_btn = QPushButton("✅ حل همه (نگه داشتن داده جدید)")
        resolve_all_btn.clicked.connect(self.resolve_all_keep_new)
        btn_layout.addWidget(resolve_all_btn)
        
        btn_layout.addStretch()
        
        close_btn = QPushButton("❌ بستن")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def load_conflicts(self):
        """بارگذاری تداخل‌ها"""
        self.db = get_financial_session()
        
        # فیلتر
        filter_type = self.filter_combo.currentText()
        
        query = self.db.query(RawData).filter(
            RawData.has_conflict == True,
            RawData.conflict_resolved == False,
            RawData.is_deleted == False
        )
        
        if filter_type != "همه":
            query = query.filter(RawData.conflict_type == filter_type)
        
        conflicts = query.order_by(RawData.change_detected_at.desc()).all()
        
        self.conflicts_table.setRowCount(len(conflicts))
        
        for i, conflict in enumerate(conflicts):
            self.conflicts_table.setItem(i, 0, QTableWidgetItem(str(conflict.id)))
            self.conflicts_table.setItem(i, 1, QTableWidgetItem(conflict.sheet_name))
            self.conflicts_table.setItem(i, 2, QTableWidgetItem(str(conflict.row_number)))
            self.conflicts_table.setItem(i, 3, QTableWidgetItem(conflict.conflict_type or ""))
            self.conflicts_table.setItem(i, 4, QTableWidgetItem(conflict.change_reason or ""))
            
            time_str = conflict.change_detected_at.strftime("%Y-%m-%d %H:%M") if conflict.change_detected_at else ""
            self.conflicts_table.setItem(i, 5, QTableWidgetItem(time_str))
            
            status = "حل نشده"
            self.conflicts_table.setItem(i, 6, QTableWidgetItem(status))
            
            # رنگ‌بندی بر اساس نوع
            color = QColor("#ffebee")  # قرمز ملایم
            if conflict.conflict_type == "data_mismatch":
                color = QColor("#fff3e0")  # نارنجی ملایم
            elif conflict.conflict_type == "duplicate_key":
                color = QColor("#fce4ec")  # صورتی ملایم
            
            for j in range(7):
                item = self.conflicts_table.item(i, j)
                if item:
                    item.setBackground(color)
    
    def show_conflict_detail(self):
        """نمایش جزئیات تداخل"""
        selected = self.conflicts_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "هشدار", "لطفاً یک تداخل را انتخاب کنید")
            return
        
        conflict_id = int(self.conflicts_table.item(selected, 0).text())
        raw_data = self.db.query(RawData).get(conflict_id)
        
        if not raw_data:
            return
        
        dialog = ConflictDetailDialog(self, raw_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_conflicts()
    
    def resolve_all_keep_new(self):
        """حل همه تداخل‌ها با نگه داشتن داده جدید"""
        reply = QMessageBox.question(
            self,
            "تأیید",
            "آیا می‌خواهید همه تداخل‌ها را با نگه داشتن داده جدید حل کنید؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            conflicts = self.db.query(RawData).filter(
                RawData.has_conflict == True,
                RawData.conflict_resolved == False
            ).all()
            
            for conflict in conflicts:
                conflict.has_conflict = False
                conflict.conflict_resolved = True
                conflict.conflict_resolution = 'keep_new'
            
            self.db.commit()
            QMessageBox.information(self, "موفق", f"{len(conflicts)} تداخل حل شد")
            self.load_conflicts()
            
        except Exception as e:
            self.db.rollback()
            QMessageBox.critical(self, "خطا", f"خطا در حل تداخل‌ها:\n{str(e)}")
    
    def closeEvent(self, event):
        """بستن دیتابیس"""
        if self.db:
            self.db.close()
        event.accept()
