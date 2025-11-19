"""
Stage 1: Raw Data Model - داده‌های خام از Google Sheets
=========================================================
Import بدون تغییر - فقط ذخیره‌سازی با Unique Key هوشمند
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, Index
from sqlalchemy import event
from datetime import datetime
import hashlib
import json

from .base_financial import FinancialBase


class RawData(FinancialBase):
    """
    داده‌های خام از Google Sheets (Stage 1)
    
    هر ردیف یک رکورد کامل است با:
    - Unique Key هوشمند (بدون row_number)
    - داده‌های کامل به صورت JSON
    - تاریخچه تغییرات
    """
    __tablename__ = 'raw_data'
    
    id = Column(Integer, primary_key=True)
    
    # شناسایی شیت
    sheet_name = Column(String(200), nullable=False, index=True, comment="نام شیت گوگل")
    sheet_id = Column(String(100), nullable=True, comment="ID شیت گوگل")
    sheet_url = Column(Text, nullable=True, comment="URL کامل شیت")
    
    # Unique Key (هش ترکیبی از فیلدهایی که کاربر تعیین کرده)
    unique_key = Column(String(64), nullable=False, unique=True, index=True, comment="""
        هش SHA256 از ترکیب فیلدهایی که used_in_unique_key=True دارند
        مثال: hash(CODE + TR_ID + Date + Customer + Rate)
    """)
    
    # فیلدهای استفاده شده در unique key (برای تشخیص تغییرات)
    unique_key_fields = Column(JSON, nullable=True, comment="""
        فیلدهایی که در unique key استفاده شدند:
        ["CODE", "TR_ID", "Sold_Date", "Customer", "Rate"]
    """)
    
    # داده‌های کامل (به صورت JSON)
    data = Column(JSON, nullable=False, comment="""
        تمام داده‌های ردیف به صورت JSON:
        {
            "CODE": "G250",
            "Value": "500",
            "TR_ID": "T12345",
            "Sold_Date": "2025-01-15",
            "Customer": "test",
            "Rate": "4.5",
            ...
        }
    """)
    
    # شماره ردیف اصلی در شیت (فقط برای مرجع - در unique key استفاده نمی‌شود)
    row_number = Column(Integer, nullable=True, comment="شماره ردیف در شیت (فقط مرجع)")
    
    # وضعیت Extracted (تیک سبز)
    is_extracted = Column(Boolean, default=False, comment="آیا تیک Extracted زده شده؟")
    
    # وضعیت پردازش
    is_processed = Column(Boolean, default=False, index=True, comment="آیا به Stage 2 پردازش شده؟")
    processed_at = Column(DateTime, nullable=True, comment="زمان پردازش")
    
    # تشخیص تغییرات
    data_hash = Column(String(64), nullable=True, comment="""
        هش کامل داده‌ها (برای تشخیص تغییرات)
        اگر data_hash تغییر کند = داده تغییر کرده
    """)
    
    previous_data = Column(JSON, nullable=True, comment="داده قبلی (برای مقایسه)")
    change_detected_at = Column(DateTime, nullable=True, comment="زمان تشخیص تغییر")
    change_reason = Column(String(100), nullable=True, comment="""
        دلیل تغییر: extracted_unchecked, data_changed, manual_update
    """)
    
    # Conflict Management
    has_conflict = Column(Boolean, default=False, index=True, comment="آیا تداخل دارد؟")
    conflict_type = Column(String(50), nullable=True, comment="""
        نوع تداخل: extracted_removed, duplicate_key, data_mismatch
    """)
    conflict_resolved = Column(Boolean, default=False, comment="آیا تداخل حل شده؟")
    conflict_resolution = Column(Text, nullable=True, comment="راه‌حل اعمال شده")
    
    # متادیتا
    import_batch_id = Column(String(50), nullable=True, index=True, comment="شناسه دسته import")
    import_source = Column(String(100), nullable=True, comment="منبع import: google_sheets, excel, api")
    
    # زمان‌ها
    created_at = Column(DateTime, default=datetime.now, index=True, comment="اولین import")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="آخرین بروزرسانی")
    last_seen_at = Column(DateTime, default=datetime.now, comment="آخرین باری که در شیت دیده شد")
    
    # نرم‌افزاری حذف شده
    is_deleted = Column(Boolean, default=False, index=True, comment="حذف نرم‌افزاری")
    deleted_at = Column(DateTime, nullable=True)
    deleted_reason = Column(String(200), nullable=True)
    
    def __repr__(self):
        return f"<RawData(id={self.id}, sheet='{self.sheet_name}', unique_key='{self.unique_key[:8]}...')>"
    
    @staticmethod
    def generate_unique_key(data_dict, unique_key_fields):
        """
        تولید Unique Key از داده‌ها
        
        Args:
            data_dict: دیکشنری داده‌ها
            unique_key_fields: لیست فیلدهایی که باید در کلید استفاده شوند
            
        Returns:
            str: هش SHA256 به صورت hex
        """
        if not unique_key_fields:
            # اگر کاربر فیلدی تعیین نکرده، از همه داده‌ها استفاده می‌کنیم
            unique_key_fields = sorted(data_dict.keys())
        
        # ترتیب مهم است - همیشه مرتب می‌کنیم
        values = []
        for field in sorted(unique_key_fields):
            value = data_dict.get(field, '')
            # تبدیل به رشته و نرمال‌سازی
            value_str = str(value).strip().lower()
            values.append(f"{field}:{value_str}")
        
        # ترکیب و هش
        combined = "|".join(values)
        hash_obj = hashlib.sha256(combined.encode('utf-8'))
        return hash_obj.hexdigest()
    
    @staticmethod
    def generate_data_hash(data_dict):
        """
        تولید هش کامل از تمام داده‌ها (برای تشخیص تغییرات)
        """
        # مرتب‌سازی کلیدها برای یکنواختی
        sorted_data = json.dumps(data_dict, sort_keys=True, ensure_ascii=False)
        hash_obj = hashlib.sha256(sorted_data.encode('utf-8'))
        return hash_obj.hexdigest()
    
    def detect_changes(self, new_data):
        """
        تشخیص تغییرات در داده
        
        Returns:
            tuple: (has_changed, changes_dict)
        """
        if not self.data:
            return False, {}
        
        old_data = self.data
        changes = {}
        
        # مقایسه فیلدها
        all_keys = set(old_data.keys()) | set(new_data.keys())
        for key in all_keys:
            old_value = old_data.get(key)
            new_value = new_data.get(key)
            
            if old_value != new_value:
                changes[key] = {
                    "old": old_value,
                    "new": new_value
                }
        
        has_changed = len(changes) > 0
        return has_changed, changes
    
    def to_dict(self, include_data=True):
        """تبدیل به دیکشنری"""
        result = {
            "id": self.id,
            "sheet_name": self.sheet_name,
            "sheet_id": self.sheet_id,
            "unique_key": self.unique_key,
            "row_number": self.row_number,
            "is_extracted": self.is_extracted,
            "is_processed": self.is_processed,
            "has_conflict": self.has_conflict,
            "conflict_type": self.conflict_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_data:
            result["data"] = self.data
        
        return result


# ایجاد Indexes برای جستجوی سریع
Index('idx_raw_data_sheet_processed', RawData.sheet_name, RawData.is_processed)
Index('idx_raw_data_batch', RawData.import_batch_id, RawData.created_at)
Index('idx_raw_data_conflicts', RawData.has_conflict, RawData.conflict_resolved)


@event.listens_for(RawData, 'before_insert')
def before_insert_raw_data(mapper, connection, target):
    """
    قبل از insert:
    - تولید unique_key اگر وجود ندارد
    - تولید data_hash
    """
    if target.data and not target.unique_key:
        target.unique_key = RawData.generate_unique_key(
            target.data, 
            target.unique_key_fields or []
        )
    
    if target.data and not target.data_hash:
        target.data_hash = RawData.generate_data_hash(target.data)


@event.listens_for(RawData, 'before_update')
def before_update_raw_data(mapper, connection, target):
    """
    قبل از update:
    - بررسی تغییرات
    - بروزرسانی data_hash
    """
    if target.data:
        new_hash = RawData.generate_data_hash(target.data)
        if new_hash != target.data_hash:
            # داده تغییر کرده
            target.previous_data = target.data
            target.data_hash = new_hash
            target.change_detected_at = datetime.now()
            
            if not target.change_reason:
                target.change_reason = 'data_changed'


class ImportBatch(FinancialBase):
    """
    اطلاعات هر دسته Import
    """
    __tablename__ = 'import_batches'
    
    id = Column(Integer, primary_key=True)
    batch_id = Column(String(50), nullable=False, unique=True, index=True)
    
    # مشخصات شیت
    sheet_name = Column(String(200), nullable=False)
    sheet_id = Column(String(100), nullable=True)
    sheet_url = Column(Text, nullable=True)
    
    # آمار
    total_rows = Column(Integer, default=0, comment="تعداد کل ردیف‌ها")
    new_rows = Column(Integer, default=0, comment="ردیف‌های جدید")
    updated_rows = Column(Integer, default=0, comment="ردیف‌های بروز شده")
    unchanged_rows = Column(Integer, default=0, comment="ردیف‌های بدون تغییر")
    error_rows = Column(Integer, default=0, comment="ردیف‌های خطا")
    
    # تنظیمات
    unique_key_fields = Column(JSON, nullable=True, comment="فیلدهای استفاده شده در unique key")
    field_mappings = Column(JSON, nullable=True, comment="نگاشت فیلدها")
    
    # وضعیت
    status = Column(String(50), default='running', comment="running, completed, failed")
    error_message = Column(Text, nullable=True)
    
    # زمان‌ها
    started_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    def __repr__(self):
        return f"<ImportBatch(batch_id='{self.batch_id}', status='{self.status}')>"
