"""
بررسی لاگ‌های موجود در دیتابیس
"""
from app.core.database import db_manager
from app.models import ProcessLog, ExportLog

def check_logs():
    """بررسی لاگ‌های موجود"""
    try:
        db = db_manager.get_session()
        
        print("="*60)
        print("📋 بررسی لاگ‌های دیتابیس")
        print("="*60)
        print()
        
        # بررسی لاگ‌های عملیات
        process_logs = db.query(ProcessLog).order_by(ProcessLog.id.desc()).limit(10).all()
        print(f"🔍 تعداد لاگ‌های عملیات (Process Logs): {len(process_logs)}")
        
        if process_logs:
            print("\n📝 آخرین لاگ‌های عملیات:")
            for i, log in enumerate(process_logs, 1):
                print(f"   {i}. ID: {log.id}")
                print(f"      نوع: {log.process_type}")
                print(f"      وضعیت: {log.status}")
                print(f"      پیام: {log.message[:50]}...")
                print(f"      تاریخ: {log.started_at}")
                print()
        else:
            print("   ⚠️ هیچ لاگ عملیاتی یافت نشد")
        
        print()
        print("-"*60)
        print()
        
        # بررسی لاگ‌های خروجی
        export_logs = db.query(ExportLog).order_by(ExportLog.id.desc()).limit(10).all()
        print(f"🔍 تعداد لاگ‌های خروجی (Export Logs): {len(export_logs)}")
        
        if export_logs:
            print("\n📤 آخرین لاگ‌های خروجی:")
            for i, log in enumerate(export_logs, 1):
                print(f"   {i}. ID: {log.id}")
                print(f"      نوع: {log.export_type}")
                print(f"      تعداد رکورد: {log.record_count}")
                print(f"      مسیر: {log.file_path}")
                print(f"      تاریخ: {log.created_at}")
                print()
        else:
            print("   ⚠️ هیچ لاگ خروجی یافت نشد")
        
        db.close()
        
        print()
        print("="*60)
        print("✅ بررسی به پایان رسید")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ خطا: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_logs()
