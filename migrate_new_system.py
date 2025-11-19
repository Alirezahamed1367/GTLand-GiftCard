"""
Migration Script - ایجاد جداول کامل
===================================
ایجاد جداول:
- سیستم قدیمی: sheet_configs, sales_data, process_logs, export_logs, export_templates
- سیستم جدید: field_roles, role_presets, raw_data, import_batches, v2_products, etc.
"""
import sys
from pathlib import Path

# اضافه کردن root به path
root_path = Path(__file__).parent
sys.path.insert(0, str(root_path))

from app.models.base import Base, engine
from app.models.financial import (
    FinancialBase, financial_engine,
    FieldRole, RolePreset,
    init_default_roles, init_default_presets,
    get_financial_session
)


def run_migration():
    """
    اجرای Migration کامل
    """
    print("=" * 60)
    print("🚀 شروع Migration - سیستم کامل")
    print("=" * 60)
    
    try:
        # 1. ایجاد جداول سیستم قدیمی (برای سازگاری)
        print("\n📊 مرحله 1: ایجاد جداول سیستم اصلی...")
        Base.metadata.create_all(engine)
        print("✅ جداول اصلی ایجاد شدند (sheet_configs, sales_data, logs, etc.)")
        
        # 2. ایجاد جداول سیستم جدید
        print("\n📊 مرحله 2: ایجاد جداول سیستم 4 مرحله‌ای...")
        FinancialBase.metadata.create_all(financial_engine)
        print("✅ جداول سیستم جدید ایجاد شدند (field_roles, raw_data, v2_products, etc.)")
        
        # 3. بارگذاری نقش‌های پیش‌فرض
        print("\n🎭 مرحله 3: بارگذاری نقش‌های پیش‌فرض...")
        db = get_financial_session()
        
        try:
            init_default_roles(db)
            init_default_presets(db)
            
            # شمارش
            roles_count = db.query(FieldRole).count()
            presets_count = db.query(RolePreset).count()
            
            print(f"✅ {roles_count} نقش پیش‌فرض بارگذاری شد")
            print(f"✅ {presets_count} پیش‌فرض بارگذاری شد")
            
        finally:
            db.close()
        
        # 4. تأیید
        print("\n" + "=" * 60)
        print("✅ Migration با موفقیت کامل شد!")
        print("=" * 60)
        
        print("\n📋 جداول سیستم اصلی:")
        print("  • sheet_configs - تنظیمات شیت‌ها")
        print("  • sales_data - داده‌های فروش")
        print("  • export_templates - قالب‌های خروجی")
        print("  • process_logs - لاگ عملیات")
        print("  • export_logs - لاگ خروجی‌ها")
        
        print("\n📋 جداول سیستم 4 مرحله‌ای:")
        print("  • field_roles - نقش‌های فیلدها")
        print("  • role_presets - پیش‌فرض‌های نقش")
        print("  • raw_data - داده‌های خام (Stage 1)")
        print("  • import_batches - دسته‌های import")
        print("  • v2_products - محصولات/اکانت‌ها")
        print("  • v2_purchases - خریدها")
        print("  • v2_customers - مشتریان")
        print("  • v2_sales - فروش‌ها")
        print("  • v2_bonuses - بونوس/سیلور")
        
        print("\n🎯 مراحل بعدی:")
        print("  1. اجرای برنامه: python app/main.py")
        print("  2. تعریف شیت در قسمت 'شیت‌ها'")
        print("  3. Import از طریق BI Platform → Smart Import")
        
        return True
        
    except Exception as e:
        print(f"\n❌ خطا در Migration: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
