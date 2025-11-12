"""
مدیریت دیتابیس - Database Manager
"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Tuple, Any
from datetime import datetime
import traceback

from app.models import (
    SessionLocal, SheetConfig, SalesData, ExportTemplate,
    ProcessLog, ExportLog
)
from app.core.logger import app_logger
from app.utils.constants import ProcessStatus, ProcessType
from app.utils.helpers import generate_unique_key, compare_dicts


class DatabaseManager:
    """
    کلاس مدیریت عملیات دیتابیس
    """
    
    def __init__(self):
        """راه‌اندازی مدیر دیتابیس"""
        self.logger = app_logger
    
    def get_session(self) -> Session:
        """دریافت session جدید"""
        return SessionLocal()
    
    # ==================== Sheet Config ====================
    
    def get_all_sheet_configs(self, active_only: bool = False) -> List[SheetConfig]:
        """
        دریافت تمام تنظیمات شیت‌ها
        
        Args:
            active_only: فقط فعال‌ها
            
        Returns:
            لیست تنظیمات
        """
        try:
            db = self.get_session()
            query = db.query(SheetConfig)
            
            if active_only:
                query = query.filter(SheetConfig.is_active == True)
            
            configs = query.all()
            db.close()
            return configs
            
        except Exception as e:
            self.logger.error(f"خطا در دریافت تنظیمات شیت‌ها: {str(e)}")
            return []
    
    def get_sheet_config(self, config_id: int) -> Optional[SheetConfig]:
        """دریافت یک تنظیمات بر اساس ID"""
        try:
            db = self.get_session()
            config = db.query(SheetConfig).filter_by(id=config_id).first()
            db.close()
            return config
        except Exception as e:
            self.logger.error(f"خطا در دریافت تنظیمات شیت: {str(e)}")
            return None
    
    def get_sheet_config_by_name(self, sheet_name: str) -> Optional[SheetConfig]:
        """دریافت تنظیمات شیت بر اساس نام"""
        try:
            db = self.get_session()
            config = db.query(SheetConfig).filter_by(name=sheet_name).first()
            db.close()
            return config
        except Exception as e:
            self.logger.error(f"خطا در دریافت تنظیمات شیت با نام '{sheet_name}': {str(e)}")
            return None
    
    def create_sheet_config(self, data: Dict) -> Tuple[bool, Optional[SheetConfig], str]:
        """
        ایجاد تنظیمات جدید
        
        Args:
            data: دیکشنری داده‌ها
            
        Returns:
            (موفقیت, شیء تنظیمات, پیام)
        """
        try:
            db = self.get_session()
            
            # بررسی تکراری بودن نام
            existing = db.query(SheetConfig).filter_by(name=data['name']).first()
            if existing:
                db.close()
                return False, None, "نام تنظیمات تکراری است."
            
            # ایجاد رکورد جدید
            config = SheetConfig(**data)
            db.add(config)
            db.commit()
            db.refresh(config)
            
            config_id = config.id
            db.close()
            
            self.logger.log_to_db(
                ProcessType.UPDATE,
                ProcessStatus.SUCCESS,
                f"تنظیمات شیت '{data['name']}' ایجاد شد.",
                details={'config_id': config_id}
            )
            
            return True, config, "تنظیمات با موفقیت ایجاد شد."
            
        except Exception as e:
            self.logger.error(f"خطا در ایجاد تنظیمات: {str(e)}")
            return False, None, f"خطا: {str(e)}"
    
    def update_sheet_config(self, config_id: int, data: Dict) -> Tuple[bool, str]:
        """
        بروزرسانی تنظیمات
        
        Args:
            config_id: شناسه تنظیمات
            data: داده‌های جدید
            
        Returns:
            (موفقیت, پیام)
        """
        try:
            db = self.get_session()
            
            config = db.query(SheetConfig).filter_by(id=config_id).first()
            if not config:
                db.close()
                return False, "تنظیمات یافت نشد."
            
            # بروزرسانی فیلدها
            for key, value in data.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            
            config.updated_at = datetime.now()
            db.commit()
            db.close()
            
            self.logger.log_to_db(
                ProcessType.UPDATE,
                ProcessStatus.SUCCESS,
                f"تنظیمات شیت '{config.name}' بروزرسانی شد.",
                details={'config_id': config_id}
            )
            
            return True, "تنظیمات با موفقیت بروزرسانی شد."
            
        except Exception as e:
            self.logger.error(f"خطا در بروزرسانی تنظیمات: {str(e)}")
            return False, f"خطا: {str(e)}"
    
    def delete_sheet_config(self, config_id: int) -> Tuple[bool, str]:
        """حذف تنظیمات"""
        try:
            db = self.get_session()
            
            config = db.query(SheetConfig).filter_by(id=config_id).first()
            if not config:
                db.close()
                return False, "تنظیمات یافت نشد."
            
            config_name = config.name
            db.delete(config)
            db.commit()
            db.close()
            
            self.logger.log_to_db(
                ProcessType.DELETE,
                ProcessStatus.SUCCESS,
                f"تنظیمات شیت '{config_name}' حذف شد."
            )
            
            return True, "تنظیمات با موفقیت حذف شد."
            
        except Exception as e:
            self.logger.error(f"خطا در حذف تنظیمات: {str(e)}")
            return False, f"خطا: {str(e)}"
    
    # ==================== Sales Data ====================
    
    def save_sales_data(
        self,
        sheet_config_id: int,
        row_number: int,
        unique_key: str,
        data: Dict,
        update_if_exists: bool = False
    ) -> Tuple[bool, Optional[SalesData], bool, str]:
        """
        ذخیره داده فروش
        
        Args:
            sheet_config_id: شناسه تنظیمات
            row_number: شماره ردیف
            unique_key: کلید یکتا
            data: داده‌ها
            update_if_exists: بروزرسانی در صورت وجود
            
        Returns:
            (موفقیت, رکورد, جدید بودن, پیام)
        """
        try:
            db = self.get_session()
            
            # جستجوی رکورد موجود
            existing = db.query(SalesData).filter_by(unique_key=unique_key).first()
            
            if existing:
                if update_if_exists:
                    # بروزرسانی
                    existing.data = data
                    existing.row_number = row_number
                    existing.is_updated = True
                    existing.update_count += 1
                    existing.updated_at = datetime.now()
                    
                    db.commit()
                    db.refresh(existing)
                    db.close()
                    
                    return True, existing, False, "داده بروزرسانی شد."
                else:
                    db.close()
                    return False, existing, False, "داده تکراری شناسایی شد."
            
            # ایجاد رکورد جدید
            new_record = SalesData(
                sheet_config_id=sheet_config_id,
                row_number=row_number,
                unique_key=unique_key,
                data=data
            )
            
            db.add(new_record)
            db.commit()
            db.refresh(new_record)
            db.close()
            
            return True, new_record, True, "داده ذخیره شد."
            
        except Exception as e:
            self.logger.error(f"خطا در ذخیره داده: {str(e)}")
            return False, None, False, f"خطا: {str(e)}"
    
    def get_unexported_data(
        self,
        export_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[SalesData]:
        """
        دریافت داده‌های خروجی نگرفته
        
        Args:
            export_type: نوع خروجی
            limit: محدودیت تعداد
            
        Returns:
            لیست داده‌ها
        """
        try:
            db = self.get_session()
            
            query = db.query(SalesData).filter(SalesData.is_exported == False)
            
            if export_type:
                query = query.filter(
                    or_(
                        SalesData.export_type == None,
                        SalesData.export_type != export_type
                    )
                )
            
            if limit:
                query = query.limit(limit)
            
            data = query.all()
            db.close()
            return data
            
        except Exception as e:
            self.logger.error(f"خطا در دریافت داده‌های خروجی نگرفته: {str(e)}")
            return []
    
    def mark_as_exported(
        self,
        data_ids: List[int],
        export_type: str
    ) -> Tuple[bool, str]:
        """
        علامت‌گذاری به عنوان خروجی گرفته شده
        
        Args:
            data_ids: لیست آی‌دی‌ها
            export_type: نوع خروجی
            
        Returns:
            (موفقیت, پیام)
        """
        try:
            db = self.get_session()
            
            db.query(SalesData).filter(SalesData.id.in_(data_ids)).update({
                'is_exported': True,
                'export_type': export_type,
                'exported_at': datetime.now()
            }, synchronize_session=False)
            
            db.commit()
            db.close()
            
            return True, f"{len(data_ids)} رکورد علامت‌گذاری شد."
            
        except Exception as e:
            self.logger.error(f"خطا در علامت‌گذاری: {str(e)}")
            return False, f"خطا: {str(e)}"
    
    # ==================== Sales Data Queries ====================
    
    def get_all_sales_data(self) -> List[SalesData]:
        """دریافت تمام داده‌های فروش"""
        try:
            db = self.get_session()
            data = db.query(SalesData).options(joinedload(SalesData.sheet_config)).order_by(SalesData.extracted_at.desc()).all()
            
            # Force load all attributes before closing session
            for item in data:
                _ = item.data
                if item.sheet_config:
                    _ = item.sheet_config.name
            
            # Detach from session
            db.expunge_all()
            db.close()
            return data
        except Exception as e:
            self.logger.error(f"خطا در دریافت داده‌ها: {str(e)}")
            return []
    
    def get_sales_data_by_export_status(self, is_exported: bool) -> List[SalesData]:
        """دریافت داده‌ها بر اساس وضعیت Export"""
        try:
            db = self.get_session()
            data = db.query(SalesData).options(joinedload(SalesData.sheet_config)).filter_by(is_exported=is_exported).order_by(SalesData.extracted_at.desc()).all()
            
            # Force load all attributes before closing session
            for item in data:
                _ = item.data
                if item.sheet_config:
                    _ = item.sheet_config.name
            
            # Detach from session
            db.expunge_all()
            db.close()
            return data
        except Exception as e:
            self.logger.error(f"خطا در دریافت داده‌ها: {str(e)}")
            return []
    
    def get_sales_data_by_unique_key(self, unique_key: str) -> Optional[SalesData]:
        """دریافت داده بر اساس کلید یکتا"""
        try:
            db = self.get_session()
            data = db.query(SalesData).filter_by(unique_key=unique_key).first()
            
            if data:
                # Force load attributes
                _ = data.data
                if data.sheet_config:
                    _ = data.sheet_config.name
                
                # Detach from session
                db.expunge(data)
            
            db.close()
            return data
        except Exception as e:
            self.logger.error(f"خطا در دریافت داده: {str(e)}")
            return None
    
    def get_updated_sales_data(self) -> List[SalesData]:
        """دریافت داده‌های ویرایش شده (نیاز به Re-export)"""
        try:
            db = self.get_session()
            data = db.query(SalesData).options(joinedload(SalesData.sheet_config)).filter_by(is_updated=True).order_by(SalesData.updated_at.desc()).all()
            
            # Force load all attributes before closing session
            for item in data:
                _ = item.data
                if item.sheet_config:
                    _ = item.sheet_config.name
            
            # Detach from session
            db.expunge_all()
            db.close()
            return data
        except Exception as e:
            self.logger.error(f"خطا در دریافت داده‌ها: {str(e)}")
            return []
    
    def get_sales_data_by_id(self, data_id: int) -> Optional[SalesData]:
        """دریافت یک رکورد بر اساس ID"""
        try:
            db = self.get_session()
            data = db.query(SalesData).options(joinedload(SalesData.sheet_config)).filter_by(id=data_id).first()
            
            if data:
                # Force load all attributes before closing session
                _ = data.data
                if data.sheet_config:
                    _ = data.sheet_config.name
                
                # Detach from session
                db.expunge(data)
            
            db.close()
            return data
        except Exception as e:
            self.logger.error(f"خطا در دریافت داده: {str(e)}")
            return None
    
    def get_sales_data_by_sheet_config(self, sheet_config_id: int) -> List[SalesData]:
        """دریافت تمام رکوردهای یک شیت"""
        try:
            db = self.get_session()
            data_list = db.query(SalesData).filter_by(sheet_config_id=sheet_config_id).all()
            
            # Force load and detach
            result = []
            for data in data_list:
                _ = data.data
                db.expunge(data)
                result.append(data)
            
            db.close()
            return result
        except Exception as e:
            self.logger.error(f"خطا در دریافت داده‌های شیت: {str(e)}")
            return []
    
    def get_sales_data_by_unique_key(self, unique_key: str) -> Optional[SalesData]:
        """دریافت یک رکورد بر اساس Unique Key"""
        try:
            db = self.get_session()
            data = db.query(SalesData).options(joinedload(SalesData.sheet_config)).filter_by(unique_key=unique_key).first()
            
            if data:
                # Force load all attributes
                _ = data.data
                if data.sheet_config:
                    _ = data.sheet_config.name
                
                # Detach from session
                db.expunge(data)
            
            db.close()
            return data
        except Exception as e:
            self.logger.error(f"خطا در دریافت داده: {str(e)}")
            return None
    
    def get_sales_data_count(self, is_exported: Optional[bool] = None) -> int:
        """شمارش داده‌ها"""
        try:
            db = self.get_session()
            query = db.query(SalesData)
            if is_exported is not None:
                query = query.filter_by(is_exported=is_exported)
            count = query.count()
            db.close()
            return count
        except Exception as e:
            self.logger.error(f"خطا در شمارش: {str(e)}")
            return 0
    
    # 🚀 Paginated Methods برای سرعت بالا
    
    def get_all_sales_data_paginated(
        self, 
        limit: int = 100, 
        offset: int = 0,
        sheet_config_id: Optional[int] = None
    ) -> Tuple[List[SalesData], int]:
        """دریافت داده‌ها با pagination"""
        try:
            db = self.get_session()
            
            query = db.query(SalesData).options(joinedload(SalesData.sheet_config))
            
            if sheet_config_id is not None:
                query = query.filter_by(sheet_config_id=sheet_config_id)
            
            # شمارش کل
            total = query.count()
            
            # دریافت صفحه فعلی
            data_list = query.order_by(SalesData.id.desc()).limit(limit).offset(offset).all()
            
            # Force load and detach
            result = []
            for data in data_list:
                _ = data.data
                if data.sheet_config:
                    _ = data.sheet_config.name
                db.expunge(data)
                result.append(data)
            
            db.close()
            return result, total
        except Exception as e:
            self.logger.error(f"خطا در دریافت داده‌ها (paginated): {str(e)}")
            return [], 0
    
    def get_sales_data_by_export_status_paginated(
        self,
        is_exported: bool,
        limit: int = 100,
        offset: int = 0,
        sheet_config_id: Optional[int] = None
    ) -> Tuple[List[SalesData], int]:
        """دریافت داده‌ها بر اساس وضعیت Export با pagination"""
        try:
            db = self.get_session()
            
            query = db.query(SalesData).options(joinedload(SalesData.sheet_config)).filter_by(is_exported=is_exported)
            
            if sheet_config_id is not None:
                query = query.filter_by(sheet_config_id=sheet_config_id)
            
            total = query.count()
            data_list = query.order_by(SalesData.id.desc()).limit(limit).offset(offset).all()
            
            result = []
            for data in data_list:
                _ = data.data
                if data.sheet_config:
                    _ = data.sheet_config.name
                db.expunge(data)
                result.append(data)
            
            db.close()
            return result, total
        except Exception as e:
            self.logger.error(f"خطا در دریافت داده‌ها (paginated): {str(e)}")
            return [], 0
    
    def get_updated_sales_data_paginated(
        self,
        limit: int = 100,
        offset: int = 0,
        sheet_config_id: Optional[int] = None
    ) -> Tuple[List[SalesData], int]:
        """دریافت داده‌های ویرایش شده با pagination"""
        try:
            db = self.get_session()
            
            query = db.query(SalesData).options(joinedload(SalesData.sheet_config)).filter_by(is_updated=True)
            
            if sheet_config_id is not None:
                query = query.filter_by(sheet_config_id=sheet_config_id)
            
            total = query.count()
            data_list = query.order_by(SalesData.id.desc()).limit(limit).offset(offset).all()
            
            result = []
            for data in data_list:
                _ = data.data
                if data.sheet_config:
                    _ = data.sheet_config.name
                db.expunge(data)
                result.append(data)
            
            db.close()
            return result, total
        except Exception as e:
            self.logger.error(f"خطا در دریافت داده‌ها (paginated): {str(e)}")
            return [], 0
    
    def get_updated_sales_data_count(self) -> int:
        """شمارش داده‌های ویرایش شده"""
        try:
            db = self.get_session()
            count = db.query(SalesData).filter_by(is_updated=True).count()
            db.close()
            return count
        except Exception as e:
            self.logger.error(f"خطا در شمارش: {str(e)}")
            return 0
    
    def get_sheet_statistics(self, sheet_config_id: int) -> Dict:
        """
        دریافت آمار کامل یک شیت
        
        Args:
            sheet_config_id: شناسه شیت
            
        Returns:
            {
                'name': 'نام شیت',
                'total': تعداد کل,
                'exported': export شده,
                'not_exported': export نشده,
                'need_reexport': نیاز به re-export,
                'last_extract': آخرین استخراج
            }
        """
        try:
            db = self.get_session()
            
            # دریافت نام شیت
            sheet_config = db.query(SheetConfig).filter_by(id=sheet_config_id).first()
            sheet_name = sheet_config.name if sheet_config else "نامشخص"
            
            # آمار کلی
            total = db.query(SalesData).filter_by(sheet_config_id=sheet_config_id).count()
            
            # Export شده
            exported = db.query(SalesData).filter_by(
                sheet_config_id=sheet_config_id,
                is_exported=True
            ).count()
            
            # Export نشده
            not_exported = db.query(SalesData).filter_by(
                sheet_config_id=sheet_config_id,
                is_exported=False
            ).count()
            
            # نیاز به Re-export (export شده ولی update شده)
            need_reexport = db.query(SalesData).filter_by(
                sheet_config_id=sheet_config_id,
                is_exported=True,
                is_updated=True
            ).count()
            
            # آخرین استخراج
            last_data = db.query(SalesData).filter_by(
                sheet_config_id=sheet_config_id
            ).order_by(SalesData.extracted_at.desc()).first()
            
            last_extract = last_data.extracted_at if last_data else None
            
            db.close()
            
            return {
                'sheet_config_id': sheet_config_id,
                'name': sheet_name,
                'total': total,
                'exported': exported,
                'not_exported': not_exported,
                'need_reexport': need_reexport,
                'last_extract': last_extract
            }
            
        except Exception as e:
            self.logger.error(f"خطا در دریافت آمار شیت: {str(e)}")
            return {
                'sheet_config_id': sheet_config_id,
                'name': "خطا",
                'total': 0,
                'exported': 0,
                'not_exported': 0,
                'need_reexport': 0,
                'last_extract': None
            }
    
    def get_all_sheets_statistics(self) -> List[Dict]:
        """دریافت آمار همه شیت‌ها"""
        try:
            db = self.get_session()
            
            # شیت‌هایی که داده دارند
            sheet_ids = db.query(SalesData.sheet_config_id).distinct().all()
            sheet_ids = [sid[0] for sid in sheet_ids]
            
            db.close()
            
            stats = []
            for sheet_id in sheet_ids:
                stat = self.get_sheet_statistics(sheet_id)
                if stat['total'] > 0:
                    stats.append(stat)
            
            # مرتب‌سازی بر اساس تعداد (بیشترین اول)
            stats.sort(key=lambda x: x['total'], reverse=True)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"خطا در دریافت آمار همه شیت‌ها: {str(e)}")
            return []
    
    def delete_sales_data(self, data_id: int) -> Tuple[bool, str]:
        """حذف یک رکورد"""
        try:
            db = self.get_session()
            data = db.query(SalesData).filter_by(id=data_id).first()
            if data:
                db.delete(data)
                db.commit()
                db.close()
                return True, "رکورد حذف شد"
            db.close()
            return False, "رکورد یافت نشد"
        except Exception as e:
            self.logger.error(f"خطا در حذف: {str(e)}")
            return False, str(e)
    
    def delete_sheet_data(self, sheet_config_id: int) -> Tuple[bool, str]:
        """
        حذف تمام داده‌های یک شیت (بدون حذف تنظیمات شیت)
        
        Args:
            sheet_config_id: شناسه تنظیمات شیت
            
        Returns:
            (موفقیت, پیام)
        """
        try:
            db = self.get_session()
            
            # شمارش رکوردها قبل از حذف
            count = db.query(SalesData).filter_by(sheet_config_id=sheet_config_id).count()
            
            if count == 0:
                db.close()
                return True, "هیچ داده‌ای برای حذف وجود ندارد"
            
            # حذف تمام داده‌های شیت
            db.query(SalesData).filter_by(sheet_config_id=sheet_config_id).delete()
            db.commit()
            db.close()
            
            self.logger.log_to_db(
                ProcessType.DELETE,
                ProcessStatus.SUCCESS,
                f"تمام داده‌های شیت (تعداد: {count}) حذف شدند"
            )
            
            return True, f"{count} رکورد حذف شد"
            
        except Exception as e:
            self.logger.error(f"خطا در حذف داده‌های شیت: {str(e)}")
            return False, f"خطا: {str(e)}"
    
    def update_sales_data(self, data_id: int, update_data: Dict) -> bool:
        """بروزرسانی یک رکورد"""
        try:
            db = self.get_session()
            db.query(SalesData).filter_by(id=data_id).update(update_data)
            db.commit()
            db.close()
            return True
        except Exception as e:
            self.logger.error(f"خطا در بروزرسانی: {str(e)}")
            return False
    
    # ==================== Export Template Management ====================
    
    def create_export_template(self, data: Dict) -> bool:
        """ایجاد Template جدید"""
        try:
            db = self.get_session()
            template = ExportTemplate(**data)
            db.add(template)
            db.commit()
            db.close()
            return True
        except Exception as e:
            self.logger.error(f"خطا در ایجاد Template: {str(e)}")
            return False
    
    def update_export_template(self, template_id: int, data: Dict) -> bool:
        """بروزرسانی Template"""
        try:
            db = self.get_session()
            db.query(ExportTemplate).filter_by(id=template_id).update(data)
            db.commit()
            db.close()
            return True
        except Exception as e:
            self.logger.error(f"خطا در بروزرسانی Template: {str(e)}")
            return False
    
    def get_all_export_templates(self, active_only: bool = False) -> List[ExportTemplate]:
        """دریافت تمام Template ها"""
        try:
            db = self.get_session()
            query = db.query(ExportTemplate)
            if active_only:
                query = query.filter_by(is_active=True)
            templates = query.all()
            db.close()
            return templates
        except Exception as e:
            self.logger.error(f"خطا در دریافت Template ها: {str(e)}")
            return []
    
    def delete_export_template(self, template_id: int) -> Tuple[bool, str]:
        """حذف Template"""
        try:
            db = self.get_session()
            template = db.query(ExportTemplate).filter_by(id=template_id).first()
            if template:
                db.delete(template)
                db.commit()
                db.close()
                return True, "Template حذف شد"
            db.close()
            return False, "Template یافت نشد"
        except Exception as e:
            self.logger.error(f"خطا در حذف: {str(e)}")
            return False, str(e)
    
    # ==================== Statistics ====================
    
    def get_statistics(self) -> Dict:
        """دریافت آمار کلی"""
        try:
            db = self.get_session()
            
            stats = {
                'total_configs': db.query(SheetConfig).count(),
                'active_configs': db.query(SheetConfig).filter_by(is_active=True).count(),
                'total_records': db.query(SalesData).count(),
                'exported_records': db.query(SalesData).filter_by(is_exported=True).count(),
                'pending_records': db.query(SalesData).filter_by(is_exported=False).count(),
                'updated_records': db.query(SalesData).filter_by(is_updated=True).count(),
                'total_templates': db.query(ExportTemplate).count(),
                'active_templates': db.query(ExportTemplate).filter_by(is_active=True).count(),
                'total_exports': db.query(ExportLog).count(),
            }
            
            db.close()
            return stats
            
        except Exception as e:
            self.logger.error(f"خطا در دریافت آمار: {str(e)}")
            return {}
    
    # ==================== Export Template Management ====================
    
    def get_all_templates(self, active_only: bool = False) -> List[ExportTemplate]:
        """دریافت تمام Template ها"""
        try:
            db = self.get_session()
            query = db.query(ExportTemplate)
            
            if active_only:
                query = query.filter(ExportTemplate.is_active == True)
            
            templates = query.all()
            db.close()
            return templates
        
        except Exception as e:
            self.logger.error(f"Error getting templates: {e}")
            return []
    
    def get_template(self, template_id: int) -> Optional[ExportTemplate]:
        """دریافت یک Template"""
        try:
            db = self.get_session()
            template = db.query(ExportTemplate).filter_by(id=template_id).first()
            db.close()
            return template
        
        except Exception as e:
            self.logger.error(f"Error getting template: {e}")
            return None
    
    def create_template(self, data: Dict) -> Tuple[bool, Optional[ExportTemplate], str]:
        """ساخت Template جدید"""
        try:
            db = self.get_session()
            
            # بررسی تکراری
            existing = db.query(ExportTemplate).filter_by(name=data['name']).first()
            if existing:
                db.close()
                return False, None, "Template با این نام قبلاً ثبت شده است"
            
            # ساخت Template
            template = ExportTemplate(**data)
            db.add(template)
            db.commit()
            db.refresh(template)
            
            self.logger.success(f"Template created: {template.name}")
            db.close()
            return True, template, "Template با موفقیت ایجاد شد"
        
        except Exception as e:
            self.logger.error(f"Error creating template: {e}")
            return False, None, str(e)
    
    def update_template(self, template_id: int, data: Dict) -> Tuple[bool, str]:
        """به‌روزرسانی Template"""
        try:
            db = self.get_session()
            
            template = db.query(ExportTemplate).filter_by(id=template_id).first()
            if not template:
                db.close()
                return False, "Template پیدا نشد"
            
            # به‌روزرسانی
            for key, value in data.items():
                if hasattr(template, key):
                    setattr(template, key, value)
            
            db.commit()
            self.logger.success(f"Template updated: {template.name}")
            db.close()
            return True, "Template با موفقیت به‌روزرسانی شد"
        
        except Exception as e:
            self.logger.error(f"Error updating template: {e}")
            return False, str(e)
    
    def delete_template(self, template_id: int) -> Tuple[bool, str]:
        """حذف Template"""
        try:
            db = self.get_session()
            
            template = db.query(ExportTemplate).filter_by(id=template_id).first()
            if not template:
                db.close()
                return False, "Template پیدا نشد"
            
            name = template.name
            db.delete(template)
            db.commit()
            
            self.logger.success(f"Template deleted: {name}")
            db.close()
            return True, "Template با موفقیت حذف شد"
        
        except Exception as e:
            self.logger.error(f"Error deleting template: {e}")
            return False, str(e)


# نمونه سراسری
db_manager = DatabaseManager()
