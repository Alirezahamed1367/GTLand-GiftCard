"""
مدل‌های دیتابیس سیستم مالی GT-Land - نسخه ساده Label-Based
Financial Database Models - Simple Label-Based System

سیستم جدید بر اساس Label به عنوان کلید اصلی
"""

# ═══════════════════════════════════════════════════════════════
# BASE (دیتابیس و session)
# ═══════════════════════════════════════════════════════════════

from .base_financial import (
    FinancialBase,
    financial_engine,
    FinancialSessionLocal,
    get_financial_db,
    get_financial_session,
    init_financial_db
)

# ═══════════════════════════════════════════════════════════════
# SIMPLE MODELS (مدل‌های ساده - سیستم جدید)
# ═══════════════════════════════════════════════════════════════

from .simple_models import (
    Account,           # آکانت‌ها (با label به عنوان کلید)
    AccountGold,       # خریدهای گلد
    AccountSilver,     # بونوس‌های سیلور (رایگان)
    Sale,              # فروش‌ها (gold یا silver)
    SaleType,          # نوع فروش (Enum)
    AccountSummary,    # خلاصه محاسبات (Materialized View)
    Customer           # مشتریان
)

# ═══════════════════════════════════════════════════════════════
# DYNAMIC MODELS (مدل‌های سیستم پویا - Field Mapping)
# ═══════════════════════════════════════════════════════════════

from .dynamic_models import (
    SheetImport,       # شیت‌های Import شده
    RawData,           # داده‌های خام
    FieldMapping,      # نقشه‌برداری فیلدها
    Platform,          # پلتفرم‌های فروش
    DiscrepancyReport, # گزارش مغایرت‌ها
    CustomReport,      # گزارش‌های سفارشی
    SheetType,         # نوع شیت (Enum)
    DataType,          # نوع داده (Enum)
    TargetField        # نقش فیلد (Enum)
)

# ═══════════════════════════════════════════════════════════════
# FIELD ROLES & CUSTOM FIELDS (قابل پیکربندی توسط کاربر)
# ═══════════════════════════════════════════════════════════════

from .field_roles import (
    FieldRole,              # نقش‌های فیلد
    RolePreset,             # پیش‌فرض‌ها
    init_default_roles,     # ایجاد نقش‌های پیش‌فرض
    init_default_presets    # ایجاد preset‌های پیش‌فرض
)

# حذف import قدیمی custom_fields که با dynamic_models جایگزین شد
# from .custom_fields import (
#     CustomField,     # فیلدهای سفارشی
#     FieldMapping     # نگاشت فیلدها
# )

# ═══════════════════════════════════════════════════════════════
# RAW DATA (داده‌های خام از Google Sheets) - قدیمی
# ═══════════════════════════════════════════════════════════════

# از raw_data.py قدیمی استفاده نمی‌کنیم - جایگزین شده با dynamic_models
# from .raw_data import (
#     RawData as OldRawData,  # داده‌های خام قدیمی
#     ImportBatch     # دسته‌های import
# )

# ═══════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════

__all__ = [
    # Base
    'FinancialBase',
    'financial_engine',
    'FinancialSessionLocal',
    'get_financial_db',
    'get_financial_session',
    'init_financial_db',
    
    # Simple Models
    'Account',
    'AccountGold',
    'AccountSilver',
    'Sale',
    'SaleType',
    'AccountSummary',
    'Customer',
    
    # Dynamic Models
    'SheetImport',
    'RawData',
    'FieldMapping',
    'Platform',
    'DiscrepancyReport',
    'CustomReport',
    'SheetType',
    'DataType',
    'TargetField',
    
    # Field Roles (old system - kept for compatibility)
    'FieldRole',
    'RolePreset',
    'init_default_roles',
    'init_default_presets',
]
