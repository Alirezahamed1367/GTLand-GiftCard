"""
Migration: اضافه کردن فیلدهای Transfer Tracking به جدول raw_data
================================================================
"""
from sqlalchemy import text
from app.models.financial import get_financial_session, financial_engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate():
    """اضافه کردن ستون‌های جدید"""
    
    session = get_financial_session()
    
    try:
        # بررسی اینکه آیا ستون‌ها قبلاً اضافه شده‌اند
        result = session.execute(text("PRAGMA table_info(raw_data)"))
        columns = [row[1] for row in result.fetchall()]
        
        logger.info(f"ستون‌های موجود: {columns}")
        
        # اضافه کردن ستون‌های جدید (فقط اگر وجود نداشته باشند)
        new_columns = {
            'transferred': 'INTEGER DEFAULT 0',
            'transferred_at': 'DATETIME',
            'transfer_status': "TEXT DEFAULT 'pending'",
            'transfer_error': 'TEXT'
        }
        
        for col_name, col_type in new_columns.items():
            if col_name not in columns:
                logger.info(f"اضافه کردن ستون: {col_name}")
                session.execute(text(f"ALTER TABLE raw_data ADD COLUMN {col_name} {col_type}"))
                session.commit()
                logger.info(f"✅ ستون {col_name} اضافه شد")
            else:
                logger.info(f"⏭️ ستون {col_name} قبلاً وجود دارد")
        
        # بروزرسانی داده‌های قدیمی
        logger.info("بروزرسانی داده‌های قدیمی...")
        
        # داده‌هایی که processed=True دارند را به عنوان transferred علامت‌گذاری می‌کنیم
        session.execute(text("""
            UPDATE raw_data 
            SET transferred = 1, 
                transfer_status = 'TRANSFERRED',
                transferred_at = CURRENT_TIMESTAMP
            WHERE processed = 1 AND transferred = 0
        """))
        session.commit()
        
        updated = session.execute(text("SELECT COUNT(*) FROM raw_data WHERE transferred = 1")).scalar()
        logger.info(f"✅ {updated} رکورد به عنوان transferred علامت‌گذاری شد")
        
        logger.info("✅ Migration با موفقیت انجام شد!")
        
    except Exception as e:
        logger.error(f"❌ خطا در Migration: {e}")
        session.rollback()
        raise
    
    finally:
        session.close()


if __name__ == "__main__":
    logger.info("شروع Migration...")
    migrate()
    logger.info("پایان Migration")
