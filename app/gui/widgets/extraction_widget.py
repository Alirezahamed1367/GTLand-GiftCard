"""
ویجت استخراج داده
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QMessageBox, QProgressBar, QTextEdit, QGroupBox,
    QCheckBox, QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from app.core.database import db_manager
from app.core.google_sheets import GoogleSheetExtractor
from app.core.logger import app_logger
from app.models import ProcessLog
from app.utils.ui_constants import (
    FONT_SIZE_SECTION, BUTTON_HEIGHT_LARGE, COLOR_PRIMARY, 
    COLOR_SUCCESS, get_button_style
)


class ExtractionThread(QThread):
    """Thread برای استخراج داده با لاگ دقیق و مدیریت خطا"""
    progress = pyqtSignal(int, str, str)  # (درصد, پیام, رنگ)
    log = pyqtSignal(str, str)  # (پیام, سطح: info/success/warning/error)
    sub_progress = pyqtSignal(int, int, str)  # (فعلی, کل, پیام) برای نوار پیشرفت جزئی
    finished = pyqtSignal(bool, str, dict)
    
    def __init__(self, selected_sheet_ids=None):
        super().__init__()
        self.logger = app_logger
        self.extractor = GoogleSheetExtractor()
        self.selected_sheet_ids = selected_sheet_ids
        self.is_cancelled = False
    
    def cancel(self):
        """لغو عملیات"""
        self.is_cancelled = True
        self.log.emit("⚠️ در حال لغو عملیات...", "warning")
    
    def run(self):
        """اجرای استخراج با لاگ کامل"""
        try:
            from datetime import datetime
            start_time = datetime.now()
            
            self.progress.emit(5, "🚀 شروع عملیات استخراج...", "#2196F3")
            self.log.emit("="*60, "info")
            self.log.emit(f"🕐 زمان شروع: {start_time.strftime('%Y/%m/%d - %H:%M:%S')}", "info")
            self.log.emit("="*60, "info")
            
            # دریافت شیت‌های فعال
            self.progress.emit(10, "دریافت لیست شیت‌ها...", "#2196F3")
            self.log.emit("\n🔍 دریافت لیست شیت‌های فعال از دیتابیس...", "info")
            
            all_configs = db_manager.get_all_sheet_configs(active_only=True)
            
            if not all_configs:
                self.log.emit("❌ هیچ شیت فعالی یافت نشد!", "error")
                self.finished.emit(False, "هیچ شیت فعالی یافت نشد!", {})
                return
            
            self.log.emit(f"✅ {len(all_configs)} شیت فعال یافت شد", "success")
            
            # فیلتر کردن بر اساس انتخاب کاربر
            if self.selected_sheet_ids:
                configs = [c for c in all_configs if c.id in self.selected_sheet_ids]
                if not configs:
                    self.log.emit("❌ هیچ شیتی انتخاب نشده است!", "error")
                    self.finished.emit(False, "هیچ شیتی انتخاب نشده است!", {})
                    return
                self.log.emit(f"📌 {len(configs)} شیت برای استخراج انتخاب شد", "info")
            else:
                configs = all_configs
                self.log.emit(f"📌 استخراج از تمام {len(configs)} شیت فعال", "info")
            
            # آمارگیری کلی
            total_new = 0
            total_updated = 0
            total_errors = 0
            total_extracted_rows = 0
            all_duplicates = []
            
            # استخراج از هر شیت
            for idx, config in enumerate(configs):
                if self.is_cancelled:
                    self.log.emit("\n⛔ عملیات توسط کاربر لغو شد", "warning")
                    break
                
                progress_pct = 10 + int((idx / len(configs)) * 85)
                self.progress.emit(
                    progress_pct,
                    f"در حال استخراج از '{config.name}' ({idx+1}/{len(configs)})",
                    "#4CAF50"
                )
                
                self.log.emit("\n" + "─"*60, "info")
                self.log.emit(f"📊 شیت {idx+1}/{len(configs)}: {config.name}", "info")
                self.log.emit(f"🔗 URL: {config.sheet_url[:50]}...", "info")
                self.log.emit(f"📄 Worksheet: {config.worksheet_name}", "info")
                self.log.emit("─"*60, "info")
                
                try:
                    # استخراج با callback برای گزارش پیشرفت
                    def progress_callback(current, total, message):
                        self.sub_progress.emit(current, total, message)
                        if current % 100 == 0 or current == total:
                            self.log.emit(f"  📥 استخراج: {current:,}/{total:,} - {message}", "info")
                    
                    success, message, stats = self.extractor.extract_and_save(
                        config.id, 
                        auto_update=False,
                        progress_callback=progress_callback
                    )
                    
                    if success:
                        new = stats.get('new_records', 0)
                        updated = stats.get('updated_records', 0)
                        extracted = stats.get('total_extracted', 0)
                        
                        total_new += new
                        total_updated += updated
                        total_extracted_rows += extracted
                        
                        # گزارش تکراری‌ها
                        duplicates = stats.get('duplicates', [])
                        if duplicates:
                            all_duplicates.extend(duplicates)
                            self.log.emit(f"  ⚠️ {len(duplicates)} ردیف تکراری شناسایی شد", "warning")
                        
                        # گزارش علامت‌گذاری
                        mark_stats = stats.get('mark_stats', {})
                        if mark_stats:
                            marked = mark_stats.get('success', 0)
                            failed_mark = mark_stats.get('failed', 0)
                            if failed_mark > 0:
                                self.log.emit(f"  ⚠️ علامت‌گذاری: {marked:,} موفق، {failed_mark:,} ناموفق", "warning")
                            else:
                                self.log.emit(f"  ✅ علامت‌گذاری: {marked:,} ردیف", "success")
                        
                        self.log.emit(
                            f"  ✅ نتیجه: {new:,} رکورد جدید، {updated:,} بروزرسانی، "
                            f"{extracted:,} ردیف استخراج شد",
                            "success"
                        )
                    else:
                        total_errors += 1
                        self.log.emit(f"  ❌ خطا: {message}", "error")
                
                except Exception as e:
                    total_errors += 1
                    self.log.emit(f"  ❌ خطای غیرمنتظره: {str(e)}", "error")
                    self.logger.error(f"خطا در استخراج از {config.name}: {str(e)}")
                    import traceback
                    self.log.emit(f"  🔍 جزئیات: {traceback.format_exc()}", "error")
            
            # محاسبه زمان
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # خلاصه نهایی
            self.progress.emit(100, "✅ تمام شد!", "#4CAF50")
            
            self.log.emit("\n" + "="*60, "info")
            self.log.emit("🎯 خلاصه نتایج نهایی", "info")
            self.log.emit("="*60, "info")
            self.log.emit(f"⏱️  مدت زمان: {duration:.1f} ثانیه ({duration/60:.1f} دقیقه)", "info")
            self.log.emit(f"📁 شیت‌های پردازش شده: {len(configs)}", "info")
            self.log.emit(f"📥 ردیف‌های استخراج شده: {total_extracted_rows:,}", "success" if total_extracted_rows > 0 else "warning")
            self.log.emit(f"➕ رکوردهای جدید: {total_new:,}", "success" if total_new > 0 else "info")
            self.log.emit(f"🔄 رکوردهای بروز شده: {total_updated:,}", "info")
            self.log.emit(f"⚠️  تکراری‌ها (نیاز به بررسی): {len(all_duplicates):,}", "warning" if len(all_duplicates) > 0 else "info")
            self.log.emit(f"❌ خطاها: {total_errors}", "error" if total_errors > 0 else "success")
            
            # محاسبه سرعت
            if duration > 0:
                speed = total_extracted_rows / duration
                self.log.emit(f"⚡ سرعت استخراج: {speed:.1f} ردیف/ثانیه", "info")
            
            self.log.emit("="*60, "info")
            self.log.emit(f"🕐 زمان پایان: {end_time.strftime('%Y/%m/%d - %H:%M:%S')}", "info")
            self.log.emit("="*60, "info")
            
            # ثبت در دیتابیس
            summary = {
                'total_configs': len(configs),
                'new_records': total_new,
                'updated_records': total_updated,
                'total_extracted': total_extracted_rows,
                'errors': total_errors,
                'duplicates': all_duplicates,
                'duration_seconds': duration
            }
            
            self._save_process_log(configs, summary, start_time, end_time)
            
            # پیام نهایی
            if total_errors == 0 and total_new + total_updated > 0:
                final_msg = f"✅ استخراج موفق: {total_new:,} جدید، {total_updated:,} بروز شد"
                self.finished.emit(True, final_msg, summary)
            elif total_errors > 0:
                final_msg = f"⚠️ استخراج با خطا: {total_errors} خطا، {total_new:,} جدید"
                self.finished.emit(False, final_msg, summary)
            else:
                final_msg = "⚠️ هیچ رکورد جدیدی یافت نشد"
                self.finished.emit(True, final_msg, summary)
                
        except Exception as e:
            self.log.emit(f"\n❌❌❌ خطای کلی: {str(e)}", "error")
            self.logger.error(f"خطای کلی در thread استخراج: {str(e)}")
            import traceback
            self.log.emit(f"🔍 Traceback:\n{traceback.format_exc()}", "error")
            self.finished.emit(False, f"خطای کلی: {str(e)}", {})
    
    def _save_process_log(self, configs, summary, start_time, end_time):
        """ذخیره لاگ عملیات در دیتابیس"""
        try:
            db = db_manager.get_session()
            
            # تعیین وضعیت
            if summary['errors'] == 0 and summary['new_records'] + summary['updated_records'] > 0:
                status = "SUCCESS"
            elif summary['errors'] > 0 and summary['new_records'] + summary['updated_records'] > 0:
                status = "PARTIAL"
            elif summary['errors'] > 0:
                status = "ERROR"
            else:
                status = "WARNING"
            
            # ساخت پیام
            message = f"استخراج از {len(configs)} شیت: {summary['new_records']:,} جدید، {summary['updated_records']:,} بروز شد"
            if len(summary['duplicates']) > 0:
                message += f", {len(summary['duplicates'])} تکراری"
            if summary['errors'] > 0:
                message += f", {summary['errors']} خطا"
            
            process_log = ProcessLog(
                process_type="EXTRACTION",
                status=status,
                message=message,
                started_at=start_time,
                completed_at=end_time,
                details=summary
            )
            db.add(process_log)
            db.commit()
            log_id = process_log.id
            db.close()
            
            self.log.emit(f"✅ لاگ عملیات در دیتابیس ثبت شد (ID: {log_id})", "success")
        except Exception as e:
            self.log.emit(f"⚠️ خطا در ثبت لاگ: {str(e)}", "warning")
    
    def run(self):
        """اجرای استخراج"""
        try:
            self.progress.emit(10, "دریافت لیست شیت‌ها...", "#2196F3")
            self.log.emit("🔍 دریافت لیست شیت‌های انتخابی...")
            
            # دریافت شیت‌های فعال
            all_configs = db_manager.get_all_sheet_configs(active_only=True)
            
            if not all_configs:
                self.finished.emit(False, "هیچ شیت فعالی یافت نشد!", {})
                return
            
            # فیلتر کردن بر اساس انتخاب کاربر
            if self.selected_sheet_ids:
                configs = [c for c in all_configs if c.id in self.selected_sheet_ids]
                if not configs:
                    self.finished.emit(False, "هیچ شیتی انتخاب نشده است!", {})
                    return
                self.log.emit(f"✅ تعداد {len(configs)} شیت انتخاب شده از {len(all_configs)} شیت فعال")
            else:
                configs = all_configs
                self.log.emit(f"✅ استخراج از همه شیت‌های فعال ({len(configs)} شیت)")
            
            total_new = 0
            total_updated = 0
            total_errors = 0
            all_duplicates = []  # تمام تکراری‌ها از همه شیت‌ها
            
            # استخراج از هر شیت
            for idx, config in enumerate(configs):
                progress_pct = 10 + int((idx / len(configs)) * 80)
                self.progress.emit(
                    progress_pct,
                    f"استخراج از '{config.name}'...",
                    "#4CAF50"
                )
                self.log.emit(f"\n📊 شروع استخراج از '{config.name}'...")
                
                try:
                    # استخراج (بدون بروزرسانی خودکار)
                    success, message, stats = self.extractor.extract_and_save(config.id, auto_update=False)
                    
                    if success:
                        total_new += stats.get('new_records', 0)
                        total_updated += stats.get('updated_records', 0)
                        
                        # جمع‌آوری تکراری‌ها
                        duplicates = stats.get('duplicates', [])
                        if duplicates:
                            all_duplicates.extend(duplicates)
                            self.log.emit(f"  ⚠️ {len(duplicates)} ردیف تکراری شناسایی شد")
                        
                        self.log.emit(
                            f"  ✅ موفق: {stats.get('new_records', 0)} جدید، "
                            f"{stats.get('updated_records', 0)} بروز شد"
                        )
                    else:
                        total_errors += 1
                        self.log.emit(f"  ❌ خطا: {message}")
                
                except Exception as e:
                    total_errors += 1
                    self.log.emit(f"  ❌ خطا: {str(e)}")
                    self.logger.error(f"خطا در استخراج از {config.name}: {str(e)}")
            
            # خلاصه نتایج
            self.progress.emit(100, "تمام شد!", "#4CAF50")
            
            summary = {
                'total_configs': len(configs),
                'new_records': total_new,
                'updated_records': total_updated,
                'errors': total_errors,
                'duplicates': all_duplicates  # لیست کامل تکراری‌ها
            }
            
            self.log.emit("\n" + "="*50)
            self.log.emit("📋 خلاصه نتایج:")
            self.log.emit(f"  • شیت‌های پردازش شده: {len(configs)}")
            self.log.emit(f"  • رکوردهای جدید: {total_new:,}")
            self.log.emit(f"  • رکوردهای بروز شده: {total_updated:,}")
            self.log.emit(f"  • تکراری‌ها (نیاز به بررسی): {len(all_duplicates):,}")
            self.log.emit(f"  • خطاها: {total_errors}")
            self.log.emit("="*50)
            
            # ثبت لاگ عملیات
            try:
                from datetime import datetime
                db = db_manager.get_session()
                
                status = "SUCCESS" if (total_new > 0 or total_updated > 0) and total_errors == 0 else "PARTIAL" if total_errors > 0 else "WARNING"
                message = f"استخراج از {len(configs)} شیت: {total_new} جدید، {total_updated} بروز شد"
                if len(all_duplicates) > 0:
                    message += f", {len(all_duplicates)} تکراری"
                if total_errors > 0:
                    message += f", {total_errors} خطا"
                
                process_log = ProcessLog(
                    process_type="EXTRACTION",
                    status=status,
                    message=message,
                    started_at=datetime.now(),
                    completed_at=datetime.now(),
                    details={
                        'total_configs': len(configs),
                        'new_records': total_new,
                        'updated_records': total_updated,
                        'duplicates': len(all_duplicates),
                        'errors': total_errors
                    }
                )
                db.add(process_log)
                db.commit()
                db.close()
                self.log.emit(f"✅ لاگ عملیات ثبت شد (ID: {process_log.id})")
            except Exception as log_error:
                self.log.emit(f"⚠️ خطا در ثبت لاگ: {log_error}")
            
            if total_new > 0 or total_updated > 0 or all_duplicates:
                msg = f"✅ استخراج موفق!\n{total_new:,} رکورد جدید، {total_updated:,} بروز شد"
                if all_duplicates:
                    msg += f"\n⚠️ {len(all_duplicates)} ردیف تکراری نیاز به بررسی دارد"
                self.finished.emit(True, msg, summary)
            else:
                self.finished.emit(
                    False,
                    "⚠️ هیچ رکورد جدیدی یافت نشد!",
                    summary
                )
        
        except Exception as e:
            self.logger.error(f"خطای بحرانی در استخراج: {str(e)}")
            self.finished.emit(False, f"❌ خطا: {str(e)}", {})


class ExtractionWidget(QWidget):
    """ویجت استخراج داده"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = app_logger
        self.extraction_thread = None
        self.parent_window = parent
        self.init_ui()
    
    def showEvent(self, event):
        """هنگام نمایش widget، لیست را refresh کن"""
        super().showEvent(event)
        self.refresh_data()
    
    def refresh_data(self):
        """بروزرسانی آمار و لیست شیت‌ها"""
        self.load_stats()
        self.load_sheets_list()
    
    def init_ui(self):
        """راه‌اندازی رابط کاربری"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # هدر: عنوان + آمار در یک خط افقی - بدون فضای اضافی
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)
        
        # عنوان
        title = QLabel("📥 استخراج داده از Google Sheets")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet("color: #2196F3;")
        header_layout.addWidget(title)
        
        # جداکننده عمودی
        separator = QLabel("│")
        separator.setFont(QFont("Segoe UI", 14))
        separator.setStyleSheet("color: #90caf9;")
        header_layout.addWidget(separator)
        
        # آمار در یک خط - جذاب و رنگی
        self.stats_label = QLabel("⏳ در حال بارگذاری آمار...")
        self.stats_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.stats_label.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e3f2fd, stop:1 #bbdefb);
                padding: 10px 20px;
                border-radius: 6px;
                color: #1565c0;
                border: 2px solid #90caf9;
            }
        """)
        header_layout.addWidget(self.stats_label, 1)  # stretch factor = 1
        
        layout.addLayout(header_layout)
        
        # انتخاب شیت‌ها - Grid 3 ستونی با checkbox های بزرگ‌تر
        sheets_group = QGroupBox("📋 انتخاب شیت‌ها برای استخراج")
        sheets_group.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        sheets_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #fafafa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                color: #333;
            }
        """)
        sheets_layout = QVBoxLayout()
        sheets_layout.setContentsMargins(12, 12, 12, 12)
        sheets_layout.setSpacing(8)
        
        # دکمه‌های انتخاب سریع
        quick_select_layout = QHBoxLayout()
        quick_select_layout.setSpacing(8)
        
        select_all_btn = QPushButton("✓ انتخاب همه")
        select_all_btn.setFixedHeight(32)
        select_all_btn.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        select_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 6px 15px;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:pressed { background-color: #388E3C; }
        """)
        select_all_btn.clicked.connect(self.select_all_sheets)
        quick_select_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("✗ لغو همه")
        deselect_all_btn.setFixedHeight(32)
        deselect_all_btn.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        deselect_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 6px 15px;
            }
            QPushButton:hover { background-color: #616161; }
            QPushButton:pressed { background-color: #424242; }
        """)
        deselect_all_btn.clicked.connect(self.deselect_all_sheets)
        quick_select_layout.addWidget(deselect_all_btn)
        quick_select_layout.addStretch()
        
        sheets_layout.addLayout(quick_select_layout)
        
        # Scroll Area با Grid 3 ستونی
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 6px;
                background-color: white;
            }
        """)
        
        scroll_container = QWidget()
        self.sheets_grid = QGridLayout(scroll_container)
        self.sheets_grid.setSpacing(8)
        self.sheets_grid.setContentsMargins(10, 10, 10, 10)
        
        scroll_area.setWidget(scroll_container)
        scroll_area.setMinimumHeight(120)
        sheets_layout.addWidget(scroll_area)
        
        self.sheet_checkboxes = {}
        
        sheets_group.setLayout(sheets_layout)
        layout.addWidget(sheets_group, 3)  # بیشترین stretch
        
        # دکمه شروع + پیشرفت در یک ردیف
        action_layout = QHBoxLayout()
        action_layout.setSpacing(8)
        
        self.start_btn = QPushButton("▶️ شروع استخراج")
        self.start_btn.setFixedHeight(36)
        self.start_btn.setMinimumWidth(120)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 10pt;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:pressed { background-color: #388E3C; }
            QPushButton:disabled {
                background-color: #BDBDBD;
                color: #757575;
            }
        """)
        self.start_btn.clicked.connect(self.start_extraction)
        action_layout.addWidget(self.start_btn)
        
        # پیشرفت با نوار بزرگ‌تر و فونت درشت‌تر
        progress_container = QVBoxLayout()
        progress_container.setSpacing(4)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(24)  # نوار بزرگ‌تر
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ddd;
                border-radius: 6px;
                text-align: center;
                font-size: 10pt;
                font-weight: bold;
                background-color: #f5f5f5;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:1 #66BB6A);
                border-radius: 4px;
            }
        """)
        progress_container.addWidget(self.progress_bar)
        
        self.status_label = QLabel("آماده")
        self.status_label.setStyleSheet("font-size: 9pt; color: #666; font-weight: bold;")
        progress_container.addWidget(self.status_label)
        
        action_layout.addLayout(progress_container, 1)
        layout.addLayout(action_layout)
        
        # لاگ - مینیمال
        log_group = QGroupBox("📝 لاگ عملیات")
        log_group.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        log_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #fafafa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                color: #333;
            }
        """)
        log_layout = QVBoxLayout()
        log_layout.setContentsMargins(12, 12, 12, 12)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(80)
        self.log_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)  # Word wrap
        self.log_text.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # بدون اسکرول افقی
        self.log_text.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)  # فقط عمودی
        self.log_text.setStyleSheet("""
            QTextEdit {
                background: #263238;
                color: #00ff00;
                font-family: 'Consolas', monospace;
                font-size: 9pt;
                border: 2px solid #37474F;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group, 1)  # کمترین stretch
        
        # بارگذاری آمار و شیت‌ها
        self.load_stats()
        self.load_sheets_list()
    
    def load_sheets_list(self):
        """بارگذاری Grid شیت‌ها با Checkboxes - همیشه 3 ستونی"""
        try:
            # پاک کردن Grid قبلی
            for i in reversed(range(self.sheets_grid.count())):
                widget = self.sheets_grid.itemAt(i).widget()
                if widget:
                    widget.deleteLater()
            
            self.sheet_checkboxes.clear()
            
            configs = db_manager.get_all_sheet_configs(active_only=True)
            
            if not configs:
                label = QLabel("⚠️ هیچ شیت فعالی یافت نشد")
                label.setStyleSheet("color: #999; font-size: 10pt; padding: 20px;")
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.sheets_grid.addWidget(label, 0, 0, 1, 3)
                return
            
            # همیشه 3 ستون (مطابق درخواست کاربر)
            num_columns = 3
            
            # افزودن Checkboxes به Grid با فونت بزرگ‌تر
            for idx, config in enumerate(configs):
                row = idx // num_columns
                col = idx % num_columns
                
                checkbox = QCheckBox(f"📊 {config.name}")
                checkbox.setStyleSheet("""
                    QCheckBox {
                        font-size: 10pt;
                        padding: 5px 8px;
                        background-color: #f9f9f9;
                        border: 1px solid #e0e0e0;
                        border-radius: 4px;
                    }
                    QCheckBox:hover {
                        background-color: #E8F5E9;
                        border: 1px solid #A5D6A7;
                    }
                    QCheckBox::indicator {
                        width: 16px;
                        height: 16px;
                        border: 1px solid #bbb;
                        border-radius: 2px;
                        background-color: white;
                    }
                    QCheckBox::indicator:hover {
                        border: 1px solid #4CAF50;
                    }
                    QCheckBox::indicator:checked {
                        background-color: #4CAF50;
                        border: 1px solid #388E3C;
                    }
                """)
                checkbox.setChecked(True)
                
                self.sheet_checkboxes[config.id] = checkbox
                self.sheets_grid.addWidget(checkbox, row, col)
            
            # اضافه کردن spacer در انتها برای چیدمان بهتر
            self.sheets_grid.setRowStretch(len(configs) // num_columns + 1, 1)
            
        except Exception as e:
            self.logger.error(f"خطا در بارگذاری لیست شیت‌ها: {e}")
    
    def select_all_sheets(self):
        """انتخاب همه Checkboxها"""
        for checkbox in self.sheet_checkboxes.values():
            checkbox.setChecked(True)
    
    def deselect_all_sheets(self):
        """لغو انتخاب همه Checkboxها"""
        for checkbox in self.sheet_checkboxes.values():
            checkbox.setChecked(False)
    
    def get_selected_sheet_ids(self):
        """دریافت ID های شیت‌های انتخاب شده"""
        selected_ids = []
        for sheet_id, checkbox in self.sheet_checkboxes.items():
            if checkbox.isChecked():
                selected_ids.append(sheet_id)
        return selected_ids
    
    def load_stats(self):
        """بارگذاری آمار - در یک خط افقی با فاصله مناسب"""
        try:
            stats = db_manager.get_statistics()
            configs = db_manager.get_all_sheet_configs(active_only=True)
            
            # آمار در یک خط افقی با فاصله بیشتر بین آیتم‌ها
            self.stats_label.setText(
                f"📋 شیت‌های فعال: {len(configs)}    •    "
                f"📦 کل رکوردها: {stats.get('total_records', 0):,}    •    "
                f"✅ خروجی گرفته شده: {stats.get('exported_records', 0):,}    •    "
                f"⏳ در انتظار: {stats.get('pending_records', 0):,}"
            )
        except Exception as e:
            self.stats_label.setText(f"❌ خطا در بارگذاری آمار: {str(e)}")
    
    def start_extraction(self):
        """شروع استخراج"""
        # بررسی شیت‌های فعال
        configs = db_manager.get_all_sheet_configs(active_only=True)
        
        if not configs:
            QMessageBox.warning(
                self,
                "هشدار",
                "⚠️ هیچ شیت فعالی برای استخراج یافت نشد!\n\n"
                "لطفاً ابتدا از تب 'مدیریت شیت‌ها' حداقل یک شیت اضافه کنید."
            )
            return
        
        # دریافت شیت‌های انتخابی
        selected_sheet_ids = self.get_selected_sheet_ids()
        
        if not selected_sheet_ids:
            QMessageBox.warning(
                self,
                "هشدار",
                "⚠️ هیچ شیتی انتخاب نشده است!\n\n"
                "لطفاً حداقل یک شیت را انتخاب کنید."
            )
            return
        
        # تایید
        selected_count = len(selected_sheet_ids)
        total_count = len(configs)
        
        if selected_count == total_count:
            confirm_msg = f"آیا می‌خواهید استخراج از همه شیت‌ها ({total_count} شیت) را شروع کنید؟"
        else:
            confirm_msg = f"آیا می‌خواهید استخراج از {selected_count} شیت انتخابی (از {total_count} شیت) را شروع کنید؟"
        
        reply = QMessageBox.question(
            self,
            "تایید",
            confirm_msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # غیرفعال کردن دکمه
        self.start_btn.setEnabled(False)
        self.start_btn.setText("⏳ در حال استخراج...")
        
        # پاک کردن لاگ
        self.log_text.clear()
        self.progress_bar.setValue(0)
        
        # ایجاد thread با شیت‌های انتخابی
        self.extraction_thread = ExtractionThread(selected_sheet_ids=selected_sheet_ids)
        
        # اتصال سیگنال‌ها
        self.extraction_thread.progress.connect(self.on_progress)
        self.extraction_thread.log.connect(self.on_log)
        self.extraction_thread.sub_progress.connect(self.on_sub_progress)
        self.extraction_thread.finished.connect(self.on_finished)
        
        # شروع
        self.extraction_thread.start()
    
    def on_progress(self, value, message, color):
        """بروزرسانی پیشرفت اصلی"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"font-size: 11pt; font-weight: bold; color: {color};")
    
    def on_sub_progress(self, current, total, message):
        """بروزرسانی پیشرفت جزئی (برای نمایش در status)"""
        if total > 0:
            percentage = int((current / total) * 100)
            self.status_label.setText(f"{message} ({current:,}/{total:,} - {percentage}%)")
    
    def on_log(self, message, level="info"):
        """
        افزودن لاگ با رنگ‌بندی بر اساس سطح
        
        Args:
            message: متن پیام
            level: سطح (info, success, warning, error)
        """
        # تعیین رنگ بر اساس سطح
        colors = {
            'info': '#00E5FF',      # آبی روشن
            'success': '#00FF41',   # سبز روشن
            'warning': '#FFC107',   # نارنجی/زرد
            'error': '#FF1744',     # قرمز
        }
        
        color = colors.get(level, '#00E5FF')
        
        # افزودن HTML با رنگ
        html = f'<span style="color: {color}; font-family: Tahoma, Consolas; font-size: 9pt;">{message}</span>'
        self.log_text.append(html)
        
        # اسکرول به انتها
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
    def on_finished(self, success, message, summary):
        """پایان استخراج"""
        # فعال کردن دکمه
        self.start_btn.setEnabled(True)
        self.start_btn.setText("▶️ شروع استخراج")
        
        # بروزرسانی آمار
        self.load_stats()
        
        # بررسی تکراری‌ها
        if success and summary and 'duplicates' in summary:
            duplicates = summary.get('duplicates', [])
            
            if duplicates:
                # نمایش پیام هشدار
                from app.gui.dialogs.duplicate_conflict_dialog import DuplicateConflictDialog
                
                reply = QMessageBox.warning(
                    self,
                    "⚠️ تشخیص داده‌های تکراری",
                    f"تعداد {len(duplicates)} ردیف تکراری شناسایی شد!\n\n"
                    f"این ردیف‌ها قبلاً استخراج شده‌اند و در Google Sheet ویرایش شده‌اند.\n"
                    f"آیا می‌خواهید آن‌ها را بررسی کنید؟",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    # نمایش Dialog برای هر تکراری
                    self.handle_duplicates(duplicates)
        
        # نمایش پیام نهایی
        if success:
            QMessageBox.information(self, "موفق", message)
        else:
            QMessageBox.warning(self, "هشدار", message)
    
    def handle_duplicates(self, duplicates: list):
        """مدیریت تکراری‌ها"""
        from app.gui.dialogs.duplicate_conflict_dialog import DuplicateConflictDialog
        
        updated_count = 0
        skipped_count = 0
        
        for dup in duplicates:
            # نمایش Dialog
            dialog = DuplicateConflictDialog(
                existing_data=dup['existing_data'],
                new_data=dup['new_data'],
                row_number=dup['row_number'],
                parent=self
            )
            
            result = dialog.exec()
            
            if result == dialog.DialogCode.Accepted:
                choice = dialog.get_user_choice()
                
                if choice == 'update':
                    # بروزرسانی در دیتابیس
                    success, saved_data, is_new, message = db_manager.save_sales_data(
                        sheet_config_id=dup['sheet_config_id'],
                        row_number=dup['row_number'],
                        unique_key=dup['unique_key'],
                        data=dup['new_data'],
                        update_if_exists=True
                    )
                    
                    if success:
                        updated_count += 1
                        self.log_text.append(f"  ✅ ردیف {dup['row_number']} بروزرسانی شد")
                        
                        # علامت‌گذاری در Google Sheet
                        try:
                            from app.core.google_sheets import GoogleSheetExtractor
                            extractor = GoogleSheetExtractor()
                            extractor.mark_as_extracted(
                                sheet_url=dup['sheet_url'],
                                worksheet_name=dup['worksheet_name'] or 'Sheet1',
                                row_number=dup['row_number'],
                                extracted_column=dup['extracted_column']
                            )
                        except Exception as e:
                            self.log_text.append(f"    ⚠️ خطا در علامت‌گذاری: {str(e)}")
                    else:
                        self.log_text.append(f"  ❌ خطا در بروزرسانی ردیف {dup['row_number']}: {message}")
                
                elif choice == 'skip':
                    skipped_count += 1
                    self.log_text.append(f"  ⏭️ ردیف {dup['row_number']} نادیده گرفته شد")
            else:
                # لغو شد
                skipped_count += 1
        
        # خلاصه نهایی
        self.log_text.append("\n" + "="*50)
        self.log_text.append(f"📋 خلاصه مدیریت تکراری‌ها:")
        self.log_text.append(f"  • بروزرسانی شده: {updated_count}")
        self.log_text.append(f"  • نادیده گرفته شده: {skipped_count}")
        self.log_text.append("="*50)
        
        # بروزرسانی آمار
        self.load_stats()

