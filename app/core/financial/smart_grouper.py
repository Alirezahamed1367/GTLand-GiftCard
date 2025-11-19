"""
Smart Grouping Algorithm - الگوریتم گروه‌بندی هوشمند
====================================================
تشخیص خودکار ردیف‌های پشت سر هم با شرایط یکسان و جمع آن‌ها
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
import hashlib


@dataclass
class GroupingRule:
    """
    قوانین گروه‌بندی که کاربر تعیین می‌کند
    """
    # فیلدهایی که باید برای گروه‌بندی یکسان باشند
    grouping_fields: List[str]  # مثال: ["Sold_Date", "CODE", "Customer", "Rate"]
    
    # فیلدی که باید جمع شود
    sum_field: str  # مثال: "Value"
    
    # آستانه زمانی (ثانیه) - اگر ردیف‌ها بیش از این فاصله داشته باشند جمع نمی‌شوند
    time_threshold_seconds: Optional[int] = None  # مثال: 300 (5 دقیقه)
    
    # حداکثر تعداد ردیف‌های قابل جمع
    max_rows_to_group: Optional[int] = None  # مثال: 200
    
    # آیا فقط ردیف‌های متوالی را جمع کنیم؟
    only_consecutive: bool = True


@dataclass
class GroupedTransaction:
    """
    نتیجه گروه‌بندی
    """
    group_id: str  # شناسه یکتای گروه
    group_key: Dict[str, Any]  # کلیدهای گروه (Date, CODE, Customer, Rate)
    total_value: float  # مجموع
    row_count: int  # تعداد ردیف‌ها
    row_ids: List[int]  # شناسه ردیف‌های اصلی
    raw_data_ids: List[int]  # IDهای raw_data
    first_row_data: Dict[str, Any]  # اولین ردیف (برای سایر فیلدها)
    created_at: datetime


class SmartGrouper:
    """
    موتور گروه‌بندی هوشمند
    """
    
    def __init__(self, rule: GroupingRule):
        self.rule = rule
    
    def group_rows(self, rows: List[Dict[str, Any]]) -> List[GroupedTransaction]:
        """
        گروه‌بندی ردیف‌ها
        
        Args:
            rows: لیست ردیف‌ها (هر ردیف یک دیکشنری)
            
        Returns:
            لیست تراکنش‌های گروه‌بندی شده
        """
        if not rows:
            return []
        
        grouped = []
        
        if self.rule.only_consecutive:
            # گروه‌بندی فقط ردیف‌های متوالی
            grouped = self._group_consecutive_rows(rows)
        else:
            # گروه‌بندی تمام ردیف‌های مشابه (حتی غیرمتوالی)
            grouped = self._group_all_similar_rows(rows)
        
        return grouped
    
    def _group_consecutive_rows(self, rows: List[Dict[str, Any]]) -> List[GroupedTransaction]:
        """
        گروه‌بندی ردیف‌های متوالی
        """
        grouped = []
        current_group = None
        current_group_rows = []
        
        for i, row in enumerate(rows):
            # کلید گروه برای این ردیف
            group_key = self._extract_group_key(row)
            
            if current_group is None:
                # اولین ردیف
                current_group = group_key
                current_group_rows = [row]
            elif self._is_same_group(group_key, current_group):
                # ردیف جدید همان گروه است
                current_group_rows.append(row)
                
                # بررسی محدودیت تعداد
                if self.rule.max_rows_to_group and len(current_group_rows) >= self.rule.max_rows_to_group:
                    # رسیدیم به حد - گروه را ذخیره کن
                    grouped.append(self._create_grouped_transaction(current_group, current_group_rows))
                    current_group = None
                    current_group_rows = []
            else:
                # گروه جدید شروع شد
                # گروه قبلی را ذخیره کن
                grouped.append(self._create_grouped_transaction(current_group, current_group_rows))
                
                # گروه جدید
                current_group = group_key
                current_group_rows = [row]
        
        # گروه آخر
        if current_group is not None and current_group_rows:
            grouped.append(self._create_grouped_transaction(current_group, current_group_rows))
        
        return grouped
    
    def _group_all_similar_rows(self, rows: List[Dict[str, Any]]) -> List[GroupedTransaction]:
        """
        گروه‌بندی تمام ردیف‌های مشابه (حتی غیرمتوالی)
        """
        groups_dict = {}
        
        for row in rows:
            group_key = self._extract_group_key(row)
            group_hash = self._hash_group_key(group_key)
            
            if group_hash not in groups_dict:
                groups_dict[group_hash] = {
                    "key": group_key,
                    "rows": []
                }
            
            groups_dict[group_hash]["rows"].append(row)
        
        # تبدیل به GroupedTransaction
        grouped = []
        for group_hash, group_data in groups_dict.items():
            grouped.append(
                self._create_grouped_transaction(
                    group_data["key"],
                    group_data["rows"]
                )
            )
        
        return grouped
    
    def _extract_group_key(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        استخراج کلید گروه از ردیف
        """
        key = {}
        for field in self.rule.grouping_fields:
            value = row.get(field)
            
            # نرمال‌سازی
            if isinstance(value, str):
                value = value.strip().lower()
            
            key[field] = value
        
        return key
    
    def _is_same_group(self, key1: Dict[str, Any], key2: Dict[str, Any]) -> bool:
        """
        بررسی آیا دو کلید گروه یکسان هستند
        """
        for field in self.rule.grouping_fields:
            if key1.get(field) != key2.get(field):
                return False
        return True
    
    def _hash_group_key(self, key: Dict[str, Any]) -> str:
        """
        تولید هش از کلید گروه
        """
        values = []
        for field in sorted(key.keys()):
            values.append(f"{field}:{key[field]}")
        
        combined = "|".join(values)
        hash_obj = hashlib.sha256(combined.encode('utf-8'))
        return hash_obj.hexdigest()
    
    def _create_grouped_transaction(
        self, 
        group_key: Dict[str, Any], 
        rows: List[Dict[str, Any]]
    ) -> GroupedTransaction:
        """
        ایجاد تراکنش گروه‌بندی شده
        """
        # محاسبه مجموع
        total = 0.0
        for row in rows:
            value = row.get(self.rule.sum_field, 0)
            try:
                total += float(value)
            except (ValueError, TypeError):
                pass
        
        # استخراج IDها
        row_ids = [row.get('id', i) for i, row in enumerate(rows)]
        raw_data_ids = [row.get('raw_data_id', row.get('id', i)) for i, row in enumerate(rows)]
        
        # گروه ID
        group_id = self._hash_group_key(group_key)
        
        return GroupedTransaction(
            group_id=group_id,
            group_key=group_key,
            total_value=total,
            row_count=len(rows),
            row_ids=row_ids,
            raw_data_ids=raw_data_ids,
            first_row_data=rows[0] if rows else {},
            created_at=datetime.now()
        )


def auto_detect_grouping_fields(rows: List[Dict[str, Any]], value_field: str) -> List[str]:
    """
    تشخیص خودکار فیلدهایی که باید برای گروه‌بندی استفاده شوند
    
    بر اساس نقش‌های فیلدها (used_in_grouping=True)
    """
    if not rows:
        return []
    
    # فیلدهای رایج که معمولاً در گروه‌بندی استفاده می‌شوند
    common_grouping_fields = [
        'date', 'sold_date', 'purchase_date', 'transaction_date',
        'code', 'account_code', 'product_code',
        'customer', 'customer_name', 'customer_code',
        'rate', 'sale_rate', 'purchase_rate',
    ]
    
    # پیدا کردن فیلدهای موجود
    available_fields = rows[0].keys()
    detected_fields = []
    
    for field in available_fields:
        field_lower = field.lower().replace('_', '').replace(' ', '')
        
        for common in common_grouping_fields:
            common_lower = common.lower().replace('_', '').replace(' ', '')
            if common_lower in field_lower or field_lower in common_lower:
                detected_fields.append(field)
                break
    
    return detected_fields


def create_grouping_rule_from_roles(
    db_session,
    value_field: str,
    only_consecutive: bool = True
) -> GroupingRule:
    """
    ایجاد قانون گروه‌بندی از روی نقش‌های تعریف شده
    
    Args:
        db_session: Session دیتابیس
        value_field: فیلدی که باید جمع شود
        only_consecutive: فقط ردیف‌های متوالی
    """
    from app.models.financial import FieldRole
    
    # پیدا کردن نقش‌هایی که used_in_grouping=True دارند
    roles = db_session.query(FieldRole).filter(
        FieldRole.used_in_grouping == True,
        FieldRole.is_active == True
    ).order_by(FieldRole.display_order).all()
    
    grouping_fields = [role.name for role in roles]
    
    if not grouping_fields:
        # اگر کاربر نقشی تعیین نکرده، از پیش‌فرض استفاده می‌کنیم
        grouping_fields = ['date', 'code', 'customer', 'rate']
    
    return GroupingRule(
        grouping_fields=grouping_fields,
        sum_field=value_field,
        only_consecutive=only_consecutive,
        max_rows_to_group=1000  # حداکثر 1000 ردیف
    )


# مثال استفاده:
"""
# تعریف قانون
rule = GroupingRule(
    grouping_fields=["Sold_Date", "CODE", "Customer", "Rate"],
    sum_field="Value",
    only_consecutive=True
)

# گروه‌بندی
grouper = SmartGrouper(rule)
grouped = grouper.group_rows(raw_rows)

# نتیجه:
for group in grouped:
    print(f"گروه {group.group_id}:")
    print(f"  تعداد ردیف: {group.row_count}")
    print(f"  مجموع: {group.total_value}")
    print(f"  کلیدها: {group.group_key}")
"""
