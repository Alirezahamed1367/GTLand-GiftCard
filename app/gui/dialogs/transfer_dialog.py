"""
Transfer Dialog - دیالوگ انتقال داده به Stage 2
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QProgressBar, QTextEdit, QGroupBox, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from datetime import datetime

from app.core.database import DatabaseManager
from app.models.financial import get_financial_session, RawData
from app.core.financial.data_processor import DataProcessor


class TransferThread(QThread):
    """
    Thread برای انتقال داده به Stage 2
    """
    progress = pyqtSignal(int, str)  # درصد، پیام
    finished = pyqtSignal(dict)  # آمار
    error = pyqtSignal(str)
    
    def __init__(self, sheet_ids, options):
        super().__init__()
        self.sheet_ids = sheet_ids
        self.options = options
    
    def run(self):
        try:
            db_manager = DatabaseManager()
            financial_db = get_financial_session()
            
            total_stats = {
                "total_rows": 0,
                "new_rows": 0,
                "processed": 0,
                "marked_transferred": 0,
                "errors": 0
            }
            
            for i, sheet_id in enumerate(self.sheet_ids):
                try:
                    # گرفتن اطلاعات شیت
                    sheet_config = db_manager.get_sheet_config(sheet_id)
                    if not sheet_config:
                        continue
                    
                    sheet_name = sheet_config['name']
                    self.progress.emit(
                        int((i / len(self.sheet_ids)) * 50),
                        f"📊 در حال پردازش: {sheet_name}"
                    )
                    
                    # گرفتن داده‌های استخراج شده که هنوز منتقل نشده‌اند
                    if self.options.get('only_non_transferred', True):
                        # فقط داده‌های منتقل نشده
                        data_rows = db_manager.get_extracted_data(
                            sheet_id, 
                            include_exported=True
                        )
                        # فیلتر: فقط ردیف‌هایی که transferred != 1
                        data_rows = [row for row in data_rows if row.get('transferred') != 1]
                    else:
                        # همه داده‌ها
                        data_rows = db_manager.get_extracted_data(
                            sheet_id,
                            include_exported=True
                        )
                    
                    if not data_rows:
                        self.progress.emit(
                            int((i / len(self.sheet_ids)) * 50),
                            f"⚠️ {sheet_name}: داده‌ای برای انتقال یافت نشد"
                        )
                        continue
                    
                    total_stats["total_rows"] += len(data_rows)
                    
                    # تبدیل به raw_data
                    self.progress.emit(
                        int((i / len(self.sheet_ids)) * 50) + 10,
                        f"🔄 تبدیل {len(data_rows)} ردیف به raw_data..."
                    )
                    
                    # تشخیص نوع شیت
                    sheet_type = self._detect_sheet_type(sheet_name)
                    
                    for j, row in enumerate(data_rows):
                        try:
                            # بررسی وجود در raw_data
                            data_dict = row['data']
                            unique_key = RawData.generate_unique_key(
                                data_dict,
                                ['CODE', 'TR_ID', 'Sold_Date', 'Customer', 'Rate']
                            )
                            
                            existing = financial_db.query(RawData).filter(
                                RawData.unique_key == unique_key
                            ).first()
                            
                            if not existing:
                                # ایجاد RawData جدید
                                raw = RawData(
                                    sheet_name=sheet_name,
                                    sheet_id=sheet_id,
                                    unique_key=unique_key,
                                    unique_key_fields=['CODE', 'TR_ID', 'Sold_Date', 'Customer', 'Rate'],
                                    data=data_dict,
                                    row_number=row['row_number'],
                                    is_extracted=True,  # برای پردازش
                                    is_processed=False,
                                    import_source='gt_land_transfer'
                                )
                                financial_db.add(raw)
                                total_stats["new_rows"] += 1
                            
                            financial_db.commit()
                            
                        except Exception as e:
                            financial_db.rollback()
                            total_stats["errors"] += 1
                            print(f"❌ خطا در ردیف {j}: {e}")
                    
                    # پردازش (Stage 1 → Stage 2)
                    if self.options.get('auto_process', True):
                        self.progress.emit(
                            int((i / len(self.sheet_ids)) * 50) + 30,
                            f"⚙️ پردازش {sheet_name} به Stage 2..."
                        )
                        
                        processor = DataProcessor(financial_db)
                        process_stats = processor.process_sheet(
                            sheet_name=sheet_name,
                            sheet_type=sheet_type,
                            enable_grouping=self.options.get('enable_grouping', True)
                        )
                        
                        total_stats["processed"] += process_stats.get("processed_rows", 0)
                    
                    # علامت‌گذاری به عنوان منتقل شده
                    if self.options.get('mark_as_transferred', True):
                        self.progress.emit(
                            int((i / len(self.sheet_ids)) * 50) + 40,
                            f"✅ علامت‌گذاری {sheet_name} به عنوان منتقل شده..."
                        )
                        
                        # بروزرسانی فیلد transferred در sales_data
                        for row in data_rows:
                            db_manager.mark_as_transferred(row['id'])
                            total_stats["marked_transferred"] += 1
                    
                except Exception as e:
                    self.error.emit(f"خطا در {sheet_name}: {str(e)}")
                    total_stats["errors"] += 1
            
            financial_db.close()
            
            self.progress.emit(100, "✅ اتمام انتقال")
            self.finished.emit(total_stats)
            
        except Exception as e:
            self.error.emit(f"خطای کلی: {str(e)}")
    
    def _detect_sheet_type(self, sheet_name):
        """تشخیص نوع شیت بر اساس نام"""
        name_lower = sheet_name.lower()
        
        if 'buy' in name_lower or 'purchase' in name_lower or 'خرید' in name_lower:
            return 'purchase'
        elif 'bonus' in name_lower or 'بونوس' in name_lower or 'silver' in name_lower:
            return 'bonus'
        else:
            return 'sale'


class TransferToStage2Dialog(QDialog):
    """
    دیالوگ انتقال به مرحله بعد
    """
    
    def __init__(self, selected_sheet_ids, parent=None):
        super().__init__(parent)
        self.selected_sheet_ids = selected_sheet_ids
        self.db_manager = DatabaseManager()
        
        self.setWindowTitle("🚀 انتقال به مرحله بعدی (Stage 2)")
        self.setMinimumSize(700, 600)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        self.init_ui()
        self.load_sheet_info()
    
    def init_ui(self):
        """ایجاد رابط کاربری"""
        layout = QVBoxLayout(self)
        
        # عنوان
        title = QLabel("🚀 انتقال داده‌ها به سیستم مالی (Stage 2)")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #7c3aed; padding: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # توضیحات
        desc = QLabel(
            "📌 این عملیات داده‌های استخراج شده را به دیتابیس مالی منتقل می‌کند\n"
            "📌 داده‌ها بر اساس نقش‌های تعریف شده پردازش می‌شوند\n"
            "📌 پس از انتقال، داده‌ها در گزارش‌ساز هوشمند قابل استفاده هستند"
        )
        desc.setStyleSheet("background: #f0f0f0; padding: 10px; border-radius: 5px; color: #333;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # جدول شیت‌های انتخاب شده
        group_sheets = QGroupBox("📋 شیت‌های انتخاب شده")
        group_sheets_layout = QVBoxLayout(group_sheets)
        
        self.sheets_table = QTableWidget()
        self.sheets_table.setColumnCount(3)
        self.sheets_table.setHorizontalHeaderLabels(["نام شیت", "تعداد داده", "وضعیت"])
        self.sheets_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.sheets_table.setAlternatingRowColors(True)
        self.sheets_table.setMaximumHeight(200)
        group_sheets_layout.addWidget(self.sheets_table)
        
        layout.addWidget(group_sheets)
        
        # گزینه‌ها
        group_options = QGroupBox("⚙️ گزینه‌های انتقال")
        group_options_layout = QVBoxLayout(group_options)
        
        self.only_non_transferred_check = QCheckBox("✅ فقط داده‌های منتقل نشده (پیشنهاد)")
        self.only_non_transferred_check.setChecked(True)
        self.only_non_transferred_check.setToolTip(
            "فقط داده‌هایی که قبلاً منتقل نشده‌اند را انتقال بده\n"
            "این گزینه از تکرار داده‌ها جلوگیری می‌کند"
        )
        group_options_layout.addWidget(self.only_non_transferred_check)
        
        self.auto_process_check = QCheckBox("⚡ پردازش خودکار (Stage 1 → Stage 2)")
        self.auto_process_check.setChecked(True)
        self.auto_process_check.setToolTip(
            "بعد از انتقال، خودکار داده‌ها را پردازش کند\n"
            "داده‌ها به محصولات، فروش‌ها، خریدها، و مشتریان تبدیل می‌شوند"
        )
        group_options_layout.addWidget(self.auto_process_check)
        
        self.enable_grouping_check = QCheckBox("🔗 گروه‌بندی هوشمند فروش‌ها")
        self.enable_grouping_check.setChecked(True)
        self.enable_grouping_check.setToolTip(
            "فروش‌های مشابه (محصول، مشتری، نرخ، تاریخ یکسان) را ترکیب می‌کند"
        )
        group_options_layout.addWidget(self.enable_grouping_check)
        
        self.mark_transferred_check = QCheckBox("🏷️ علامت‌گذاری به عنوان 'منتقل شده'")
        self.mark_transferred_check.setChecked(True)
        self.mark_transferred_check.setToolTip(
            "داده‌های منتقل شده را علامت‌گذاری می‌کند\n"
            "در دفعات بعدی، داده‌های علامت‌گذاری شده دوباره منتقل نمی‌شوند"
        )
        group_options_layout.addWidget(self.mark_transferred_check)
        
        layout.addWidget(group_options)
        
        # پیشرفت
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # لاگ
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setVisible(False)
        layout.addWidget(self.log_text)
        
        # دکمه‌ها
        buttons_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("🚀 شروع انتقال")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: #7c3aed;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px 30px;
                font-size: 12pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #6d28d9;
            }
        """)
        self.start_btn.clicked.connect(self.start_transfer)
        buttons_layout.addWidget(self.start_btn)
        
        self.cancel_btn = QPushButton("❌ انصراف")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px 30px;
                font-size: 12pt;
            }
            QPushButton:hover {
                background: #5a6268;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_sheet_info(self):
        """بارگذاری اطلاعات شیت‌ها"""
        self.sheets_table.setRowCount(len(self.selected_sheet_ids))
        
        total_rows = 0
        
        for i, sheet_id in enumerate(self.selected_sheet_ids):
            sheet_config = self.db_manager.get_sheet_config(sheet_id)
            if not sheet_config:
                continue
            
            # نام شیت
            self.sheets_table.setItem(i, 0, QTableWidgetItem(sheet_config['name']))
            
            # تعداد داده‌های منتقل نشده
            all_data = self.db_manager.get_extracted_data(sheet_id, include_exported=True)
            non_transferred = [row for row in all_data if row.get('transferred') != 1]
            
            self.sheets_table.setItem(i, 1, QTableWidgetItem(f"{len(non_transferred)} ردیف"))
            total_rows += len(non_transferred)
            
            # وضعیت
            if len(non_transferred) > 0:
                status = "✅ آماده انتقال"
            else:
                status = "⚠️ همه منتقل شده"
            self.sheets_table.setItem(i, 2, QTableWidgetItem(status))
        
        # بروزرسانی عنوان
        if total_rows == 0:
            QMessageBox.warning(
                self, "هشدار",
                "⚠️ همه داده‌ها قبلاً منتقل شده‌اند!\n\n"
                "برای انتقال مجدد، گزینه 'فقط داده‌های منتقل نشده' را غیرفعال کنید."
            )
    
    def start_transfer(self):
        """شروع انتقال"""
        # نمایش progress bar و log
        self.progress_bar.setVisible(True)
        self.log_text.setVisible(True)
        self.start_btn.setEnabled(False)
        
        # جمع‌آوری گزینه‌ها
        options = {
            'only_non_transferred': self.only_non_transferred_check.isChecked(),
            'auto_process': self.auto_process_check.isChecked(),
            'enable_grouping': self.enable_grouping_check.isChecked(),
            'mark_as_transferred': self.mark_transferred_check.isChecked()
        }
        
        # شروع thread
        self.transfer_thread = TransferThread(self.selected_sheet_ids, options)
        self.transfer_thread.progress.connect(self.on_progress)
        self.transfer_thread.finished.connect(self.on_finished)
        self.transfer_thread.error.connect(self.on_error)
        self.transfer_thread.start()
    
    def on_progress(self, percent, message):
        """بروزرسانی پیشرفت"""
        self.progress_bar.setValue(percent)
        self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    
    def on_finished(self, stats):
        """اتمام انتقال"""
        self.log_text.append("\n" + "="*50)
        self.log_text.append("✅ انتقال با موفقیت انجام شد!")
        self.log_text.append("="*50)
        self.log_text.append(f"📊 کل ردیف‌ها: {stats['total_rows']}")
        self.log_text.append(f"➕ ردیف‌های جدید: {stats['new_rows']}")
        self.log_text.append(f"⚙️ پردازش شده: {stats['processed']}")
        self.log_text.append(f"🏷️ علامت‌گذاری شده: {stats['marked_transferred']}")
        self.log_text.append(f"❌ خطاها: {stats['errors']}")
        
        self.start_btn.setText("✅ اتمام - بستن پنجره")
        self.start_btn.setEnabled(True)
        self.start_btn.clicked.disconnect()
        self.start_btn.clicked.connect(self.accept)
    
    def on_error(self, error_msg):
        """مدیریت خطا"""
        self.log_text.append(f"\n❌ خطا: {error_msg}")
        QMessageBox.critical(self, "خطا", error_msg)
        self.start_btn.setEnabled(True)
