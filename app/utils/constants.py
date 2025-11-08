"""
ثابت‌های برنامه - Constants
"""
from enum import Enum


class ProcessStatus(Enum):
    """وضعیت فرآیندها"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    IN_PROGRESS = "in_progress"


class ProcessType(Enum):
    """نوع فرآیند"""
    EXTRACT = "extract"
    EXPORT = "export"
    UPDATE = "update"
    DELETE = "delete"
    SYNC = "sync"


class ExportType(Enum):
    """نوع خروجی"""
    TYPE_1 = "type1"
    TYPE_2 = "type2"
    TYPE_3 = "type3"


# پیام‌های خطا به فارسی
ERROR_MESSAGES = {
    # خطاهای اتصال
    "CONNECTION_FAILED": "خطا در برقراری ارتباط با سرور. لطفاً اتصال اینترنت خود را بررسی کنید.",
    "DATABASE_CONNECTION_FAILED": "خطا در اتصال به دیتابیس. لطفاً تنظیمات دیتابیس را بررسی کنید.",
    "GOOGLE_SHEETS_AUTH_FAILED": "خطا در احراز هویت با Google Sheets. لطفاً فایل credentials را بررسی کنید.",
    
    # خطاهای داده
    "DUPLICATE_DATA": "داده تکراری شناسایی شد. آیا می‌خواهید داده قبلی را بروزرسانی کنید؟",
    "INVALID_DATA": "داده‌های نامعتبر شناسایی شد. لطفاً داده‌های ورودی را بررسی کنید.",
    "EMPTY_DATA": "هیچ داده‌ای برای پردازش یافت نشد.",
    "MISSING_REQUIRED_FIELD": "فیلدهای الزامی وارد نشده است.",
    
    # خطاهای فایل
    "FILE_NOT_FOUND": "فایل مورد نظر یافت نشد.",
    "FILE_READ_ERROR": "خطا در خواندن فایل.",
    "FILE_WRITE_ERROR": "خطا در نوشتن فایل.",
    "TEMPLATE_NOT_FOUND": "فایل تمپلیت یافت نشد.",
    
    # خطاهای شیت
    "SHEET_NOT_FOUND": "شیت مورد نظر یافت نشد.",
    "WORKSHEET_NOT_FOUND": "ورک‌شیت مورد نظر در فایل یافت نشد.",
    "COLUMN_NOT_FOUND": "ستون مورد نظر در شیت یافت نشد.",
    "INVALID_SHEET_URL": "آدرس Google Sheet نامعتبر است.",
    
    # خطاهای پردازش
    "PROCESSING_ERROR": "خطا در پردازش داده‌ها.",
    "EXPORT_ERROR": "خطا در تولید فایل خروجی.",
    "VALIDATION_ERROR": "خطا در اعتبارسنجی داده‌ها.",
    
    # خطاهای عمومی
    "UNKNOWN_ERROR": "خطای ناشناخته رخ داد.",
    "TIMEOUT_ERROR": "زمان انتظار برای عملیات به پایان رسید.",
    "PERMISSION_DENIED": "شما دسترسی لازم برای این عملیات را ندارید.",
}


# پیام‌های موفقیت
SUCCESS_MESSAGES = {
    "DATA_EXTRACTED": "داده‌ها با موفقیت استخراج شدند.",
    "DATA_SAVED": "داده‌ها با موفقیت ذخیره شدند.",
    "EXPORT_COMPLETED": "فایل خروجی با موفقیت تولید شد.",
    "SYNC_COMPLETED": "همگام‌سازی با موفقیت انجام شد.",
    "CONFIG_SAVED": "تنظیمات با موفقیت ذخیره شدند.",
    "CONNECTION_SUCCESSFUL": "اتصال با موفقیت برقرار شد.",
}


# پیام‌های هشدار
WARNING_MESSAGES = {
    "NO_NEW_DATA": "هیچ داده جدیدی برای استخراج یافت نشد.",
    "PARTIAL_SUCCESS": "برخی از داده‌ها با موفقیت پردازش شدند.",
    "SLOW_CONNECTION": "سرعت اتصال پایین است. ممکن است عملیات طولانی شود.",
}


# تنظیمات پیش‌فرض
DEFAULT_SETTINGS = {
    "theme": "dark",
    "language": "fa",
    "auto_sync": True,
    "sync_interval": 300,  # 5 دقیقه
    "batch_size": 1000,
    "max_retries": 3,
    "timeout": 300,
}


# رنگ‌های برنامه
COLORS = {
    "primary": "#2196F3",
    "secondary": "#4CAF50",
    "success": "#4CAF50",
    "warning": "#FFC107",
    "error": "#F44336",
    "info": "#2196F3",
    "dark": "#212121",
    "light": "#FAFAFA",
}


# آیکون‌های برنامه
ICONS = {
    "dashboard": "dashboard",
    "sheets": "description",
    "extract": "cloud_download",
    "export": "file_upload",
    "reports": "assessment",
    "settings": "settings",
    "sync": "sync",
    "add": "add",
    "edit": "edit",
    "delete": "delete",
    "save": "save",
    "cancel": "cancel",
}


# حداکثر اندازه‌ها
MAX_SIZES = {
    "file_size_mb": 100,
    "rows_per_batch": 1000,
    "export_rows": 100000,
    "log_file_mb": 50,
}


# فرمت‌های تاریخ
DATE_FORMATS = {
    "display": "%Y/%m/%d %H:%M:%S",
    "filename": "%Y%m%d_%H%M%S",
    "persian": "%Y/%m/%d",
}
