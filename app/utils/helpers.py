"""
توابع کمکی - Helper Functions
"""
import hashlib
import json
import re
from typing import Any, Dict, List, Optional
from datetime import datetime
import validators


def generate_unique_key(data: Dict, key_columns: List[str]) -> str:
    """
    تولید کلید یکتا از ترکیب ستون‌های مشخص
    
    Args:
        data: دیکشنری داده
        key_columns: لیست نام ستون‌های کلیدی
        
    Returns:
        کلید یکتای MD5
    """
    key_values = []
    for col in key_columns:
        value = data.get(col, '')
        # تبدیل به رشته و حذف فضاهای خالی
        key_values.append(str(value).strip())
    
    combined = '|'.join(key_values)
    return hashlib.md5(combined.encode('utf-8')).hexdigest()


def validate_google_sheet_url(url: str) -> bool:
    """
    اعتبارسنجی URL گوگل شیت
    
    Args:
        url: آدرس گوگل شیت
        
    Returns:
        True اگر معتبر باشد
    """
    if not validators.url(url):
        return False
    
    patterns = [
        r'https://docs\.google\.com/spreadsheets/d/[a-zA-Z0-9-_]+',
        r'https://drive\.google\.com/.*[?&]id=[a-zA-Z0-9-_]+',
    ]
    
    for pattern in patterns:
        if re.match(pattern, url):
            return True
    
    return False


def extract_sheet_id(url: str) -> Optional[str]:
    """
    استخراج شناسه شیت از URL
    
    Args:
        url: آدرس گوگل شیت
        
    Returns:
        شناسه شیت یا None
    """
    patterns = [
        r'spreadsheets/d/([a-zA-Z0-9-_]+)',
        r'[?&]id=([a-zA-Z0-9-_]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def format_bytes(bytes_num: int) -> str:
    """
    فرمت کردن حجم بایت به رشته قابل خواندن
    
    Args:
        bytes_num: تعداد بایت
        
    Returns:
        رشته فرمت شده مثل "10.5 MB"
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_num < 1024.0:
            return f"{bytes_num:.2f} {unit}"
        bytes_num /= 1024.0
    return f"{bytes_num:.2f} PB"


def sanitize_filename(filename: str) -> str:
    """
    پاکسازی نام فایل از کاراکترهای غیرمجاز
    
    Args:
        filename: نام فایل
        
    Returns:
        نام فایل پاکسازی شده
    """
    # حذف کاراکترهای غیرمجاز
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # حذف فضاهای اضافی
    filename = ' '.join(filename.split())
    return filename


def deep_merge(dict1: Dict, dict2: Dict) -> Dict:
    """
    ادغام عمیق دو دیکشنری
    
    Args:
        dict1: دیکشنری اول
        dict2: دیکشنری دوم
        
    Returns:
        دیکشنری ادغام شده
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """
    تقسیم لیست به بخش‌های کوچکتر
    
    Args:
        lst: لیست ورودی
        chunk_size: اندازه هر بخش
        
    Returns:
        لیست از بخش‌ها
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def compare_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """
    مقایسه دو دیکشنری و یافتن تفاوت‌ها
    
    Args:
        dict1: دیکشنری اول (قدیمی)
        dict2: دیکشنری دوم (جدید)
        
    Returns:
        دیکشنری تفاوت‌ها
    """
    changes = {}
    
    # کلیدهای جدید
    for key in dict2:
        if key not in dict1:
            changes[key] = {
                'old': None,
                'new': dict2[key],
                'status': 'added'
            }
        elif dict1[key] != dict2[key]:
            changes[key] = {
                'old': dict1[key],
                'new': dict2[key],
                'status': 'modified'
            }
    
    # کلیدهای حذف شده
    for key in dict1:
        if key not in dict2:
            changes[key] = {
                'old': dict1[key],
                'new': None,
                'status': 'removed'
            }
    
    return changes


def format_duration(seconds: float) -> str:
    """
    فرمت کردن مدت زمان به فارسی
    
    Args:
        seconds: تعداد ثانیه
        
    Returns:
        رشته فرمت شده مثل "2 دقیقه و 30 ثانیه"
    """
    if seconds < 60:
        return f"{int(seconds)} ثانیه"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes} دقیقه و {secs} ثانیه"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours} ساعت و {minutes} دقیقه"


def parse_persian_date(date_str: str) -> Optional[datetime]:
    """
    تبدیل تاریخ فارسی به datetime
    
    Args:
        date_str: رشته تاریخ فارسی
        
    Returns:
        شیء datetime یا None
    """
    # این تابع باید با توجه به نیاز واقعی پیاده‌سازی شود
    # فعلاً یک نمونه ساده است
    try:
        # فرمت‌های مختلف را امتحان کن
        formats = [
            "%Y/%m/%d",
            "%Y-%m-%d",
            "%Y/%m/%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    except Exception:
        return None


def safe_get(dictionary: Dict, keys: List[str], default: Any = None) -> Any:
    """
    دریافت ایمن مقدار از دیکشنری تودرتو
    
    Args:
        dictionary: دیکشنری
        keys: لیست کلیدها
        default: مقدار پیش‌فرض
        
    Returns:
        مقدار یا default
    """
    result = dictionary
    for key in keys:
        if isinstance(result, dict) and key in result:
            result = result[key]
        else:
            return default
    return result


def convert_to_jalali(gregorian_date: datetime) -> str:
    """
    تبدیل تاریخ میلادی به شمسی
    
    Args:
        gregorian_date: تاریخ میلادی
        
    Returns:
        رشته تاریخ شمسی
    """
    # این تابع نیاز به کتابخانه jdatetime دارد
    # فعلاً همان تاریخ میلادی را برمی‌گرداند
    # در صورت نیاز باید jdatetime نصب شود
    return gregorian_date.strftime("%Y/%m/%d")


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    کوتاه کردن رشته
    
    Args:
        text: متن
        max_length: حداکثر طول
        suffix: پسوند
        
    Returns:
        متن کوتاه شده
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def is_valid_email(email: str) -> bool:
    """
    اعتبارسنجی ایمیل
    
    Args:
        email: آدرس ایمیل
        
    Returns:
        True اگر معتبر باشد
    """
    return validators.email(email) is True


def clean_dict(data: Dict) -> Dict:
    """
    پاکسازی دیکشنری از مقادیر None و رشته‌های خالی
    
    Args:
        data: دیکشنری
        
    Returns:
        دیکشنری پاکسازی شده
    """
    return {
        k: v for k, v in data.items()
        if v is not None and (not isinstance(v, str) or v.strip())
    }
