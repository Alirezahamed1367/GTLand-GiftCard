"""
توابع کمکی برای تشخیص هوشمند وضعیت سلول‌های Google Sheets
"""
from typing import Any, Optional


def is_cell_checked(value: Any) -> bool:
    """
    تشخیص هوشمند اینکه یک سلول "فعال" است یا خیر
    
    این تابع انواع مختلف مقدار‌دهی در Google Sheets را پشتیبانی می‌کند:
    - Checkbox: TRUE/FALSE
    - Dropdown: بله/خیر، Yes/No، آماده/نامعتبر، ✓/✗
    - Text: 1/0, done/pending, فعال/غیرفعال
    - Unicode: ✓, ✔, ☑, ✅
    
    Args:
        value: مقدار سلول
        
    Returns:
        True اگر سلول "فعال" باشد، در غیر این صورت False
    
    Examples:
        >>> is_cell_checked(True)
        True
        >>> is_cell_checked("TRUE")
        True
        >>> is_cell_checked("بله")
        True
        >>> is_cell_checked("✓")
        True
        >>> is_cell_checked("آماده")
        True
        >>> is_cell_checked("")
        False
        >>> is_cell_checked("NO")
        False
    """
    # اگر خالی است
    if value is None or value == "":
        return False
    
    # تبدیل به رشته و normalize کردن
    str_value = str(value).strip()
    
    # اگر خالی است (بعد از strip)
    if not str_value:
        return False
    
    # تبدیل به حروف کوچک برای مقایسه
    lower_value = str_value.lower()
    
    # بررسی boolean واقعی
    if isinstance(value, bool):
        return value
    
    # بررسی مقادیر متنی رایج
    positive_values = {
        # انگلیسی
        "true", "yes", "y", "ok", "done", "completed", "ready", "active",
        "checked", "enabled", "on", "1", "complete", "finished",
        
        # فارسی
        "بله", "آره", "اره", "آری", "بلی", "بلە", "درست", "صحیح",
        "آماده", "تکمیل", "انجام شده", "فعال", "انجام", "تمام",
        
        # Unicode symbols
        "✓", "✔", "☑", "✅", "√", "tick", "check",
        
        # عربی
        "نعم", "صح", "جاهز"
    }
    
    # بررسی مقدار در لیست مثبت‌ها
    if lower_value in positive_values:
        return True
    
    # بررسی اینکه شروع با یکی از کلمات کلیدی باشد
    positive_starts = ["آماده", "done", "ready", "complete", "فعال", "active"]
    for start in positive_starts:
        if lower_value.startswith(start.lower()):
            return True
    
    # بررسی Unicode characters
    unicode_checks = ["✓", "✔", "☑", "✅", "√"]
    for check in unicode_checks:
        if check in str_value:
            return True
    
    return False


def is_cell_extracted(value: Any) -> bool:
    """
    تشخیص هوشمند اینکه یک سلول "استخراج شده" است یا خیر
    
    مشابه is_cell_checked اما برای ستون "استخراج شده"
    همان logic را دارد
    
    Args:
        value: مقدار سلول
        
    Returns:
        True اگر سلول "استخراج شده" باشد
    """
    # از همان تابع استفاده می‌کنیم
    return is_cell_checked(value)


def normalize_cell_value(value: Any, target_type: str = "boolean") -> Any:
    """
    تبدیل مقدار سلول به نوع مورد نظر
    
    Args:
        value: مقدار سلول
        target_type: نوع مورد نظر ('boolean', 'text', 'checkbox')
        
    Returns:
        مقدار تبدیل شده
    
    Examples:
        >>> normalize_cell_value("بله", "boolean")
        True
        >>> normalize_cell_value(True, "text")
        "TRUE"
        >>> normalize_cell_value("✓", "checkbox")
        True
    """
    if target_type == "boolean":
        return is_cell_checked(value)
    
    elif target_type == "text":
        if is_cell_checked(value):
            return "TRUE"
        else:
            return "FALSE"
    
    elif target_type == "checkbox":
        # برای Google Sheets checkbox
        return is_cell_checked(value)
    
    else:
        return value


def get_cell_status_info(value: Any) -> dict:
    """
    اطلاعات کامل درباره وضعیت یک سلول
    
    Args:
        value: مقدار سلول
        
    Returns:
        دیکشنری حاوی اطلاعات وضعیت
        
    Example:
        >>> get_cell_status_info("✓")
        {
            'original_value': '✓',
            'is_checked': True,
            'detected_type': 'unicode_symbol',
            'normalized_boolean': True,
            'normalized_text': 'TRUE'
        }
    """
    is_checked = is_cell_checked(value)
    
    # تشخیص نوع
    str_value = str(value).strip() if value else ""
    
    if isinstance(value, bool):
        detected_type = "boolean"
    elif str_value in ["✓", "✔", "☑", "✅", "√"]:
        detected_type = "unicode_symbol"
    elif str_value.upper() in ["TRUE", "FALSE"]:
        detected_type = "checkbox"
    elif str_value in ["بله", "خیر", "Yes", "No"]:
        detected_type = "dropdown_yesno"
    elif str_value in ["آماده", "نامعتبر", "Ready", "Not Ready"]:
        detected_type = "dropdown_ready"
    elif str_value in ["1", "0"]:
        detected_type = "numeric"
    else:
        detected_type = "text"
    
    return {
        'original_value': value,
        'is_checked': is_checked,
        'detected_type': detected_type,
        'normalized_boolean': is_checked,
        'normalized_text': 'TRUE' if is_checked else 'FALSE'
    }


# برای test
if __name__ == "__main__":
    # Test cases
    test_values = [
        True, False,
        "TRUE", "FALSE",
        "بله", "خیر",
        "Yes", "No",
        "✓", "✗",
        "آماده", "نامعتبر",
        "1", "0",
        "done", "pending",
        "", None,
        "Ready", "Not Ready"
    ]
    
    print("=" * 60)
    print("تست تابع تشخیص هوشمند وضعیت سلول")
    print("=" * 60)
    
    for val in test_values:
        result = is_cell_checked(val)
        info = get_cell_status_info(val)
        print(f"\n{'✅' if result else '❌'} {repr(val):20} → {result:5} | Type: {info['detected_type']}")
