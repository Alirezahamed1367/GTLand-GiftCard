"""
Smart Import Wizard - ویزارد Import هوشمند با گروه‌بندی خودکار
================================================================
Import از Google Sheets با:
- Unique Key هوشمند
- گروه‌بندی خودکار فروش‌ها
- تشخیص تداخل
"""
from PyQt6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
    QProgressBar, QTextEdit, QCheckBox, QMessageBox, QGroupBox,
    QRadioButton, QSpinBox, QHeaderView, QLineEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from datetime import datetime
import uuid

from app.models.financial import (
    FieldRole, FieldMapping, RawData,
    get_financial_session
)
from app.models.sheet_config import SheetConfig
from app.core.database import db_manager
from app.core.google_sheets import GoogleSheetExtractor
from app.core.financial.data_processor import DataProcessor


class ImportThread(QThread):
    """
    Thread برای Import
    """
    progress = pyqtSignal(int, str)  # درصد، پیام
    finished = pyqtSignal(dict)  # آمار
    error = pyqtSignal(str)
    
    def __init__(self, config):
        super().__init__()
        self.config = config
    
    def run(self):
        try:
            db = get_financial_session()
            
            # 1. دریافت داده از Google Sheets
            self.progress.emit(10, "📥 دریافت داده از Google Sheets...")
            
            gs_extractor = GoogleSheetExtractor()
            
            # استفاده از URL واقعی شیت
            sheet_url = self.config.get('sheet_url')
            worksheet_name = self.config.get('worksheet_name')
            
            if not sheet_url:
                self.error.emit("URL شیت یافت نشد. لطفاً در قسمت 'شیت‌ها' شیت را تنظیم کنید.")
                return
            
            # دریافت داده
            sheet_data = gs_extractor.extract_ready_rows(
                sheet_url=sheet_url,
                worksheet_name=worksheet_name,
                ready_column=None,  # فعلاً بدون فیلتر
                extracted_column=None,
                columns_to_extract=None,
                skip_rows=0
            )
            
            if not sheet_data:
                self.error.emit("خطا در دریافت داده از شیت")
                return
            
            if not sheet_data or len(sheet_data) < 2:
                self.error.emit("شیت خالی است یا فقط هدر دارد")
                return
            
            headers = sheet_data[0]
            rows = sheet_data[1:]
            
            self.progress.emit(20, f"✅ {len(rows)} ردیف دریافت شد")
            
            # 2. تولید Unique Key
            self.progress.emit(30, "🔑 تولید Unique Key...")
            
            unique_key_fields = self._get_unique_key_fields(db)
            batch_id = str(uuid.uuid4())[:8]
            
            # ایجاد ImportBatch
            import_batch = ImportBatch(
                batch_id=batch_id,
                sheet_name=self.config['sheet_name'],
                sheet_id=self.config['sheet_id'],
                total_rows=len(rows),
                unique_key_fields=unique_key_fields,
                status='running'
            )
            db.add(import_batch)
            db.commit()
            
            # 3. Import ردیف‌ها
            self.progress.emit(40, "📊 Import داده‌ها...")
            
            stats = {
                "new": 0,
                "updated": 0,
                "unchanged": 0,
                "conflicts": 0,
                "errors": 0
            }
            
            for i, row_data in enumerate(rows):
                try:
                    # تبدیل به دیکشنری
                    data_dict = {}
                    for j, value in enumerate(row_data):
                        if j < len(headers):
                            data_dict[headers[j]] = value
                    
                    # تولید unique key
                    unique_key = RawData.generate_unique_key(data_dict, unique_key_fields)
                    
                    # بررسی وجود
                    existing = db.query(RawData).filter(
                        RawData.unique_key == unique_key
                    ).first()
                    
                    if existing:
                        # بررسی تغییرات
                        has_changed, changes = existing.detect_changes(data_dict)
                        
                        if has_changed:
                            # داده تغییر کرده
                            existing.previous_data = existing.data
                            existing.data = data_dict
                            existing.data_hash = RawData.generate_data_hash(data_dict)
                            existing.change_detected_at = datetime.now()
                            existing.change_reason = 'data_changed'
                            existing.last_seen_at = datetime.now()
                            
                            # اگر Extracted باشد، conflict می‌شود
                            if existing.is_extracted:
                                existing.has_conflict = True
                                existing.conflict_type = 'data_mismatch'
                                stats["conflicts"] += 1
                            else:
                                stats["updated"] += 1
                        else:
                            # بدون تغییر
                            existing.last_seen_at = datetime.now()
                            stats["unchanged"] += 1
                    else:
                        # ردیف جدید
                        # همیشه is_extracted=True برای پردازش خودکار
                        # (اگر ستون Extracted در شیت وجود داشت، از اون استفاده می‌کنیم)
                        extracted_value = data_dict.get('Extracted', 'FALSE')
                        is_extracted_bool = str(extracted_value).strip().upper() == 'TRUE'
                        
                        # اگر auto_process فعال باشه، همیشه True
                        if self.config.get('auto_process', False):
                            is_extracted_bool = True
                        
                        raw = RawData(
                            sheet_name=self.config['sheet_name'],
                            sheet_id=self.config['sheet_id'],
                            unique_key=unique_key,
                            unique_key_fields=unique_key_fields,
                            data=data_dict,
                            row_number=i + 2,  # +2 چون ردیف 1 هدر است
                            is_extracted=is_extracted_bool,
                            import_batch_id=batch_id,
                            import_source='google_sheets'
                        )
                        db.add(raw)
                        stats["new"] += 1
                    
                    # Commit بعد از هر ردیف موفق
                    db.commit()
                    
                    # بروزرسانی پیشرفت
                    progress_pct = 40 + int((i / len(rows)) * 40)
                    self.progress.emit(progress_pct, f"Import شد: {i+1}/{len(rows)}")
                    
                except Exception as e:
                    # Rollback در صورت خطا
                    db.rollback()
                    stats["errors"] += 1
                    print(f"❌ خطا در ردیف {i+2}: {e}")
            
            # 4. پردازش (Stage 1 → Stage 2)
            if self.config.get('auto_process', False):
                self.progress.emit(85, "⚙️ پردازش داده‌ها...")
                
                processor = DataProcessor(db)
                process_stats = processor.process_sheet(
                    sheet_name=self.config['sheet_name'],
                    sheet_type=self.config.get('sheet_type', 'sale'),
                    enable_grouping=self.config.get('enable_grouping', True)
                )
                
                stats.update(process_stats)
            
            # 5. بروزرسانی آمار batch
            import_batch.new_rows = stats["new"]
            import_batch.updated_rows = stats["updated"]
            import_batch.unchanged_rows = stats["unchanged"]
            import_batch.error_rows = stats["errors"]
            import_batch.status = 'completed'
            import_batch.completed_at = datetime.now()
            
            duration = (datetime.now() - import_batch.started_at).total_seconds()
            import_batch.duration_seconds = int(duration)
            
            db.commit()
            db.close()
            
            self.progress.emit(100, "✅ اتمام Import")
            self.finished.emit(stats)
            
        except Exception as e:
            self.error.emit(f"خطای کلی: {str(e)}")
    
    def _get_unique_key_fields(self, db):
        """دریافت فیلدهای Unique Key"""
        roles = db.query(FieldRole).filter(
            FieldRole.used_in_unique_key == True,
            FieldRole.is_active == True
        ).order_by(FieldRole.unique_key_priority).all()
        
        field_names = []
        for role in roles:
            fields = db.query(CustomField).filter(
                CustomField.role_id == role.id,
                CustomField.is_active == True
            ).all()
            
            for field in fields:
                field_names.append(field.name)
        
        return field_names or ['CODE', 'TR_ID', 'Sold_Date', 'Customer', 'Rate']


class SheetSelectionPage(QWizardPage):
    """
    صفحه 1: انتخاب شیت
    """
    
    def __init__(self):
        super().__init__()
        self.setTitle("انتخاب شیت")
        self.setSubTitle("شیت Google Sheets را برای Import انتخاب کنید")
        
        layout = QVBoxLayout()
        
        # انتخاب شیت
        sheet_layout = QHBoxLayout()
        sheet_layout.addWidget(QLabel("شیت:"))
        self.sheet_combo = QComboBox()
        self._load_sheets()
        sheet_layout.addWidget(self.sheet_combo)
        
        # نمایش نوع شیت انتخاب شده
        self.sheet_type_label = QLabel("🔍 ابتدا یک شیت را انتخاب کنید")
        self.sheet_type_label.setStyleSheet("""
            padding: 12px;
            background: #FFF9C4;
            border: 2px solid #FBC02D;
            border-radius: 5px;
            font-weight: bold;
            font-size: 11pt;
        """)
        sheet_layout.addWidget(self.sheet_type_label)
        
        # به‌روزرسانی نوع شیت هنگام تغییر انتخاب
        self.sheet_combo.currentIndexChanged.connect(self._on_sheet_changed)
        
        layout.addLayout(sheet_layout)
        
        # گروه‌بندی
        grouping_group = QGroupBox("گروه‌بندی هوشمند")
        grouping_layout = QVBoxLayout()
        
        self.enable_grouping_check = QCheckBox("فعال‌سازی گروه‌بندی خودکار فروش‌ها")
        self.enable_grouping_check.setChecked(True)
        grouping_layout.addWidget(self.enable_grouping_check)
        
        info_label = QLabel(
            "💡 گروه‌بندی خودکار: ردیف‌های پشت سر هم با شرایط یکسان "
            "(تاریخ، کد، مشتری، نرخ) به یک تراکنش تبدیل می‌شوند."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-size: 11px;")
        grouping_layout.addWidget(info_label)
        
        grouping_group.setLayout(grouping_layout)
        layout.addWidget(grouping_group)
        
        # پردازش خودکار
        self.auto_process_check = QCheckBox("پردازش خودکار پس از Import (Stage 1 → Stage 2)")
        self.auto_process_check.setChecked(True)
        layout.addWidget(self.auto_process_check)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def _load_sheets(self):
        """بارگذاری شیت‌های موجود از دیتابیس"""
        try:
            session = db_manager.get_session()
            sheets = session.query(SheetConfig).filter(
                SheetConfig.is_active == True
            ).all()
            
            self.sheet_data = {}
            for sheet in sheets:
                self.sheet_combo.addItem(sheet.name)
                self.sheet_data[sheet.name] = {
                    'id': sheet.id,
                    'url': sheet.sheet_url,
                    'worksheet': sheet.worksheet_name,
                    'sheet_type': sheet.sheet_type,  # ⭐ اضافه شد!
                    'config': sheet
                }
            
            if not sheets:
                self.sheet_combo.addItem("⚠️ هیچ شیتی تعریف نشده - ابتدا به قسمت 'شیت‌ها' بروید")
                
        except Exception as e:
            print(f"خطا در بارگذاری شیت‌ها: {e}")
            self.sheet_combo.addItem("❌ خطا در بارگذاری شیت‌ها")
    
    def _on_sheet_changed(self):
        """به‌روزرسانی نمایش نوع شیت"""
        sheet_name = self.sheet_combo.currentText()
        sheet_info = self.sheet_data.get(sheet_name, {})
        sheet_type = sheet_info.get('sheet_type', '')
        
        type_icons = {
            'Purchase': '🛒',
            'Sale': '💰',
            'Bonus': '🎁'
        }
        type_names = {
            'Purchase': 'خرید',
            'Sale': 'فروش',
            'Bonus': 'بونوس'
        }
        
        if sheet_type:
            icon = type_icons.get(sheet_type, '📄')
            name = type_names.get(sheet_type, sheet_type)
            self.sheet_type_label.setText(f"{icon} نوع شیت: {name} ({sheet_type})")
            self.sheet_type_label.setStyleSheet("""
                padding: 12px;
                background: #C8E6C9;
                border: 2px solid #4CAF50;
                border-radius: 5px;
                font-weight: bold;
                font-size: 11pt;
            """)
        else:
            self.sheet_type_label.setText("⚠️ نوع شیت تعریف نشده است!")
            self.sheet_type_label.setStyleSheet("""
                padding: 12px;
                background: #FFCDD2;
                border: 2px solid #F44336;
                border-radius: 5px;
                font-weight: bold;
                font-size: 11pt;
            """)
    
    def get_config(self):
        """دریافت تنظیمات"""
        sheet_name = self.sheet_combo.currentText()
        sheet_info = self.sheet_data.get(sheet_name, {})
        
        # ⭐ نوع شیت از دیتابیس می‌آید (نه از انتخاب کاربر)
        sheet_type = sheet_info.get('sheet_type', 'Sale')
        
        return {
            'sheet_name': sheet_name,
            'sheet_id': sheet_info.get('id'),  # ⭐ اضافه شد
            'sheet_url': sheet_info.get('url'),
            'worksheet_name': sheet_info.get('worksheet'),
            'sheet_config': sheet_info.get('config'),
            'sheet_type': sheet_type,
            'enable_grouping': self.enable_grouping_check.isChecked(),
            'auto_process': self.auto_process_check.isChecked()
        }


class ImportProgressPage(QWizardPage):
    """
    صفحه 2: پیشرفت Import
    """
    
    def __init__(self):
        super().__init__()
        self.setTitle("Import در حال اجراست...")
        self.setSubTitle("لطفاً صبر کنید")
        
        layout = QVBoxLayout()
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        layout.addWidget(self.progress_bar)
        
        # پیام
        self.status_label = QLabel("در حال شروع...")
        layout.addWidget(self.status_label)
        
        # لاگ
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def update_progress(self, percent, message):
        """بروزرسانی پیشرفت"""
        self.progress_bar.setValue(percent)
        self.status_label.setText(message)
        self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")


class ImportSummaryPage(QWizardPage):
    """
    صفحه 3: خلاصه نتایج
    """
    
    def __init__(self):
        super().__init__()
        self.setTitle("✅ Import کامل شد")
        self.setSubTitle("خلاصه نتایج")
        
        layout = QVBoxLayout()
        
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        layout.addWidget(self.summary_text)
        
        self.setLayout(layout)
    
    def show_stats(self, stats):
        """نمایش آمار"""
        summary = f"""
<h2>📊 خلاصه Import</h2>

<h3>Stage 1: Raw Data</h3>
<ul>
    <li>✅ ردیف‌های جدید: <b>{stats.get('new', 0)}</b></li>
    <li>🔄 ردیف‌های بروز شده: <b>{stats.get('updated', 0)}</b></li>
    <li>⚪ بدون تغییر: <b>{stats.get('unchanged', 0)}</b></li>
    <li>⚠️ تداخل: <b>{stats.get('conflicts', 0)}</b></li>
    <li>❌ خطا: <b>{stats.get('errors', 0)}</b></li>
</ul>

<h3>Stage 2: Processed Data</h3>
<ul>
    <li>📦 محصولات جدید: <b>{stats.get('new_products', 0)}</b></li>
    <li>🛒 خریدهای جدید: <b>{stats.get('new_purchases', 0)}</b></li>
    <li>💰 فروش‌های جدید: <b>{stats.get('new_sales', 0)}</b></li>
    <li>🎁 بونوس‌های جدید: <b>{stats.get('new_bonuses', 0)}</b></li>
    <li>👥 مشتریان جدید: <b>{stats.get('new_customers', 0)}</b></li>
    <li>🔗 تراکنش‌های گروه‌بندی شده: <b>{stats.get('grouped_transactions', 0)}</b></li>
</ul>

<p style="color: green; font-size: 14px;">
✅ Import با موفقیت کامل شد!
</p>
        """
        
        self.summary_text.setHtml(summary)


class SmartImportWizard(QWizard):
    """
    ویزارد Import هوشمند
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("🚀 Import هوشمند از Google Sheets")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.resize(700, 500)
        
        # صفحات
        self.sheet_page = SheetSelectionPage()
        self.progress_page = ImportProgressPage()
        self.summary_page = ImportSummaryPage()
        
        self.addPage(self.sheet_page)
        self.addPage(self.progress_page)
        self.addPage(self.summary_page)
        
        # اتصال سیگنال‌ها
        self.currentIdChanged.connect(self.on_page_changed)
    
    def on_page_changed(self, page_id):
        """تغییر صفحه"""
        if page_id == 1:  # صفحه پیشرفت
            # شروع Import
            self.start_import()
    
    def start_import(self):
        """شروع Import"""
        config = self.sheet_page.get_config()
        
        # ایجاد Thread
        self.import_thread = ImportThread(config)
        self.import_thread.progress.connect(self.progress_page.update_progress)
        self.import_thread.finished.connect(self.on_import_finished)
        self.import_thread.error.connect(self.on_import_error)
        
        self.import_thread.start()
    
    def on_import_finished(self, stats):
        """اتمام Import"""
        self.summary_page.show_stats(stats)
        self.next()
    
    def on_import_error(self, error_msg):
        """خطا در Import"""
        QMessageBox.critical(self, "خطا", f"خطا در Import:\n{error_msg}")
        self.reject()
