"""
پنجره لاگ زنده برای نمایش جزئیات کامل عملیات استخراج
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QPushButton, QLabel, QProgressBar, QFrame
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont, QTextCursor, QIcon
from datetime import datetime


class LiveLogDialog(QDialog):
    """
    پنجره لاگ زنده با قابلیت:
    - نمایش لحظه‌ای تمام لاگ‌ها
    - رنگ‌بندی بر اساس سطح
    - Auto-scroll
    - نوار پیشرفت
    - امکان توقف عملیات
    - ذخیره لاگ
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 لاگ زنده عملیات استخراج")
        self.setMinimumSize(1000, 700)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowMaximizeButtonHint)
        
        self.is_cancelled = False
        self.extraction_thread = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """راه‌اندازی رابط کاربری"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # ========== هدر ==========
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 10px;
                padding: 15px;
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setSpacing(8)
        
        title_label = QLabel("🚀 سیستم نظارت زنده عملیات")
        title_label.setFont(QFont("Tahoma", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)
        
        self.time_label = QLabel(f"⏰ شروع: {datetime.now().strftime('%Y/%m/%d - %H:%M:%S')}")
        self.time_label.setFont(QFont("Tahoma", 10))
        self.time_label.setStyleSheet("color: #f0f0f0;")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.time_label)
        
        layout.addWidget(header_frame)
        
        # ========== نوار وضعیت ==========
        status_frame = QFrame()
        status_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        status_layout = QVBoxLayout(status_frame)
        status_layout.setSpacing(8)
        
        # وضعیت فعلی
        self.status_label = QLabel("⏳ در حال آماده‌سازی...")
        self.status_label.setFont(QFont("Tahoma", 11, QFont.Weight.Bold))
        self.status_label.setStyleSheet("color: #2196F3;")
        status_layout.addWidget(self.status_label)
        
        # نوار پیشرفت اصلی
        progress_container = QHBoxLayout()
        progress_container.setSpacing(10)
        
        self.main_progress_bar = QProgressBar()
        self.main_progress_bar.setMinimum(0)
        self.main_progress_bar.setMaximum(100)
        self.main_progress_bar.setValue(0)
        self.main_progress_bar.setTextVisible(True)
        self.main_progress_bar.setFormat("پیشرفت کلی: %p%")
        self.main_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #2196F3;
                border-radius: 8px;
                text-align: center;
                font-size: 11pt;
                font-weight: bold;
                font-family: 'Tahoma';
                background-color: white;
                height: 30px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 6px;
            }
        """)
        progress_container.addWidget(self.main_progress_bar)
        
        self.progress_label = QLabel("0%")
        self.progress_label.setFont(QFont("Tahoma", 12, QFont.Weight.Bold))
        self.progress_label.setStyleSheet("color: #667eea; min-width: 50px;")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_container.addWidget(self.progress_label)
        
        status_layout.addLayout(progress_container)
        
        # نوار پیشرفت جزئی
        self.sub_progress_label = QLabel("")
        self.sub_progress_label.setFont(QFont("Tahoma", 9))
        self.sub_progress_label.setStyleSheet("color: #666;")
        status_layout.addWidget(self.sub_progress_label)
        
        layout.addWidget(status_frame)
        
        # ========== آمار لحظه‌ای ==========
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setSpacing(15)
        
        # شیت‌های پردازش شده
        self.sheets_stat = self._create_stat_widget("📁", "شیت‌ها", "0/0", "#2196F3")
        stats_layout.addWidget(self.sheets_stat)
        
        # رکوردهای جدید
        self.new_stat = self._create_stat_widget("➕", "جدید", "0", "#4CAF50")
        stats_layout.addWidget(self.new_stat)
        
        # بروزرسانی
        self.updated_stat = self._create_stat_widget("🔄", "بروز شده", "0", "#2196F3")
        stats_layout.addWidget(self.updated_stat)
        
        # تکراری
        self.duplicate_stat = self._create_stat_widget("⚠️", "تکراری", "0", "#FFC107")
        stats_layout.addWidget(self.duplicate_stat)
        
        # خطا
        self.error_stat = self._create_stat_widget("❌", "خطا", "0", "#F44336")
        stats_layout.addWidget(self.error_stat)
        
        layout.addWidget(stats_frame)
        
        # ========== ناحیه لاگ ==========
        log_label = QLabel("📝 لاگ جزئیات عملیات:")
        log_label.setFont(QFont("Tahoma", 10, QFont.Weight.Bold))
        layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 2px solid #3c3c3c;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Consolas', 'Courier New', monospace;
                line-height: 1.4;
            }
            QScrollBar:vertical {
                background: #2d2d2d;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #667eea;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: #764ba2;
            }
        """)
        layout.addWidget(self.log_text, 1)  # بیشترین فضا
        
        # ========== دکمه‌ها ==========
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        # دکمه توقف
        self.stop_btn = QPushButton("⏸️ توقف عملیات")
        self.stop_btn.setFont(QFont("Tahoma", 10, QFont.Weight.Bold))
        self.stop_btn.setMinimumHeight(40)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_extraction)
        buttons_layout.addWidget(self.stop_btn)
        
        buttons_layout.addStretch()
        
        # دکمه ذخیره لاگ
        save_btn = QPushButton("💾 ذخیره لاگ")
        save_btn.setFont(QFont("Tahoma", 10))
        save_btn.setMinimumHeight(40)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        save_btn.clicked.connect(self.save_log)
        buttons_layout.addWidget(save_btn)
        
        # دکمه پاک کردن
        clear_btn = QPushButton("🗑️ پاک کردن")
        clear_btn.setFont(QFont("Tahoma", 10))
        clear_btn.setMinimumHeight(40)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        clear_btn.clicked.connect(self.log_text.clear)
        buttons_layout.addWidget(clear_btn)
        
        # دکمه بستن
        self.close_btn = QPushButton("✖️ بستن")
        self.close_btn.setFont(QFont("Tahoma", 10, QFont.Weight.Bold))
        self.close_btn.setMinimumHeight(40)
        self.close_btn.setEnabled(False)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
        """)
        self.close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(self.close_btn)
        
        layout.addLayout(buttons_layout)
        
        # ========== آمار اولیه ==========
        self.stats = {
            'sheets_processed': 0,
            'sheets_total': 0,
            'new_records': 0,
            'updated_records': 0,
            'duplicates': 0,
            'errors': 0
        }
    
    def _create_stat_widget(self, icon, label, value, color):
        """ایجاد ویجت آمار"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-left: 4px solid {color};
                border-radius: 6px;
                padding: 8px;
            }}
        """)
        
        layout = QVBoxLayout(frame)
        layout.setSpacing(4)
        layout.setContentsMargins(10, 8, 10, 8)
        
        # آیکون + عنوان
        header = QHBoxLayout()
        header.setSpacing(5)
        
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI Emoji", 14))
        header.addWidget(icon_label)
        
        title_label = QLabel(label)
        title_label.setFont(QFont("Tahoma", 9))
        title_label.setStyleSheet("color: #666;")
        header.addWidget(title_label)
        header.addStretch()
        
        layout.addLayout(header)
        
        # مقدار
        value_label = QLabel(value)
        value_label.setFont(QFont("Tahoma", 14, QFont.Weight.Bold))
        value_label.setStyleSheet(f"color: {color};")
        value_label.setObjectName("value")
        layout.addWidget(value_label)
        
        return frame
    
    def _update_stat_widget(self, widget, value):
        """بروزرسانی مقدار آمار"""
        value_label = widget.findChild(QLabel, "value")
        if value_label:
            value_label.setText(str(value))
    
    @pyqtSlot(int, str, str)
    def update_progress(self, value, message, color):
        """بروزرسانی نوار پیشرفت اصلی"""
        self.main_progress_bar.setValue(value)
        self.progress_label.setText(f"{value}%")
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold;")
    
    @pyqtSlot(int, int, str)
    def update_sub_progress(self, current, total, message):
        """بروزرسانی پیشرفت جزئی"""
        if total > 0:
            percentage = int((current / total) * 100)
            self.sub_progress_label.setText(f"🔄 {message}: {current:,} / {total:,} ({percentage}%)")
        else:
            self.sub_progress_label.setText("")
    
    @pyqtSlot(str, str)
    def append_log(self, message, level="info"):
        """
        افزودن لاگ با رنگ‌بندی
        
        Args:
            message: متن پیام
            level: سطح (info, success, warning, error)
        """
        # تعیین رنگ بر اساس سطح
        color_map = {
            'info': '#61AFEF',      # آبی روشن
            'success': '#98C379',   # سبز
            'warning': '#E5C07B',   # زرد
            'error': '#E06C75',     # قرمز
            'debug': '#C678DD'      # بنفش
        }
        
        color = color_map.get(level, '#d4d4d4')
        
        # اضافه کردن timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # افزودن به HTML
        html = f'<span style="color: #7c7c7c;">[{timestamp}]</span> <span style="color: {color};">{message}</span><br>'
        
        # افزودن به TextEdit
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)
        self.log_text.insertHtml(html)
        
        # Auto-scroll
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def update_stats(self, stats_dict):
        """بروزرسانی آمار"""
        self.stats.update(stats_dict)
        
        # بروزرسانی ویجت‌ها
        self._update_stat_widget(
            self.sheets_stat, 
            f"{self.stats['sheets_processed']}/{self.stats['sheets_total']}"
        )
        self._update_stat_widget(self.new_stat, f"{self.stats['new_records']:,}")
        self._update_stat_widget(self.updated_stat, f"{self.stats['updated_records']:,}")
        self._update_stat_widget(self.duplicate_stat, f"{self.stats['duplicates']:,}")
        self._update_stat_widget(self.error_stat, f"{self.stats['errors']}")
    
    def stop_extraction(self):
        """توقف عملیات"""
        self.is_cancelled = True
        if self.extraction_thread:
            self.extraction_thread.cancel()
        self.append_log("⚠️ درخواست توقف توسط کاربر...", "warning")
        self.stop_btn.setEnabled(False)
    
    def on_extraction_finished(self):
        """پایان عملیات"""
        self.stop_btn.setEnabled(False)
        self.close_btn.setEnabled(True)
        self.time_label.setText(
            f"⏰ پایان: {datetime.now().strftime('%Y/%m/%d - %H:%M:%S')}"
        )
    
    def save_log(self):
        """ذخیره لاگ در فایل"""
        from PyQt6.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "ذخیره لاگ",
            f"extraction_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                self.append_log(f"✅ لاگ در فایل ذخیره شد: {filename}", "success")
            except Exception as e:
                self.append_log(f"❌ خطا در ذخیره لاگ: {str(e)}", "error")
