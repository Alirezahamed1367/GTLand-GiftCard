"""
سیستم تشخیص تغییرات در Google Sheets
"""
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from app.core.logger import app_logger


@dataclass
class RowChange:
    """تغییرات یک ردیف"""
    row_number: int
    change_type: str  # 'added', 'deleted', 'moved', 'updated', 'unchanged'
    old_data: Optional[Dict] = None
    new_data: Optional[Dict] = None
    old_row_number: Optional[int] = None
    confidence: float = 1.0  # اطمینان از تشخیص (0-1)
    notes: str = ""


class ChangeDetector:
    """تشخیص تغییرات بین دو نسخه از داده"""
    
    def __init__(self):
        self.logger = app_logger
    
    def detect_changes(
        self,
        old_data: List[Dict],  # داده‌های قبلی از دیتابیس
        new_data: List[Dict],  # داده‌های جدید از Google Sheet
        unique_columns: Optional[List[str]] = None
    ) -> Tuple[List[RowChange], Dict]:
        """
        تشخیص تغییرات بین دو مجموعه داده
        
        Args:
            old_data: داده‌های قبلی (از دیتابیس)
            new_data: داده‌های جدید (از Google Sheet)
            unique_columns: ستون‌های کلیدی برای تطبیق
            
        Returns:
            (لیست تغییرات, آمار)
        """
        from app.utils.unique_key_generator import generate_content_hash
        
        changes = []
        stats = {
            'added': 0,
            'deleted': 0,
            'moved': 0,
            'updated': 0,
            'unchanged': 0
        }
        
        # ساخت نقشه hash برای داده‌های قدیمی
        old_hash_map = {}  # {hash: (row_num, data)}
        for item in old_data:
            content_hash = generate_content_hash(item['data'], unique_columns)
            old_hash_map[content_hash] = (item['row_number'], item['data'])
        
        # ساخت نقشه hash برای داده‌های جدید
        new_hash_map = {}  # {hash: (row_num, data)}
        for item in new_data:
            content_hash = generate_content_hash(item['data'], unique_columns)
            new_hash_map[content_hash] = (item['row_number'], item['data'])
        
        # پیدا کردن ردیف‌های حذف شده
        for content_hash, (old_row, old_row_data) in old_hash_map.items():
            if content_hash not in new_hash_map:
                changes.append(RowChange(
                    row_number=old_row,
                    change_type='deleted',
                    old_data=old_row_data,
                    notes=f"ردیف {old_row} در شیت حذف شده است"
                ))
                stats['deleted'] += 1
        
        # پیدا کردن ردیف‌های جدید و تغییر یافته
        for content_hash, (new_row, new_row_data) in new_hash_map.items():
            if content_hash in old_hash_map:
                old_row, old_row_data = old_hash_map[content_hash]
                
                if old_row == new_row:
                    # ردیف جابجا نشده
                    changes.append(RowChange(
                        row_number=new_row,
                        change_type='unchanged',
                        old_data=old_row_data,
                        new_data=new_row_data
                    ))
                    stats['unchanged'] += 1
                else:
                    # ردیف جابجا شده
                    changes.append(RowChange(
                        row_number=new_row,
                        change_type='moved',
                        old_data=old_row_data,
                        new_data=new_row_data,
                        old_row_number=old_row,
                        notes=f"ردیف از {old_row} به {new_row} جابجا شده"
                    ))
                    stats['moved'] += 1
            else:
                # ردیف جدید
                changes.append(RowChange(
                    row_number=new_row,
                    change_type='added',
                    new_data=new_row_data,
                    notes=f"ردیف {new_row} جدید است"
                ))
                stats['added'] += 1
        
        return changes, stats
    
    def generate_warning_report(self, changes: List[RowChange]) -> str:
        """
        ساخت گزارش هشدار برای کاربر
        
        Args:
            changes: لیست تغییرات
            
        Returns:
            متن گزارش
        """
        deleted = [c for c in changes if c.change_type == 'deleted']
        moved = [c for c in changes if c.change_type == 'moved']
        
        if not deleted and not moved:
            return ""
        
        report = "⚠️ تغییراتی در Google Sheet شناسایی شد:\n\n"
        
        if deleted:
            report += f"🗑️ {len(deleted)} ردیف حذف شده:\n"
            for change in deleted[:10]:  # نمایش 10 اولی
                report += f"   • ردیف {change.row_number}\n"
            if len(deleted) > 10:
                report += f"   ... و {len(deleted) - 10} ردیف دیگر\n"
            report += "\n"
        
        if moved:
            report += f"🔄 {len(moved)} ردیف جابجا شده:\n"
            for change in moved[:10]:
                report += f"   • ردیف {change.old_row_number} → {change.row_number}\n"
            if len(moved) > 10:
                report += f"   ... و {len(moved) - 10} ردیف دیگر\n"
            report += "\n"
        
        report += "💡 توصیه: قبل از ادامه، تغییرات را بررسی کنید."
        
        return report
