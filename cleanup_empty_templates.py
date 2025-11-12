"""
اسکریپت پاک‌سازی Template های خالی یا نامعتبر
"""
from app.core.database import db_manager
from app.core.logger import app_logger

def cleanup_empty_templates():
    """پاک کردن Template هایی که نام ندارند یا نامعتبر هستند"""
    try:
        print("🔍 جستجوی Template های خالی...")
        
        templates = db_manager.get_all_templates()
        deleted_count = 0
        
        for template in templates:
            # بررسی شرایط حذف
            should_delete = False
            reason = ""
            
            # 1. نام خالی
            if not template.name or not template.name.strip():
                should_delete = True
                reason = "نام خالی"
            
            # 2. مسیر فایل ندارد
            elif not template.template_path or not template.template_path.strip():
                should_delete = True
                reason = "مسیر فایل خالی"
            
            # 3. هیچ Mapping ندارد
            elif not template.column_mappings or len(template.column_mappings) == 0:
                should_delete = True
                reason = "بدون Mapping"
            
            if should_delete:
                print(f"   🗑️  حذف Template (ID: {template.id}) - دلیل: {reason}")
                print(f"      نام: '{template.name}'")
                print(f"      نوع: {template.template_type}")
                print(f"      مسیر: {template.template_path}")
                
                # حذف از دیتابیس
                success, message = db_manager.delete_template(template.id)
                if success:
                    deleted_count += 1
                    print(f"      ✅ حذف شد")
                else:
                    print(f"      ❌ خطا: {message}")
                print()
        
        if deleted_count > 0:
            print(f"\n✅ تعداد {deleted_count} Template نامعتبر حذف شد")
        else:
            print("\n✅ هیچ Template نامعتبری یافت نشد")
        
        # نمایش Template های باقی‌مانده
        remaining = db_manager.get_all_templates()
        print(f"\n📊 تعداد Template های باقی‌مانده: {len(remaining)}")
        
        if remaining:
            print("\n📋 لیست Template های معتبر:")
            for i, template in enumerate(remaining, 1):
                mappings = template.column_mappings or {}
                print(f"   {i}. {template.name}")
                print(f"      نوع: {template.template_type}")
                print(f"      Mappings: {len(mappings)}")
                print()
        
    except Exception as e:
        app_logger.error(f"خطا در پاک‌سازی: {e}")
        print(f"\n❌ خطا: {e}")

if __name__ == "__main__":
    print("="*60)
    print("🧹 پاک‌سازی Template های نامعتبر")
    print("="*60)
    print()
    
    cleanup_empty_templates()
    
    print()
    print("="*60)
    print("✅ پاک‌سازی به پایان رسید")
    print("="*60)
