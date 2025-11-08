"""
ویجت استخراج داده
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QMessageBox, QProgressBar, QTextEdit, QGroupBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from app.core.database import db_manager
from app.core.google_sheets import GoogleSheetExtractor
from app.core.logger import app_logger
from app.utils.ui_constants import (
    FONT_SIZE_SECTION, BUTTON_HEIGHT_LARGE, COLOR_PRIMARY, 
    COLOR_SUCCESS, get_button_style
)


class ExtractionThread(QThread):
    """Thread برای استخراج داده"""
    progress = pyqtSignal(int, str, str)  # (درصد, پیام, رنگ)
    log = pyqtSignal(str)
    finished = pyqtSignal(bool, str, dict)
    
    def __init__(self):
        super().__init__()
        self.logger = app_logger
        self.extractor = GoogleSheetExtractor()
    
    def run(self):
        """اجرای استخراج"""
        try:
            self.progress.emit(10, "دریافت لیست شیت‌ها...", "#2196F3")
            self.log.emit("🔍 دریافت لیست شیت‌های فعال...")
            
            # دریافت شیت‌های فعال
            configs = db_manager.get_all_sheet_configs(active_only=True)
            
            if not configs:
                self.finished.emit(False, "هیچ شیت فعالی یافت نشد!", {})
                return
            
            self.log.emit(f"✅ تعداد {len(configs)} شیت فعال یافت شد")
            
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
        self.init_ui()
    
    def init_ui(self):
        """راه‌اندازی رابط کاربری"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # عنوان
        title = QLabel("📥 استخراج داده از Google Sheets")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #2196F3;")
        layout.addWidget(title)
        
        # آمار
        stats_group = QGroupBox("📊 آمار فعلی")
        stats_layout = QVBoxLayout()
        
        self.stats_label = QLabel("در حال بارگذاری...")
        self.stats_label.setStyleSheet("""
            background: #e3f2fd;
            padding: 15px;
            border-radius: 5px;
            font-weight: bold;
            font-size: 11pt;
        """)
        stats_layout.addWidget(self.stats_label)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # دکمه شروع
        self.start_btn = QPushButton("▶️ شروع استخراج")
        self.start_btn.setMinimumHeight(BUTTON_HEIGHT_LARGE)
        self.start_btn.setStyleSheet(get_button_style(COLOR_SUCCESS, 14, BUTTON_HEIGHT_LARGE))
        self.start_btn.clicked.connect(self.start_extraction)
        layout.addWidget(self.start_btn)
        
        # نوار پیشرفت
        progress_group = QGroupBox("⏳ پیشرفت")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e0e0e0;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
                height: 30px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("آماده")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 11pt; font-weight: bold; color: #666;")
        progress_layout.addWidget(self.status_label)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # لاگ
        log_group = QGroupBox("📝 جزئیات")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background: #263238;
                color: #00ff00;
                font-family: 'Courier New';
                font-size: 9pt;
                border: 2px solid #37474F;
                border-radius: 5px;
            }
        """)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # بارگذاری آمار
        self.load_stats()
    
    def load_stats(self):
        """بارگذاری آمار"""
        try:
            stats = db_manager.get_statistics()
            configs = db_manager.get_all_sheet_configs(active_only=True)
            
            self.stats_label.setText(
                f"📋 شیت‌های فعال: {len(configs)}\n"
                f"📦 کل رکوردها: {stats.get('total_records', 0):,}\n"
                f"✅ خروجی گرفته شده: {stats.get('exported_records', 0):,}\n"
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
        
        # تایید
        reply = QMessageBox.question(
            self,
            "تایید",
            f"آیا می‌خواهید استخراج از {len(configs)} شیت را شروع کنید؟",
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
        
        # ایجاد thread
        self.extraction_thread = ExtractionThread()
        
        # اتصال سیگنال‌ها
        self.extraction_thread.progress.connect(self.on_progress)
        self.extraction_thread.log.connect(self.on_log)
        self.extraction_thread.finished.connect(self.on_finished)
        
        # شروع
        self.extraction_thread.start()
    
    def on_progress(self, value, message, color):
        """بروزرسانی پیشرفت"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"font-size: 11pt; font-weight: bold; color: {color};")
    
    def on_log(self, message):
        """افزودن لاگ"""
        self.log_text.append(message)
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

