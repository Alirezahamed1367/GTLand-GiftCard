"""
Data Importer - واسط بین Google Sheets و Dynamic System
این ماژول داده‌های خام را از Google Sheets دریافت و در SheetImport/RawData ذخیره می‌کند
"""
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime
import json

from app.core.google_sheets import GoogleSheetExtractor
from app.models.financial import SheetImport, RawData, SheetType
from app.core.logger import app_logger


class DataImporter:
    """کلاس import داده از Google Sheets به سیستم دینامیک"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.logger = app_logger
        self.sheet_extractor = GoogleSheetExtractor()
    
    def import_from_google_sheet(
        self,
        sheet_url: str,
        worksheet_name: str,
        sheet_name: str,
        sheet_type: SheetType,
        platform: Optional[str] = None,
        skip_header: bool = True
    ) -> Tuple[bool, str, Optional[int]]:
        """
        Import داده از Google Sheet
        
        Args:
            sheet_url: آدرس Google Sheet
            worksheet_name: نام worksheet
            sheet_name: نام دلخواه برای این import
            sheet_type: نوع شیت (PURCHASE/SALE/BONUS)
            platform: پلتفرم (فقط برای SALE ضروری است)
            skip_header: آیا سطر اول را نادیده بگیرد؟
        
        Returns:
            (success, message, sheet_import_id)
        """
        try:
            # بررسی platform برای SALE
            if sheet_type == SheetType.SALE and not platform:
                return False, "❌ برای شیت فروش، تعیین platform الزامی است!", None
            
            self.logger.info(f"🔄 شروع import از '{worksheet_name}'...")
            
            # دریافت تمام داده‌ها
            all_data = self.sheet_extractor.get_all_data(sheet_url, worksheet_name)
            
            if not all_data:
                return False, "❌ هیچ داده‌ای در worksheet یافت نشد!", None
            
            # حذف هدر اگر لازم باشد
            start_row = 1 if skip_header else 0
            data_rows = all_data[start_row:]
            
            if not data_rows:
                return False, "❌ بعد از حذف هدر، هیچ داده‌ای باقی نماند!", None
            
            # دریافت headers
            headers = all_data[0] if all_data else []
            
            # ایجاد SheetImport
            sheet_import = SheetImport(
                sheet_name=sheet_name,
                sheet_type=sheet_type,
                platform=platform,
                source_url=sheet_url,
                total_rows=len(data_rows),
                processed_rows=0,
                import_date=datetime.now(),
                notes=f"Imported from worksheet: {worksheet_name}"
            )
            self.db.add(sheet_import)
            self.db.flush()  # برای گرفتن ID
            
            self.logger.info(f"📊 SheetImport ایجاد شد با ID: {sheet_import.id}")
            
            # ذخیره هر سطر به عنوان RawData
            raw_data_list = []
            for idx, row in enumerate(data_rows, start=1):
                # تبدیل row به dictionary با استفاده از headers
                row_dict = {}
                for col_idx, value in enumerate(row):
                    if col_idx < len(headers):
                        col_name = headers[col_idx]
                        row_dict[col_name] = value
                    else:
                        # اگر ستونی header نداشت
                        row_dict[f"Column_{col_idx + 1}"] = value
                
                raw_data = RawData(
                    sheet_import_id=sheet_import.id,
                    row_number=idx,
                    data=row_dict,  # SQLAlchemy به صورت خودکار به JSON تبدیل می‌کند
                    processed=False
                )
                raw_data_list.append(raw_data)
            
            self.db.bulk_save_objects(raw_data_list)
            self.db.commit()
            
            success_msg = f"✅ Import موفق: {len(data_rows)} سطر از '{worksheet_name}' ذخیره شد!"
            self.logger.success(success_msg)
            
            return True, success_msg, sheet_import.id
            
        except Exception as e:
            self.db.rollback()
            error_msg = f"❌ خطا در import: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg, None
    
    def get_import_preview(self, sheet_import_id: int, max_rows: int = 5) -> Dict:
        """
        نمایش پیش‌نمایش داده‌های import شده
        
        Returns:
            {
                'sheet_info': {...},
                'columns': [...],
                'sample_rows': [...]
            }
        """
        try:
            sheet_import = self.db.query(SheetImport).filter_by(id=sheet_import_id).first()
            if not sheet_import:
                return {"error": "SheetImport یافت نشد!"}
            
            # دریافت چند سطر نمونه
            sample_rows = self.db.query(RawData)\
                .filter_by(sheet_import_id=sheet_import_id)\
                .order_by(RawData.row_number)\
                .limit(max_rows)\
                .all()
            
            # استخراج نام ستون‌ها
            columns = []
            if sample_rows:
                first_row_data = sample_rows[0].data
                columns = list(first_row_data.keys())
            
            return {
                'sheet_info': {
                    'id': sheet_import.id,
                    'name': sheet_import.sheet_name,
                    'type': sheet_import.sheet_type.value,
                    'platform': sheet_import.platform,
                    'total_rows': sheet_import.total_rows,
                    'processed_rows': sheet_import.processed_rows,
                    'import_date': sheet_import.import_date.strftime('%Y-%m-%d %H:%M')
                },
                'columns': columns,
                'sample_rows': [
                    {
                        'row_number': row.row_number,
                        'data': row.data,
                        'processed': row.processed
                    }
                    for row in sample_rows
                ]
            }
            
        except Exception as e:
            self.logger.error(f"خطا در دریافت پیش‌نمایش: {str(e)}")
            return {"error": str(e)}
    
    def get_all_imports(self) -> List[Dict]:
        """لیست تمام importهای انجام شده"""
        try:
            imports = self.db.query(SheetImport)\
                .order_by(SheetImport.import_date.desc())\
                .all()
            
            return [
                {
                    'id': imp.id,
                    'name': imp.sheet_name,
                    'type': imp.sheet_type.value,
                    'platform': imp.platform,
                    'total_rows': imp.total_rows,
                    'processed_rows': imp.processed_rows,
                    'progress': f"{imp.processed_rows}/{imp.total_rows}",
                    'import_date': imp.import_date.strftime('%Y-%m-%d %H:%M')
                }
                for imp in imports
            ]
        except Exception as e:
            self.logger.error(f"خطا در دریافت لیست imports: {str(e)}")
            return []
