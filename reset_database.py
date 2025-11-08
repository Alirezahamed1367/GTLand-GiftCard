"""
اسکریپت حذف و ایجاد مجدد دیتابیس
"""
import sys
import os
from pathlib import Path
import time

# اضافه کردن مسیر پروژه
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def reset_database():
    """حذف و ایجاد مجدد دیتابیس"""
    print("🗑️ در حال حذف دیتابیس قدیمی...")
    
    db_path = project_root / "data" / "gt_land.db"
    
    # بستن تمام اتصالات SQLAlchemy
    try:
        from app.core.database import db_manager
        db_manager.close()
        print("✅ اتصالات دیتابیس بسته شد")
    except Exception as e:
        print(f"⚠️ خطا در بستن اتصالات: {e}")
    
    # بستن تمام اتصالات
    import gc
    gc.collect()
    time.sleep(2)
    
    # حذف دیتابیس قدیمی
    if db_path.exists():
        try:
            # تلاش اول
            os.remove(db_path)
            print("✅ دیتابیس قدیمی حذف شد")
        except PermissionError:
            # تلاش دوم: تغییر نام
            try:
                backup_path = db_path.with_suffix('.db.old')
                if backup_path.exists():
                    os.remove(backup_path)
                os.rename(db_path, backup_path)
                print(f"✅ دیتابیس قدیمی به {backup_path.name} تغییر نام یافت")
            except Exception as e2:
                print(f"❌ خطا در حذف دیتابیس: {e2}")
                print("⚠️ لطفاً:")
                print("   1. تمام ترمینال‌های Python را ببندید")
                print("   2. VS Code را ببندید و دوباره باز کنید")
                print("   3. دوباره این اسکریپت را اجرا کنید")
                return False
        except Exception as e:
            print(f"❌ خطا در حذف دیتابیس: {e}")
            print("⚠️ لطفاً برنامه را ببندید و دوباره امتحان کنید")
            return False
    else:
        print("ℹ️ دیتابیس وجود ندارد")
    
    # ایجاد دیتابیس جدید
    print("\n🔧 در حال ایجاد دیتابیس جدید...")
    try:
        from app.models import init_db
        init_db()
        print("✅ دیتابیس جدید با موفقیت ایجاد شد")
        
        # بررسی
        if db_path.exists():
            size = db_path.stat().st_size
            print(f"📊 حجم دیتابیس: {size} bytes")
        
        return True
    except Exception as e:
        print(f"❌ خطا در ایجاد دیتابیس: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🔄 ریست کامل دیتابیس GT-Land")
    print("=" * 50)
    
    confirm = input("\n⚠️ این عملیات تمام داده‌ها را حذف می‌کند. ادامه؟ (yes/no): ")
    if confirm.lower() != "yes":
        print("❌ عملیات لغو شد")
        sys.exit(0)
    
    print()
    success = reset_database()
    
    if success:
        print("\n" + "=" * 50)
        print("✅ عملیات با موفقیت انجام شد!")
        print("=" * 50)
        print("\n📝 مراحل بعدی:")
        print("1. فایل credentials.json را در config/ قرار دهید")
        print("2. برنامه را اجرا کنید: python app/main.py")
    else:
        print("\n" + "=" * 50)
        print("❌ عملیات ناموفق بود")
        print("=" * 50)
        sys.exit(1)
