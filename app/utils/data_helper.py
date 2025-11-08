"""
Helper برای خواندن اطلاعات از دیتابیس
"""
from typing import List, Dict, Optional, Set
from collections import Counter
import json

from app.core.database import db_manager
from app.models import SalesData, SheetConfig


class DatabaseColumnInfo:
    """اطلاعات یک ستون دیتابیس"""
    def __init__(self, name: str, sample_value: any = None, data_type: str = None, frequency: int = 0):
        self.name = name
        self.sample_value = sample_value
        self.data_type = data_type
        self.frequency = frequency  # تعداد دفعات ظاهر شدن
    
    def __repr__(self):
        if self.sample_value:
            return f"{self.name} (نمونه: {self.sample_value})"
        return self.name
    
    def to_dict(self):
        return {
            'name': self.name,
            'sample_value': str(self.sample_value) if self.sample_value else None,
            'data_type': self.data_type,
            'frequency': self.frequency
        }


class DataHelper:
    """کلاس کمکی برای کار با داده‌های دیتابیس"""
    
    @staticmethod
    def get_sheet_configs() -> List[Dict]:
        """
        دریافت لیست تمام SheetConfig ها
        
        Returns:
            لیست دیکشنری اطلاعات Sheet ها
        """
        try:
            session = db_manager.get_session()
            configs = session.query(SheetConfig).all()
            
            result = []
            for config in configs:
                # شمارش رکوردها
                record_count = session.query(SalesData)\
                    .filter(SalesData.sheet_config_id == config.id)\
                    .count()
                
                result.append({
                    'id': config.id,
                    'name': config.name,
                    'sheet_url': config.sheet_url,
                    'worksheet_name': config.worksheet_name,
                    'is_active': config.is_active,
                    'record_count': record_count
                })
            
            session.close()
            return result
            
        except Exception as e:
            print(f"خطا در خواندن SheetConfig: {str(e)}")
            return []
    
    @staticmethod
    def get_data_columns(sheet_config_id: int, sample_size: int = 100) -> List[DatabaseColumnInfo]:
        """
        دریافت لیست ستون‌های موجود در data (JSON)
        
        Args:
            sheet_config_id: شناسه SheetConfig
            sample_size: تعداد رکورد برای نمونه‌برداری
            
        Returns:
            لیست اطلاعات ستون‌ها
        """
        try:
            session = db_manager.get_session()
            
            # خواندن نمونه رکوردها
            samples = session.query(SalesData)\
                .filter(SalesData.sheet_config_id == sheet_config_id)\
                .limit(sample_size)\
                .all()
            
            session.close()
            
            if not samples:
                return []
            
            # جمع‌آوری تمام کلیدها
            all_keys = set()
            key_samples = {}  # ذخیره نمونه مقدار برای هر کلید
            key_frequencies = Counter()
            
            for sample in samples:
                if sample.data:
                    for key, value in sample.data.items():
                        all_keys.add(key)
                        key_frequencies[key] += 1
                        
                        # ذخیره اولین مقدار غیر خالی
                        if key not in key_samples or not key_samples[key]:
                            if value and str(value).strip():
                                key_samples[key] = value
            
            # ساخت لیست ستون‌ها
            columns = []
            for key in sorted(all_keys):  # مرتب‌سازی الفبایی
                sample_value = key_samples.get(key)
                data_type = type(sample_value).__name__ if sample_value else 'str'
                frequency = key_frequencies[key]
                
                col_info = DatabaseColumnInfo(
                    name=key,
                    sample_value=sample_value,
                    data_type=data_type,
                    frequency=frequency
                )
                columns.append(col_info)
            
            return columns
            
        except Exception as e:
            print(f"خطا در خواندن ستون‌های data: {str(e)}")
            return []
    
    @staticmethod
    def get_column_values(sheet_config_id: int, column_name: str, limit: int = 10) -> List:
        """
        دریافت نمونه مقادیر یک ستون (برای پیش‌نمایش)
        
        Args:
            sheet_config_id: شناسه SheetConfig
            column_name: نام ستون
            limit: حداکثر تعداد
            
        Returns:
            لیست مقادیر
        """
        try:
            session = db_manager.get_session()
            
            samples = session.query(SalesData)\
                .filter(SalesData.sheet_config_id == sheet_config_id)\
                .limit(limit)\
                .all()
            
            session.close()
            
            values = []
            for sample in samples:
                if sample.data and column_name in sample.data:
                    values.append(sample.data[column_name])
            
            return values
            
        except Exception as e:
            print(f"خطا در خواندن مقادیر: {str(e)}")
            return []
    
    @staticmethod
    def get_data_stats(sheet_config_id: int) -> Dict:
        """
        دریافت آمار داده‌ها برای یک Sheet
        
        Args:
            sheet_config_id: شناسه SheetConfig
            
        Returns:
            دیکشنری آمار
        """
        try:
            session = db_manager.get_session()
            
            total_count = session.query(SalesData)\
                .filter(SalesData.sheet_config_id == sheet_config_id)\
                .count()
            
            exported_count = session.query(SalesData)\
                .filter(
                    SalesData.sheet_config_id == sheet_config_id,
                    SalesData.is_exported == True
                )\
                .count()
            
            updated_count = session.query(SalesData)\
                .filter(
                    SalesData.sheet_config_id == sheet_config_id,
                    SalesData.is_updated == True
                )\
                .count()
            
            # خواندن نمونه برای شمارش ستون‌ها
            sample = session.query(SalesData)\
                .filter(SalesData.sheet_config_id == sheet_config_id)\
                .first()
            
            column_count = len(sample.data.keys()) if sample and sample.data else 0
            
            session.close()
            
            return {
                'total_records': total_count,
                'exported_records': exported_count,
                'updated_records': updated_count,
                'new_records': total_count - exported_count,
                'column_count': column_count,
                'export_percentage': round(exported_count / total_count * 100, 1) if total_count > 0 else 0
            }
            
        except Exception as e:
            print(f"خطا در خواندن آمار: {str(e)}")
            return {}
    
    @staticmethod
    def get_all_unique_columns() -> Set[str]:
        """
        دریافت تمام ستون‌های منحصر به فرد در کل دیتابیس
        
        Returns:
            مجموعه نام ستون‌ها
        """
        try:
            session = db_manager.get_session()
            
            all_data = session.query(SalesData.data).all()
            
            session.close()
            
            columns = set()
            for row in all_data:
                if row.data:
                    columns.update(row.data.keys())
            
            return columns
            
        except Exception as e:
            print(f"خطا در خواندن ستون‌ها: {str(e)}")
            return set()
    
    @staticmethod
    def suggest_mapping(db_columns: List[str], excel_columns: List[str]) -> Dict[str, str]:
        """
        پیشنهاد خودکار Mapping بین ستون‌های دیتابیس و Excel
        
        Args:
            db_columns: لیست ستون‌های دیتابیس
            excel_columns: لیست ستون‌های Excel
            
        Returns:
            دیکشنری Mapping پیشنهادی
        """
        mapping = {}
        
        # تطبیق دقیق
        for db_col in db_columns:
            if db_col in excel_columns:
                mapping[db_col] = db_col
        
        # تطبیق تقریبی (نام‌های مشابه)
        for db_col in db_columns:
            if db_col not in mapping:
                # بررسی شباهت
                db_col_clean = db_col.lower().strip()
                for excel_col in excel_columns:
                    excel_col_clean = excel_col.lower().strip()
                    
                    # شامل بودن
                    if db_col_clean in excel_col_clean or excel_col_clean in db_col_clean:
                        mapping[db_col] = excel_col
                        break
        
        return mapping


# توابع کمکی سریع
def get_sheet_list() -> List[Dict]:
    """تابع سریع برای دریافت لیست Sheet ها"""
    helper = DataHelper()
    return helper.get_sheet_configs()


def get_columns_for_sheet(sheet_id: int) -> List[Dict]:
    """
    تابع سریع برای دریافت ستون‌ها به صورت دیکشنری
    
    Returns:
        لیست دیکشنری ستون‌ها
    """
    helper = DataHelper()
    columns = helper.get_data_columns(sheet_id)
    return [col.to_dict() for col in columns]


def get_sheet_stats(sheet_id: int) -> Dict:
    """تابع سریع برای دریافت آمار"""
    helper = DataHelper()
    return helper.get_data_stats(sheet_id)


if __name__ == "__main__":
    # تست
    print("🧪 تست DataHelper:")
    
    # لیست Sheet ها
    sheets = get_sheet_list()
    print(f"\n📊 تعداد Sheet ها: {len(sheets)}")
    
    for sheet in sheets:
        print(f"\n{'='*50}")
        print(f"📋 {sheet['name']}")
        print(f"   ID: {sheet['id']}")
        print(f"   تعداد رکورد: {sheet['record_count']}")
        print(f"   وضعیت: {'✅ فعال' if sheet['is_active'] else '❌ غیرفعال'}")
        
        # ستون‌ها
        columns = get_columns_for_sheet(sheet['id'])
        print(f"\n   📋 ستون‌ها ({len(columns)}):")
        for col in columns[:10]:  # فقط 10 تای اول
            print(f"      • {col['name']}: {col['sample_value'] or '(خالی)'} ({col['frequency']} بار)")
        
        if len(columns) > 10:
            print(f"      ... و {len(columns) - 10} ستون دیگر")
        
        # آمار
        stats = get_sheet_stats(sheet['id'])
        if stats:
            print(f"\n   📊 آمار:")
            print(f"      کل رکوردها: {stats['total_records']}")
            print(f"      Export شده: {stats['exported_records']} ({stats['export_percentage']}%)")
            print(f"      جدید: {stats['new_records']}")
