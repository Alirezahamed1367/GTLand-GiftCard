"""
Migration Script - ایجاد جداول جدید
===================================
ایجاد جداول:
- field_roles, role_presets
- raw_data, import_batches
- products, purchases, sales, bonuses, customers
"""
import sys
from pathlib import Path

# اضافه کردن root به path
root_path = Path(__file__).parent
sys.path.insert(0, str(root_path))

from app.models.financial import (
    FinancialBase, financial_engine,
    FieldRole, RolePreset,
    init_default_roles, init_default_presets,
    get_financial_session
)


def run_migration():
    """
    اجرای Migration
    """
    print("=" * 60)
    print("🚀 شروع Migration - سیستم 4 مرحله‌ای جدید")
    print("=" * 60)
    
    try:
        # 1. ایجاد جداول
        print("\n📊 مرحله 1: ایجاد جداول...")
        FinancialBase.metadata.create_all(financial_engine)
        print("✅ جداول ایجاد شدند")
        
        # 2. بارگذاری نقش‌های پیش‌فرض
        print("\n🎭 مرحله 2: بارگذاری نقش‌های پیش‌فرض...")
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
        
        # 3. تأیید
        print("\n" + "=" * 60)
        print("✅ Migration با موفقیت کامل شد!")
        print("=" * 60)
        
        print("\n📋 جداول ایجاد شده:")
        print("  • field_roles - نقش‌های فیلدها")
        print("  • role_presets - پیش‌فرض‌های نقش")
        print("  • raw_data - داده‌های خام (Stage 1)")
        print("  • import_batches - دسته‌های import")
        print("  • products - محصولات/اکانت‌ها")
        print("  • purchases - خریدها")
        print("  • customers - مشتریان")
        print("  • sales - فروش‌ها")
        print("  • bonuses - بونوس/سیلور")
        
        print("\n🎯 مراحل بعدی:")
        print("  1. باز کردن برنامه GT-Land")
        print("  2. رفتن به منوی مدیریت نقش‌ها")
        print("  3. بررسی نقش‌های پیش‌فرض")
        print("  4. Import اولین شیت")
        
        return True
        
    except Exception as e:
        print(f"\n❌ خطا در Migration: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
