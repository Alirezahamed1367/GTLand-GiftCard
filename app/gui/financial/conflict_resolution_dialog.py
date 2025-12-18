"""
Conflict Resolution Dialog - مدیریت تداخل‌ها (DEPRECATED)
==========================================
⚠️ این دیالوگ با سیستم قدیمی RawData کار می‌کند
⚠️ باید با RawData جدید (dynamic_models) بازنویسی شود

فعلاً غیرفعال شده است.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton
)


class ConflictDetailDialog(QDialog):
    """دیالوگ نمایش جزئیات یک تداخل - DEPRECATED"""
    
    def __init__(self, parent=None, raw_data=None):
        super().__init__(parent)
        self.setWindowTitle("⚠️ غیرفعال")
        self.setModal(True)
        self.resize(400, 200)
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel(
            "⚠️ این بخش با سیستم قدیمی کار می‌کند.\n\n"
            "باید با RawData جدید بازنویسی شود.\n\n"
            "فعلاً از این قسمت استفاده نکنید."
        ))
        
        close_btn = QPushButton("بستن")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)


class ConflictResolutionDialog(QDialog):
    """دیالوگ مدیریت تداخل‌ها - DEPRECATED"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚠️ مدیریت تداخل‌ها - غیرفعال")
        self.setModal(True)
        self.resize(600, 300)
        
        layout = QVBoxLayout()
        
        warning = QLabel(
            "⚠️ این بخش با سیستم قدیمی RawData کار می‌کند.\n\n"
            "RawData جدید (در dynamic_models.py) فیلدهای زیر را ندارد:\n"
            "• has_conflict\n"
            "• conflict_type\n"
            "• conflict_resolved\n"
            "• change_detected_at\n\n"
            "این بخش باید با ساختار جدید بازنویسی شود.\n"
            "فعلاً از Smart Import Wizard برای Import استفاده کنید."
        )
        warning.setWordWrap(True)
        warning.setStyleSheet("""
            background: #fff3cd;
            padding: 20px;
            border: 2px solid #ffc107;
            border-radius: 10px;
            font-size: 11pt;
            color: #856404;
        """)
        layout.addWidget(warning)
        
        close_btn = QPushButton("❌ بستن")
        close_btn.clicked.connect(self.accept)
        close_btn.setMinimumHeight(40)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
