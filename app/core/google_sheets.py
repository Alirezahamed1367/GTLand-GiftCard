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
    def extract_ready_rows(self, sheet_url, worksheet_name, ready_column, extracted_column, columns_to_extract=None, skip_rows=0, max_rows=None, log_callback=None):
        """
        استخراج ردیف‌های آماده از Google Sheets
        
        Args:
            log_callback: تابع اختیاری (message, level) برای ارسال لاگ به UI
        """
        try:
            msg = f"📄 در حال باز کردن worksheet: '{worksheet_name}'"
            self.logger.info(msg)
            if log_callback:
                log_callback(msg, "info")
            
            sheet = self.client.open_by_url(sheet_url)
            
            # لیست تمام worksheetها را لاگ کن
            all_worksheets = [ws.title for ws in sheet.worksheets()]
            msg = f"📋 لیست worksheetهای موجود: {all_worksheets}"
            self.logger.info(msg)
            if log_callback:
                log_callback(msg, "info")
            
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
            if log_callback:
                log_callback(f"✅ Worksheet '{worksheet.title}' باز شد", "success")
            
            all_values = worksheet.get_all_values()
            if not all_values or len(all_values) < 2:
                msg = "⚠️ شیت خالی است یا فقط هدر دارد"
                self.logger.warning(msg)
                if log_callback:
                    log_callback(msg, "warning")
                return []
            
            # پاک‌سازی هدرها: حذف علامت تیک و فضای خالی
            headers = all_values[0]
            headers = [str(h).strip().replace('✓', '').replace('✔', '').replace('☑', '').replace('✅', '').strip() for h in headers]
            
            msg = f"📊 هدرهای یافت شده: {headers}"
            self.logger.info(msg)
            if log_callback:
                log_callback(msg, "info")
            
            msg = f"📏 تعداد کل ردیف‌ها: {len(all_values) - 1:,}"
            self.logger.info(msg)
            if log_callback:
                log_callback(msg, "info")
            
            # ==================== پیدا کردن ستون آماده (Ready) ====================
            ready_col_idx = -1
            ready_column_clean = ready_column.strip().lower()
            
            # روش 1: جستجو در نام‌های ستون‌ها (اولویت اول)
            for idx, header in enumerate(headers):
                header_clean = str(header).strip().lower()
                if header_clean == ready_column_clean:
                    ready_col_idx = idx
                    msg = f"✅ ستون آماده پیدا شد با نام: '{header}' (index {idx})"
                    self.logger.info(msg)
                    if log_callback:
                        log_callback(msg, "success")
                    break
            
            # روش 2: اگر پیدا نشد، شاید حرف ستون باشد (A, B, C, ...)
            if ready_col_idx == -1 and len(ready_column) <= 3 and ready_column.isalpha():
                try:
                    ready_col_idx = column_letter_to_index(ready_column)
                    if ready_col_idx < len(headers):
                        self.logger.info(f"✅ ستون آماده پیدا شد با حرف: {ready_column} -> '{headers[ready_col_idx]}' (index {ready_col_idx})")
                    else:
                        ready_col_idx = -1
                except:
                    pass
            
            if ready_col_idx == -1:
                self.logger.error(f"❌ ستون آماده '{ready_column}' یافت نشد!")
                self.logger.error(f"📋 هدرهای موجود: {headers}")
                return []
            
            # ==================== پیدا کردن ستون استخراج شده (Extracted) ====================
            extracted_col_idx = -1
            extracted_column_clean = extracted_column.strip().lower()
            
            # روش 1: جستجو در نام‌های ستون‌ها (اولویت اول)
            for idx, header in enumerate(headers):
                header_clean = str(header).strip().lower()
                if header_clean == extracted_column_clean:
                    extracted_col_idx = idx
                    msg = f"✅ ستون استخراج پیدا شد با نام: '{header}' (index {idx})"
                    self.logger.info(msg)
                    if log_callback:
                        log_callback(msg, "success")
                    break
            
            # روش 2: اگر پیدا نشد، شاید حرف ستون باشد (A, B, C, ...)
            if extracted_col_idx == -1 and len(extracted_column) <= 3 and extracted_column.isalpha():
                try:
                    extracted_col_idx = column_letter_to_index(extracted_column)
                    if extracted_col_idx < len(headers):
                        self.logger.info(f"✅ ستون استخراج پیدا شد با حرف: {extracted_column} -> '{headers[extracted_col_idx]}' (index {extracted_col_idx})")
                    else:
                        extracted_col_idx = -1
                except:
                    pass
            
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
                        row_data[col_name] = row_data.get(col_name, row_values[idx] if idx < len(row_values) else "")
                    ready_rows.append({"row_number": row_idx, "data": row_data})
            
            msg = f"✅ {len(ready_rows):,} ردیف آماده یافت شد"
            self.logger.success(msg)
            if log_callback:
                log_callback(msg, "success")
            
            return ready_rows
        except Exception as e:
            msg = f"❌ خطا در استخراج از worksheet '{worksheet_name}': {str(e)}"
            self.logger.error(msg)
            if log_callback:
                log_callback(msg, "error")
            import traceback
            self.logger.error(f"جزئیات خطا: {traceback.format_exc()}")
            return []
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def mark_as_extracted(self, sheet_url, worksheet_name, row_number, extracted_column):
        """علامت‌گذاری یک ردیف - برای سازگاری با کدهای قدیمی"""
        return self.mark_rows_as_extracted(sheet_url, worksheet_name, [row_number], extracted_column)
    
    def mark_rows_as_extracted(self, sheet_url, worksheet_name, row_numbers: List[int], extracted_column, progress_callback=None):
        """
        علامت‌گذاری چندین ردیف با مدیریت پیشرفته خطا و تقسیم‌بندی هوشمند
        
        این متد:
        - رکوردها را به بچ‌های کوچک تقسیم می‌کند (500 رکورد)
        - از timeout و retry استفاده می‌کند
        - پیشرفت را گزارش می‌دهد
        - در صورت خطا، بچ را به قسمت‌های کوچک‌تر تقسیم می‌کند
        
        Args:
            sheet_url: آدرس Google Sheet
            worksheet_name: نام worksheet
            row_numbers: لیست شماره ردیف‌ها
            extracted_column: نام یا حرف ستون
            progress_callback: تابع گزارش پیشرفت (فعلی, کل, پیام)
        
        Returns:
            (موفقیت, پیام, آمار)
        """
        try:
            if not row_numbers:
                return True, "هیچ ردیفی برای علامت‌گذاری نیست", {}
            
            total_rows = len(row_numbers)
            self.logger.info(f"🔄 شروع علامت‌گذاری {total_rows:,} ردیف...")
            
            # اتصال به شیت
            sheet = self.client.open_by_url(sheet_url)
            
            # جستجوی case-insensitive برای worksheet (مشابه extract_ready_rows)
            if worksheet_name:
                matching_ws = None
                all_worksheets = [ws.title for ws in sheet.worksheets()]
                
                for ws in sheet.worksheets():
                    if ws.title.lower() == worksheet_name.lower():
                        matching_ws = ws
                        break
                
                if matching_ws:
                    worksheet = matching_ws
                    if matching_ws.title != worksheet_name:
                        self.logger.info(f"📋 Worksheet واقعی: '{matching_ws.title}' (از تنظیمات: '{worksheet_name}')")
                else:
                    self.logger.error(f"❌ Worksheet '{worksheet_name}' یافت نشد. موجود: {all_worksheets}")
                    return False, f"Worksheet '{worksheet_name}' یافت نشد", {}
            else:
                worksheet = sheet.sheet1
            
            # پیدا کردن ایندکس ستون با منطق جدید
            headers = worksheet.row_values(1)
            
            # پاک‌سازی هدرها: حذف علامت تیک و فضای خالی
            headers = [str(h).strip().replace('✓', '').replace('✔', '').replace('☑', '').replace('✅', '').strip() for h in headers]
            
            extracted_col_idx = -1
            extracted_column_clean = extracted_column.strip().lower()
            
            # جستجوی نام ستون
            for idx, header in enumerate(headers):
                if str(header).strip().lower() == extracted_column_clean:
                    extracted_col_idx = idx + 1  # +1 برای gspread (1-indexed)
                    self.logger.info(f"✅ ستون استخراج پیدا شد: '{header}' (index {extracted_col_idx})")
                    break
            
            # اگر نیافت، شاید حرف ستون باشد
            if extracted_col_idx == -1 and len(extracted_column) <= 3 and extracted_column.isalpha():
                try:
                    extracted_col_idx = column_letter_to_index(extracted_column) + 1
                    self.logger.info(f"✅ ستون استخراج از طریق حرف: {extracted_column} (index {extracted_col_idx})")
                except:
                    pass
            
            if extracted_col_idx == -1:
                self.logger.error(f"❌ ستون '{extracted_column}' یافت نشد!")
                self.logger.error(f"📋 هدرهای پاک شده: {headers}")
                return False, f"ستون '{extracted_column}' یافت نشد", {}
            
            self.logger.info(f"🎯 شروع علامت‌گذاری در ستون index {extracted_col_idx}")
            
            # تقسیم به بچ‌های بزرگ‌تر برای سرعت بیشتر
            BATCH_SIZE = 1000  # افزایش از 500 به 1000 برای سرعت بیشتر
            total_batches = (total_rows + BATCH_SIZE - 1) // BATCH_SIZE
            
            success_count = 0
            failed_batches = []
            
            for batch_num in range(total_batches):
                start_idx = batch_num * BATCH_SIZE
                end_idx = min(start_idx + BATCH_SIZE, total_rows)
                batch_rows = row_numbers[start_idx:end_idx]
                batch_size = len(batch_rows)
                
                # گزارش پیشرفت
                if progress_callback:
                    progress_callback(success_count, total_rows, f"علامت‌گذاری بچ {batch_num + 1}/{total_batches}")
                
                self.logger.info(f"📦 بچ {batch_num + 1}/{total_batches}: {batch_size} ردیف (از {start_idx + 1} تا {end_idx})")
                
                try:
                    # تلاش برای update با timeout
                    success = self._update_batch_with_retry(
                        worksheet, batch_rows, extracted_col_idx, 
                        max_attempts=3, initial_batch_size=batch_size
                    )
                    
                    if success:
                        success_count += batch_size
                        self.logger.success(f"✅ بچ {batch_num + 1} موفق: {batch_size} ردیف")
                    else:
                        failed_batches.append(batch_num + 1)
                        self.logger.error(f"❌ بچ {batch_num + 1} ناموفق")
                        
                except Exception as e:
                    failed_batches.append(batch_num + 1)
                    self.logger.error(f"❌ خطا در بچ {batch_num + 1}: {str(e)}")
                
                # تاخیر کمتر بین بچ‌ها برای سرعت بیشتر
                if batch_num < total_batches - 1:
                    time.sleep(0.5)  # کاهش از 1 ثانیه به 0.5 ثانیه
            
            # گزارش نهایی
            stats = {
                'total': total_rows,
                'success': success_count,
                'failed': total_rows - success_count,
                'failed_batches': failed_batches
            }
            
            if success_count == total_rows:
                msg = f"✅ تمام {total_rows:,} ردیف با موفقیت علامت‌گذاری شدند"
                self.logger.success(msg)
                return True, msg, stats
            elif success_count > 0:
                msg = f"⚠️ {success_count:,} از {total_rows:,} ردیف علامت‌گذاری شد (بچ‌های ناموفق: {failed_batches})"
                self.logger.warning(msg)
                return True, msg, stats
            else:
                msg = f"❌ هیچ ردیفی علامت‌گذاری نشد"
                self.logger.error(msg)
                return False, msg, stats
                
        except Exception as e:
            self.logger.error(f"❌ خطای کلی در علامت‌گذاری: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False, f"خطا: {str(e)}", {'total': len(row_numbers), 'success': 0, 'failed': len(row_numbers)}
    
    def _update_batch_with_retry(self, worksheet, row_numbers, col_idx, max_attempts=3, initial_batch_size=None):
        """
        تلاش برای update یک بچ با retry و تقسیم‌بندی در صورت خطا
        
        Args:
            worksheet: worksheet object
            row_numbers: لیست شماره ردیف‌ها
            col_idx: ایندکس ستون
            max_attempts: حداکثر تلاش
            initial_batch_size: اندازه اولیه بچ
        
        Returns:
            bool: موفقیت
        """
        batch_size = initial_batch_size or len(row_numbers)
        
        for attempt in range(max_attempts):
            try:
                # ساخت لیست سلول‌ها
                cell_list = []
                for row_num in row_numbers:
                    cell_list.append(gspread.Cell(row_num, col_idx, "TRUE"))
                
                # تلاش برای update
                worksheet.update_cells(cell_list, value_input_option='USER_ENTERED')
                return True
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # اگر خطای timeout یا connection بود
                if 'timeout' in error_msg or 'connection' in error_msg or 'aborted' in error_msg:
                    # تقسیم بچ به دو نیمه و تلاش مجدد
                    if len(row_numbers) > 10:  # فقط اگر بچ بزرگ باشد
                        mid = len(row_numbers) // 2
                        self.logger.warning(f"⚠️ تقسیم بچ به دو نیمه ({mid} + {len(row_numbers) - mid})")
                        
                        # تلاش برای نیمه اول
                        success1 = self._update_batch_with_retry(
                            worksheet, row_numbers[:mid], col_idx, 
                            max_attempts=2, initial_batch_size=mid
                        )
                        
                        # تلاش برای نیمه دوم
                        success2 = self._update_batch_with_retry(
                            worksheet, row_numbers[mid:], col_idx,
                            max_attempts=2, initial_batch_size=len(row_numbers) - mid
                        )
                        
                        return success1 and success2
                
                # اگر تلاش آخر بود
                if attempt == max_attempts - 1:
                    self.logger.error(f"❌ شکست بعد از {max_attempts} تلاش: {str(e)}")
                    return False
                
                # تاخیر قبل از تلاش بعدی
                wait_time = 2 ** attempt  # exponential backoff
                self.logger.warning(f"⚠️ تلاش {attempt + 1} ناموفق، صبر {wait_time}s...")
                time.sleep(wait_time)
        
        return False
    
    def extract_and_save(self, sheet_config_id: int, auto_update: bool = False, progress_callback=None, log_callback=None) -> Tuple[bool, str, Dict]:
        """
        استخراج و ذخیره داده از یک شیت با گزارش پیشرفت دقیق
        
        Args:
            sheet_config_id: شناسه تنظیمات شیت
            auto_update: بروزرسانی خودکار بدون تایید کاربر
            progress_callback: تابع (current, total, message) برای گزارش پیشرفت
            log_callback: تابع (message, level) برای ارسال لاگ به UI
            
        Returns:
            (موفقیت, پیام, آمار کامل)
        """
        from app.core.database import db_manager
        import json
        
        try:
            # دریافت تنظیمات شیت
            if progress_callback:
                progress_callback(0, 100, "دریافت تنظیمات شیت")
            
            sheet_config = db_manager.get_sheet_config(sheet_config_id)
            
            if not sheet_config:
                return False, "تنظیمات شیت یافت نشد", {}
            
            if not sheet_config.is_active:
                return False, "شیت غیرفعال است", {}
            
            # استخراج داده‌ها
            if progress_callback:
                progress_callback(10, 100, "اتصال به Google Sheets")
            
            if log_callback:
                log_callback("🔗 اتصال به Google Sheets برقرار شد", "success")
            
            ready_rows = self.extract_ready_rows(
                sheet_url=sheet_config.sheet_url,
                worksheet_name=sheet_config.worksheet_name or 'Sheet1',
                ready_column=sheet_config.ready_column,
                extracted_column=sheet_config.extracted_column,
                columns_to_extract=sheet_config.columns_to_extract,
                log_callback=log_callback
            )
            
            if not ready_rows:
                return True, "هیچ ردیف آماده‌ای یافت نشد", {
                    'new_records': 0, 
                    'updated_records': 0, 
                    'total_extracted': 0,
                    'duplicates': [], 
                    'warnings': []
                }
            
            total_rows = len(ready_rows)
            msg = f"📥 {total_rows:,} ردیف آماده برای پردازش"
            self.logger.info(msg)
            if log_callback:
                log_callback(msg, "info")
            
            if progress_callback:
                progress_callback(20, 100, f"پردازش {total_rows:,} ردیف")
            
            # 🔍 تشخیص تغییرات
            from app.utils.change_detector import ChangeDetector
            from app.utils.unique_key_generator import generate_unique_key
            
            if log_callback:
                log_callback("🔍 بررسی تغییرات و تکراری‌ها...", "info")
            
            warnings = []
            existing_data_list = db_manager.get_sales_data_by_sheet_config(sheet_config_id)
            
            if existing_data_list:
                if log_callback:
                    log_callback(f"📊 {len(existing_data_list):,} رکورد موجود در دیتابیس", "info")
                
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
                    if log_callback:
                        log_callback(f"⚠️ تغییرات شناسایی شد: {change_stats}", "warning")
            else:
                if log_callback:
                    log_callback("📊 هیچ رکورد قبلی در دیتابیس یافت نشد (اولین استخراج)", "info")
            
            # ذخیره در دیتابیس
            if log_callback:
                log_callback("💾 شروع ذخیره رکوردها در دیتابیس...", "info")
            
            new_count = 0
            updated_count = 0
            duplicate_list = []  # لیست تکراری‌ها برای بررسی بعدی
            rows_to_mark = []  # ردیف‌هایی که باید علامت بخورند
            
            for idx, row in enumerate(ready_rows):
                if progress_callback and idx % 100 == 0:
                    progress_callback(
                        30 + int((idx / total_rows) * 50),
                        100,
                        f"پردازش {idx+1:,} از {total_rows:,}"
                    )
                
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
            mark_stats = {}
            if rows_to_mark:
                msg = f"🔄 در حال علامت‌گذاری {len(rows_to_mark):,} ردیف در ستون Extracted..."
                self.logger.info(msg)
                if log_callback:
                    log_callback(msg, "info")
                
                # callback برای پیشرفت علامت‌گذاری
                def mark_progress_callback(current, total, message):
                    if progress_callback:
                        progress_callback(80 + int((current / total) * 15), 100, message)
                
                success, mark_msg, mark_stats = self.mark_rows_as_extracted(
                    sheet_config.sheet_url,
                    sheet_config.worksheet_name or 'Sheet1',
                    rows_to_mark,
                    sheet_config.extracted_column,
                    progress_callback=mark_progress_callback
                )
                
                if success:
                    msg = f"✅ علامت‌گذاری تکمیل شد: {mark_stats.get('success', 0):,} ردیف"
                    self.logger.success(msg)
                    if log_callback:
                        log_callback(msg, "success")
                else:
                    msg = f"⚠️ علامت‌گذاری با خطا: {mark_msg}"
                    self.logger.warning(msg)
                    if log_callback:
                        log_callback(msg, "warning")
            
            if progress_callback:
                progress_callback(100, 100, "✅ تمام شد!")
            
            stats = {
                'new_records': new_count,
                'updated_records': updated_count,
                'total_rows': len(ready_rows),
                'total_extracted': len(rows_to_mark),
                'mark_stats': mark_stats,
                'duplicates': duplicate_list,  # لیست تکراری‌ها
                'warnings': warnings  # هشدارهای تغییرات
            }
            
            return True, f"{new_count} جدید، {updated_count} بروز شد، {len(duplicate_list)} تکراری", stats
            
        except Exception as e:
            self.logger.error(f"خطا در extract_and_save: {str(e)}")
            return False, str(e), {}
