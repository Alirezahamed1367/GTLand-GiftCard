# Google Sheets Extractor
import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict, Optional, Tuple
from tenacity import retry, stop_after_attempt, wait_exponential
import time

from app.core.logger import app_logger
from app.utils.constants import ERROR_MESSAGES, SUCCESS_MESSAGES
from app.utils.helpers import validate_google_sheet_url
from app.utils.cell_status_detector import is_cell_checked, is_cell_extracted

def column_letter_to_index(column_letter):
    column_letter = column_letter.upper().strip()
    result = 0
    for char in column_letter:
        result = result * 26 + (ord(char) - ord('A') + 1)
    return result - 1

class GoogleSheetExtractor:
    def __init__(self, credentials_path=None):
        import os
        self.logger = app_logger
        self.credentials_path = credentials_path or os.getenv("GOOGLE_CREDENTIALS_PATH", "config/credentials.json")
        self.client = None
        self._connect()
    
    def _connect(self):
        try:
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive",
                "https://www.googleapis.com/auth/spreadsheets"
            ]
            creds = Credentials.from_service_account_file(self.credentials_path, scopes=scope)
            self.client = gspread.authorize(creds)
            self.logger.success("اتصال به Google Sheets برقرار شد.")
        except FileNotFoundError:
            self.logger.error(f"فایل credentials یافت نشد: {self.credentials_path}")
            raise Exception(ERROR_MESSAGES["GOOGLE_SHEETS_AUTH_FAILED"])
        except Exception as e:
            self.logger.error(f"خطا در احراز هویت Google Sheets: {str(e)}")
            raise Exception(ERROR_MESSAGES["GOOGLE_SHEETS_AUTH_FAILED"])
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def test_connection(self, sheet_url):
        try:
            if not validate_google_sheet_url(sheet_url):
                return False, ERROR_MESSAGES["INVALID_SHEET_URL"]
            sheet = self.client.open_by_url(sheet_url)
            worksheets = sheet.worksheets()
            return True, f"اتصال موفق. تعداد ورک‌شیت‌ها: {len(worksheets)}"
        except gspread.exceptions.SpreadsheetNotFound:
            return False, ERROR_MESSAGES["SHEET_NOT_FOUND"]
        except gspread.exceptions.APIError as e:
            if "PERMISSION_DENIED" in str(e):
                return False, ERROR_MESSAGES["PERMISSION_DENIED"]
            return False, f"خطا در دسترسی به شیت: {str(e)}"
        except Exception as e:
            return False, f"خطا: {str(e)}"
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_worksheets(self, sheet_url):
        try:
            sheet = self.client.open_by_url(sheet_url)
            return [ws.title for ws in sheet.worksheets()]
        except Exception as e:
            self.logger.error(f"خطا در دریافت ورک‌شیت‌ها: {str(e)}")
            return []
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_headers(self, sheet_url, worksheet_name=None):
        try:
            sheet = self.client.open_by_url(sheet_url)
            worksheet = sheet.worksheet(worksheet_name) if worksheet_name else sheet.sheet1
            return worksheet.row_values(1)
        except Exception as e:
            self.logger.error(f"خطا در دریافت هدرها: {str(e)}")
            return []
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def extract_ready_rows(self, sheet_url, worksheet_name, ready_column, extracted_column, columns_to_extract=None, skip_rows=0, max_rows=None):
        try:
            self.logger.info(f"📄 در حال باز کردن worksheet: '{worksheet_name}'")
            sheet = self.client.open_by_url(sheet_url)
            
            # لیست تمام worksheetها را لاگ کن
            all_worksheets = [ws.title for ws in sheet.worksheets()]
            self.logger.info(f"📋 لیست worksheetهای موجود: {all_worksheets}")
            
            # جستجوی case-insensitive برای worksheet
            if worksheet_name:
                # سعی کن نام دقیق را پیدا کنی
                matching_ws = None
                for ws in sheet.worksheets():
                    if ws.title.lower() == worksheet_name.lower():
                        matching_ws = ws
                        break
                
                if matching_ws:
                    worksheet = matching_ws
                    if matching_ws.title != worksheet_name:
                        self.logger.warning(f"⚠️ نام worksheet در دیتابیس '{worksheet_name}' با نام واقعی '{matching_ws.title}' متفاوت است")
                else:
                    raise Exception(f"Worksheet با نام '{worksheet_name}' یافت نشد. worksheetهای موجود: {all_worksheets}")
            else:
                worksheet = sheet.sheet1
            
            self.logger.info(f"✅ Worksheet '{worksheet.title}' باز شد")
            all_values = worksheet.get_all_values()
            if not all_values or len(all_values) < 2:
                self.logger.warning("شیت خالی است یا فقط هدر دارد")
                return []
            headers = all_values[0]
            self.logger.info(f"📊 هدرهای یافت شده: {headers}")
            self.logger.info(f"تعداد کل ردیف‌ها: {len(all_values) - 1}")
            
            # پیدا کردن ستون آماده (Ready) با جستجوی هوشمند
            try:
                ready_col_idx = column_letter_to_index(ready_column)
                self.logger.info(f"✅ ستون آماده از طریق حرف: {ready_column} -> index {ready_col_idx}")
            except:
                # جستجوی case-insensitive و trim شده
                ready_col_idx = -1
                ready_column_lower = ready_column.strip().lower()
                
                for idx, header in enumerate(headers):
                    header_clean = str(header).strip().lower()
                    if header_clean == ready_column_lower:
                        ready_col_idx = idx
                        self.logger.info(f"✅ ستون آماده پیدا شد: '{header}' (index {idx})")
                        break
                
                if ready_col_idx == -1:
                    self.logger.error(f"❌ ستون آماده '{ready_column}' یافت نشد!")
                    self.logger.error(f"📋 هدرهای موجود: {headers}")
                    return []
            
            # پیدا کردن ستون استخراج شده (Extracted) با جستجوی هوشمند
            try:
                extracted_col_idx = column_letter_to_index(extracted_column)
                self.logger.info(f"✅ ستون استخراج از طریق حرف: {extracted_column} -> index {extracted_col_idx}")
            except:
                # جستجوی case-insensitive و trim شده
                extracted_col_idx = -1
                extracted_column_lower = extracted_column.strip().lower()
                
                for idx, header in enumerate(headers):
                    header_clean = str(header).strip().lower()
                    if header_clean == extracted_column_lower:
                        extracted_col_idx = idx
                        self.logger.info(f"✅ ستون استخراج پیدا شد: '{header}' (index {idx})")
                        break
                
                if extracted_col_idx == -1:
                    self.logger.error(f"❌ ستون استخراج '{extracted_column}' یافت نشد!")
                    self.logger.error(f"📋 هدرهای موجود: {headers}")
                    return []
            if columns_to_extract:
                col_indices, col_names = [], []
                for col in columns_to_extract:
                    try:
                        idx = column_letter_to_index(col)
                        if idx < len(headers):
                            col_indices.append(idx)
                            col_names.append(headers[idx])
                    except:
                        if col in headers:
                            col_indices.append(headers.index(col))
                            col_names.append(col)
                if not col_indices:
                    self.logger.error("هیچ ستون معتبری برای استخراج یافت نشد!")
                    return []
            else:
                col_indices = list(range(len(headers)))
                col_names = headers
            ready_rows = []
            for row_idx, row_values in enumerate(all_values[1:], start=2):
                if max_rows and len(ready_rows) >= max_rows:
                    break
                while len(row_values) < len(headers):
                    row_values.append("")
                ready_value = row_values[ready_col_idx] if ready_col_idx < len(row_values) else ""
                extracted_value = row_values[extracted_col_idx] if extracted_col_idx < len(row_values) else ""
                
                # استفاده از تشخیص هوشمند به جای چک ساده
                # این قابلیت Checkbox, Dropdown, Text و Unicode را پشتیبانی می‌کند
                is_ready = is_cell_checked(ready_value)
                is_extracted = is_cell_extracted(extracted_value)
                
                if is_ready and not is_extracted:
                    row_data = {}
                    for idx, col_name in zip(col_indices, col_names):
                        row_data[col_name] = row_values[idx] if idx < len(row_values) else ""
                    ready_rows.append({"row_number": row_idx, "data": row_data})
            self.logger.success(f" {len(ready_rows)} ردیف آماده یافت شد")
            return ready_rows
        except Exception as e:
            self.logger.error(f"خطا در استخراج از worksheet '{worksheet_name}': {str(e)}")
            import traceback
            self.logger.error(f"جزئیات خطا: {traceback.format_exc()}")
            return []
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def mark_as_extracted(self, sheet_url, worksheet_name, row_number, extracted_column):
        """علامت‌گذاری یک ردیف - برای سازگاری با کدهای قدیمی"""
        return self.mark_rows_as_extracted(sheet_url, worksheet_name, [row_number], extracted_column)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def mark_rows_as_extracted(self, sheet_url, worksheet_name, row_numbers: List[int], extracted_column):
        """
        علامت‌گذاری چندین ردیف به صورت یکجا (Batch Update)
        این روش تعداد API calls را کاهش می‌دهد و از Rate Limit جلوگیری می‌کند
        
        Args:
            sheet_url: آدرس Google Sheet
            worksheet_name: نام worksheet
            row_numbers: لیست شماره ردیف‌ها
            extracted_column: نام یا حرف ستون
        """
        try:
            if not row_numbers:
                return True, "هیچ ردیفی برای علامت‌گذاری نیست"
            
            sheet = self.client.open_by_url(sheet_url)
            worksheet = sheet.worksheet(worksheet_name) if worksheet_name else sheet.sheet1
            
            # پیدا کردن ایندکس ستون
            try:
                col_index = column_letter_to_index(extracted_column) + 1
            except:
                headers = worksheet.row_values(1)
                if extracted_column not in headers:
                    return False, "ستون یافت نشد"
                col_index = headers.index(extracted_column) + 1
            
            # ساخت لیست سلول‌ها برای batch update
            cell_list = []
            for row_num in row_numbers:
                cell_list.append(gspread.Cell(row_num, col_index, "TRUE"))
            
            # یک بار update (به جای N بار!)
            worksheet.update_cells(cell_list, value_input_option='USER_ENTERED')
            # time.sleep(0.3)
            self.logger.success(f"✅ {len(row_numbers)} ردیف به صورت batch علامت‌گذاری شد")
            return True, f"{len(row_numbers)} ردیف علامت‌گذاری شد"
            
        except Exception as e:
            self.logger.error(f"خطا در علامت‌گذاری batch: {str(e)}")
            return False, str(e)
    
    def extract_and_save(self, sheet_config_id: int, auto_update: bool = False) -> Tuple[bool, str, Dict]:
        """
        استخراج و ذخیره داده از یک شیت
        
        Args:
            sheet_config_id: شناسه تنظیمات شیت
            auto_update: بروزرسانی خودکار بدون تایید کاربر
            
        Returns:
            (موفقیت, پیام, آمار)
        """
        from app.core.database import db_manager
        import json
        
        try:
            # دریافت تنظیمات شیت
            sheet_config = db_manager.get_sheet_config(sheet_config_id)
            
            if not sheet_config:
                return False, "تنظیمات شیت یافت نشد", {}
            
            if not sheet_config.is_active:
                return False, "شیت غیرفعال است", {}
            
            # استخراج داده‌ها
            # columns_to_extract قبلاً یک لیست است (JSON در دیتابیس)
            ready_rows = self.extract_ready_rows(
                sheet_url=sheet_config.sheet_url,
                worksheet_name=sheet_config.worksheet_name or 'Sheet1',
                ready_column=sheet_config.ready_column,
                extracted_column=sheet_config.extracted_column,
                columns_to_extract=sheet_config.columns_to_extract  # قبلاً لیست است
            )
            
            if not ready_rows:
                return True, "هیچ ردیف آماده‌ای یافت نشد", {'new_records': 0, 'updated_records': 0, 'duplicates': [], 'warnings': []}
            
            # 🔍 تشخیص تغییرات (ردیف‌های حذف شده/جابجا شده)
            from app.utils.change_detector import ChangeDetector
            from app.utils.unique_key_generator import generate_unique_key
            
            warnings = []
            
            # دریافت داده‌های قبلی از دیتابیس
            existing_data_list = db_manager.get_sales_data_by_sheet_config(sheet_config_id)
            
            if existing_data_list:
                detector = ChangeDetector()
                old_data = [
                    {'row_number': item.row_number, 'data': item.data}
                    for item in existing_data_list
                ]
                changes, change_stats = detector.detect_changes(
                    old_data,
                    ready_rows,
                    sheet_config.unique_key_columns
                )
                
                # اگر ردیف حذف شده یا جابجا شده وجود دارد
                if change_stats['deleted'] > 0 or change_stats['moved'] > 0:
                    warning_report = detector.generate_warning_report(changes)
                    warnings.append(warning_report)
                    self.logger.warning(warning_report)
            
            # ذخیره در دیتابیس
            new_count = 0
            updated_count = 0
            duplicate_list = []  # لیست تکراری‌ها برای بررسی بعدی
            rows_to_mark = []  # ردیف‌هایی که باید علامت بخورند
            
            for row in ready_rows:
                # ✨ ساخت کلید یکتا با سیستم جدید
                unique_key = generate_unique_key(
                    sheet_config_id=sheet_config_id,
                    row_data=row['data'],
                    unique_columns=sheet_config.unique_key_columns,
                    row_number=row['row_number']
                )
                
                # ابتدا چک می‌کنیم آیا قبلاً وجود دارد
                existing = db_manager.get_sales_data_by_unique_key(unique_key)
                
                if existing and not auto_update:
                    # تکراری است - به لیست اضافه می‌کنیم
                    duplicate_list.append({
                        'row_number': row['row_number'],
                        'unique_key': unique_key,
                        'existing_data': existing.data,
                        'new_data': row['data'],
                        'existing_id': existing.id,
                        'sheet_config_id': sheet_config_id,  # اضافه شد
                        'sheet_url': sheet_config.sheet_url,  # برای علامت‌گذاری
                        'worksheet_name': sheet_config.worksheet_name,  # برای علامت‌گذاری
                        'extracted_column': sheet_config.extracted_column  # برای علامت‌گذاری
                    })
                    continue
                
                # ذخیره داده
                success, saved_data, is_new, message = db_manager.save_sales_data(
                    sheet_config_id=sheet_config_id,
                    row_number=row['row_number'],
                    unique_key=unique_key,
                    data=row['data'],
                    update_if_exists=auto_update or existing is None
                )
                
                if success:
                    if is_new:
                        new_count += 1
                    else:
                        updated_count += 1
                    
                    # اضافه کردن به لیست ردیف‌های آماده علامت‌گذاری
                    rows_to_mark.append(row['row_number'])
            
            # علامت‌گذاری همه ردیف‌ها به صورت یکجا (Batch Update)
            if rows_to_mark:
                self.logger.info(f"🔄 در حال علامت‌گذاری {len(rows_to_mark)} ردیف...")
                self.mark_rows_as_extracted(
                    sheet_config.sheet_url,
                    sheet_config.worksheet_name or 'Sheet1',
                    rows_to_mark,
                    sheet_config.extracted_column
                )
            
            stats = {
                'new_records': new_count,
                'updated_records': updated_count,
                'total_rows': len(ready_rows),
                'duplicates': duplicate_list,  # لیست تکراری‌ها
                'warnings': warnings  # هشدارهای تغییرات
            }
            
            return True, f"{new_count} جدید، {updated_count} بروز شد، {len(duplicate_list)} تکراری", stats
            
        except Exception as e:
            self.logger.error(f"خطا در extract_and_save: {str(e)}")
            return False, str(e), {}
