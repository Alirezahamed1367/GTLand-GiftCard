"""
اسکریپت مایگریشن - ایجاد جداول سیستم پویا
"""
import sys
sys.path.append('.')

from app.models.financial import (
    init_financial_db,
    FinancialSessionLocal,
    # Dynamic Models
    SheetImport, RawData, FieldMapping, Platform,
    DiscrepancyReport, CustomReport,
    # Simple Models  
    Account, AccountGold, AccountSilver, Sale, Customer
)
from app.models.financial.base_financial import FinancialBase, financial_engine
from sqlalchemy import inspect


def check_table_exists(engine, table_name):
    """بررسی وجود جدول"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def migrate_to_dynamic_system():
    """
    مایگریشن به سیستم پویا
    
    مراحل:
    1. ایجاد جداول جدید (اگر وجود ندارند)
    2. به‌روزرسانی جداول موجود (اضافه کردن ستون‌های جدید)
    3. ایجاد Platform های پیش‌فرض
    """
    print("=" * 60)
    print("🚀 شروع مایگریشن به سیستم پویا (Dynamic System)")
    print("=" * 60)
    
    # بررسی جداول موجود
    print("\n📋 بررسی جداول موجود...")
    
    tables_to_create = [
        'sheet_imports',
        'raw_data', 
        'field_mappings',
        'platforms',
        'discrepancy_reports',
        'custom_reports'
    ]
    
    existing_tables = []
    new_tables = []
    
    for table in tables_to_create:
        if check_table_exists(financial_engine, table):
            existing_tables.append(table)
        else:
            new_tables.append(table)
    
    if existing_tables:
        print(f"  ✅ جداول موجود: {', '.join(existing_tables)}")
    
    if new_tables:
        print(f"  🆕 جداول جدید: {', '.join(new_tables)}")
    
    # ایجاد همه جداول
    print("\n🔨 ایجاد جداول...")
    
    try:
        # این خط همه جداول را ایجاد می‌کند (اگر وجود نداشته باشند)
        FinancialBase.metadata.create_all(bind=financial_engine)
        print("  ✅ همه جداول با موفقیت ایجاد شدند")
    except Exception as e:
        print(f"  ❌ خطا در ایجاد جداول: {str(e)}")
        return False
    
    # ایجاد Platform های پیش‌فرض
    print("\n🎮 ایجاد پلتفرم‌های پیش‌فرض...")
    
    session = FinancialSessionLocal()
    
    default_platforms = [
        {'code': 'roblox', 'name': 'Roblox'},
        {'code': 'apple', 'name': 'Apple Gift Card'},
        {'code': 'google', 'name': 'Google Play Gift Card'},
        {'code': 'nintendo', 'name': 'Nintendo eShop'},
        {'code': 'xbox', 'name': 'Xbox Gift Card'},
        {'code': 'playstation', 'name': 'PlayStation Store'},
        {'code': 'pubg', 'name': 'PUBG Mobile'},
        {'code': 'freefire', 'name': 'Free Fire'},
        {'code': 'steam', 'name': 'Steam Wallet'},
    ]
    
    created_count = 0
    
    for platform_data in default_platforms:
        existing = session.query(Platform).filter_by(code=platform_data['code']).first()
        
        if not existing:
            platform = Platform(
                code=platform_data['code'],
                name=platform_data['name'],
                is_active=True
            )
            session.add(platform)
            created_count += 1
            print(f"  ✅ {platform_data['name']}")
    
    session.commit()
    session.close()
    
    if created_count > 0:
        print(f"\n  ✅ {created_count} پلتفرم جدید ایجاد شد")
    else:
        print("  ℹ️ همه پلتفرم‌ها قبلاً وجود داشتند")
    
    # خلاصه
    print("\n" + "=" * 60)
    print("✅ مایگریشن با موفقیت تکمیل شد!")
    print("=" * 60)
    print("\n📊 وضعیت جداول:")
    print(f"  • SheetImport: ذخیره شیت‌های Import شده")
    print(f"  • RawData: داده‌های خام JSON")
    print(f"  • FieldMapping: نقش هر ستون (تعریف شده توسط کاربر)")
    print(f"  • Platform: پلتفرم‌های فروش")
    print(f"  • DiscrepancyReport: گزارش مغایرت‌های سود")
    print(f"  • CustomReport: گزارش‌های سفارشی کاربر")
    
    print("\n🎯 مراحل بعدی:")
    print("  1. Import داده از Google Sheets")
    print("  2. تعریف Field Mapping در UI")
    print("  3. پردازش داده‌ها با DynamicDataProcessor")
    print("  4. تولید گزارش‌ها")
    
    return True


if __name__ == "__main__":
    success = migrate_to_dynamic_system()
    
    if not success:
        print("\n❌ مایگریشن با خطا مواجه شد")
        sys.exit(1)
    
    print("\n✅ مایگریشن موفق")
    sys.exit(0)
