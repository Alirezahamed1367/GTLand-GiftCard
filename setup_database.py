"""
اسکریپت راه‌اندازی اولیه دیتابیس
"""
import sys
from pathlib import Path

# اضافه کردن مسیر پروژه به sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.models import init_db, drop_db, SessionLocal
from app.models.sheet_config import SheetConfig
from app.models.export_template import ExportTemplate
from datetime import datetime


def setup_database():
    """راه‌اندازی دیتابیس"""
    print("🔧 در حال راه‌اندازی دیتابیس...")
    
    try:
        # ایجاد جداول
        init_db()
        print("✅ جداول با موفقیت ایجاد شدند.")
        
        # بررسی اتصال
        from sqlalchemy import text
        db = SessionLocal()
        result = db.execute(text("SELECT 1")).scalar()
        if result == 1:
            print("✅ اتصال به دیتابیس برقرار است.")
        db.close()
        
        # ایجاد داده‌های نمونه (اختیاری)
        create_sample_data = input("\nآیا می‌خواهید داده‌های نمونه ایجاد شود؟ (y/n): ")
        if create_sample_data.lower() == 'y':
            add_sample_data()
        
        print("\n✅ راه‌اندازی با موفقیت انجام شد!")
        print("\n📝 مراحل بعدی:")
        print("1. فایل credentials.json را در دایرکتوری config قرار دهید")
        print("2. فایل‌های تمپلیت Excel را در دایرکتوری templates قرار دهید")
        print("3. فایل .env را تنظیم کنید")
        print("4. برنامه را اجرا کنید: python app/main.py")
        
    except Exception as e:
        print(f"\n❌ خطا در راه‌اندازی: {str(e)}")
        sys.exit(1)


def add_sample_data():
    """افزودن داده‌های نمونه"""
    print("\n📥 در حال افزودن داده‌های نمونه...")
    
    try:
        db = SessionLocal()
        
        # تنظیمات نمونه شیت
        sample_config = SheetConfig(
            name="شیت نمونه",
            sheet_url="https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit",
            worksheet_name="Sheet1",
            is_active=False,  # غیرفعال به طور پیش‌فرض
            column_mappings={
                "تاریخ": "date",
                "نام مشتری": "customer_name",
                "مبلغ": "amount",
                "توضیحات": "description"
            },
            ready_column="آماده",
            extracted_column="استخراج شده",
            unique_key_columns=["تاریخ", "نام مشتری"],
            description="این یک تنظیمات نمونه است. لطفاً آن را ویرایش کنید."
        )
        
        db.add(sample_config)
        
        # تمپلیت نمونه
        sample_template = ExportTemplate(
            name="تمپلیت نمونه - نوع 1",
            template_type="type1",
            template_path="templates/template_type1.xlsx",
            output_filename_pattern="Sales_Type1_{date}.xlsx",
            column_mappings={
                "date": "تاریخ",
                "customer_name": "نام مشتری",
                "amount": "مبلغ",
                "description": "توضیحات"
            },
            target_worksheet="Sheet1",
            start_row=2,
            start_column=1,
            is_active=False,  # غیرفعال به طور پیش‌فرض
            description="این یک تمپلیت نمونه است."
        )
        
        db.add(sample_template)
        
        db.commit()
        db.close()
        
        print("✅ داده‌های نمونه افزوده شدند.")
        print("⚠️  توجه: داده‌های نمونه غیرفعال هستند. از طریق برنامه آنها را ویرایش کنید.")
        
    except Exception as e:
        print(f"❌ خطا در افزودن داده‌های نمونه: {str(e)}")


def reset_database():
    """بازنشانی دیتابیس (حذف و ایجاد مجدد)"""
    confirm = input("\n⚠️  هشدار: این عملیات تمام داده‌ها را حذف می‌کند. ادامه می‌دهید؟ (yes/no): ")
    
    if confirm.lower() == 'yes':
        print("\n🗑️  در حال حذف جداول...")
        drop_db()
        print("✅ جداول حذف شدند.")
        
        print("\n🔧 در حال ایجاد مجدد جداول...")
        init_db()
        print("✅ جداول مجدداً ایجاد شدند.")
    else:
        print("❌ عملیات لغو شد.")


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 GT-Land Manager - راه‌اندازی دیتابیس")
    print("=" * 60)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        reset_database()
    else:
        setup_database()
