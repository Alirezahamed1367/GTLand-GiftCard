"""
ساخت کلید یکتا برای ردیف‌های Google Sheet
"""
import hashlib
import json
from typing import Dict, List, Optional


def generate_unique_key(
    sheet_config_id: int,
    row_data: Dict,
    unique_columns: Optional[List[str]] = None,
    row_number: Optional[int] = None
) -> str:
    """
    ساخت کلید یکتا برای یک ردیف
    
    استراتژی:
    1. اگر unique_columns مشخص شده → از محتوای آن ستون‌ها
    2. اگر نه → از تمام محتوای ردیف
    3. شماره ردیف به عنوان fallback
    
    Args:
        sheet_config_id: شناسه تنظیمات شیت
        row_data: داده‌های ردیف
        unique_columns: ستون‌هایی که برای یکتایی استفاده می‌شوند
        row_number: شماره ردیف (اختیاری)
        
    Returns:
        کلید یکتا به فرمت: {sheet_id}_{hash}[_{row}]
    """
    
    # انتخاب داده‌های کلیدی
    if unique_columns:
        # فقط ستون‌های مشخص شده
        key_data = {
            col: row_data.get(col, '')
            for col in unique_columns
            if col in row_data
        }
    else:
        # تمام داده‌ها
        key_data = row_data
    
    # تبدیل به JSON و نرمال‌سازی
    # sort_keys=True باعث می‌شود ترتیب مهم نباشد
    data_str = json.dumps(
        key_data, 
        sort_keys=True, 
        ensure_ascii=False,
        separators=(',', ':')  # حذف فضاهای اضافی
    ).strip()
    
    # ساخت hash
    hash_value = hashlib.md5(data_str.encode('utf-8')).hexdigest()[:16]
    
    # ساخت کلید نهایی
    if row_number:
        # شامل شماره ردیف (برای تشخیص جابجایی)
        return f"{sheet_config_id}_{hash_value}_r{row_number}"
    else:
        # فقط بر اساس محتوا
        return f"{sheet_config_id}_{hash_value}"


def extract_row_number_from_key(unique_key: str) -> Optional[int]:
    """
    استخراج شماره ردیف از کلید یکتا
    
    Args:
        unique_key: کلید یکتا
        
    Returns:
        شماره ردیف یا None
    """
    parts = unique_key.split('_')
    
    # فرمت: {sheet_id}_{hash}_r{row_number}
    if len(parts) >= 3 and parts[-1].startswith('r'):
        try:
            return int(parts[-1][1:])  # حذف 'r' و تبدیل به عدد
        except ValueError:
            return None
    
    return None


def generate_content_hash(row_data: Dict, columns: Optional[List[str]] = None) -> str:
    """
    ساخت hash فقط از محتوا (بدون شماره ردیف)
    برای مقایسه محتوایی
    
    Args:
        row_data: داده‌های ردیف
        columns: ستون‌های خاص (اختیاری)
        
    Returns:
        hash محتوا
    """
    if columns:
        key_data = {col: row_data.get(col, '') for col in columns if col in row_data}
    else:
        key_data = row_data
    
    data_str = json.dumps(key_data, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    return hashlib.md5(data_str.encode('utf-8')).hexdigest()[:16]


def compare_data_content(data1: Dict, data2: Dict, ignore_keys: List[str] = None) -> bool:
    """
    مقایسه محتوای دو دیکشنری
    
    Args:
        data1: داده اول
        data2: داده دوم
        ignore_keys: کلیدهایی که نباید مقایسه شوند
        
    Returns:
        True اگر محتوا یکسان باشد
    """
    ignore_keys = ignore_keys or []
    
    # حذف کلیدهای نادیده گرفته شده
    clean_data1 = {k: v for k, v in data1.items() if k not in ignore_keys}
    clean_data2 = {k: v for k, v in data2.items() if k not in ignore_keys}
    
    # مقایسه با hash
    hash1 = generate_content_hash(clean_data1)
    hash2 = generate_content_hash(clean_data2)
    
    return hash1 == hash2
