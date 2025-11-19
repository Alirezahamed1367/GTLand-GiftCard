"""
Data Processor - پردازشگر Stage 1 → Stage 2
============================================
تبدیل raw_data به products, purchases, sales, bonuses, customers
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.financial import (
    RawData, 
    ProductV2, PurchaseV2, SaleV2, BonusV2, CustomerV2,
    FieldRole, CustomField
)
from app.core.financial.smart_grouper import SmartGrouper, GroupingRule, GroupedTransaction


class DataProcessor:
    """
    پردازشگر داده‌ها
    
    تبدیل raw_data به مدل‌های Stage 2
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def process_sheet(
        self, 
        sheet_name: str, 
        sheet_type: str,
        enable_grouping: bool = True
    ) -> Dict[str, int]:
        """
        پردازش یک شیت کامل
        
        Args:
            sheet_name: نام شیت
            sheet_type: نوع شیت (purchase, sale, bonus)
            enable_grouping: فعال‌سازی گروه‌بندی هوشمند
            
        Returns:
            آمار پردازش
        """
        stats = {
            "processed_rows": 0,
            "new_products": 0,
            "new_purchases": 0,
            "new_sales": 0,
            "new_bonuses": 0,
            "new_customers": 0,
            "grouped_transactions": 0,
            "errors": 0
        }
        
        # پیدا کردن raw_dataهای پردازش نشده
        raw_rows = self.db.query(RawData).filter(
            and_(
                RawData.sheet_name == sheet_name,
                RawData.is_processed == False,
                RawData.is_extracted == True,  # فقط ردیف‌های Extracted
                RawData.has_conflict == False,  # بدون تداخل
                RawData.is_deleted == False
            )
        ).order_by(RawData.row_number).all()
        
        if not raw_rows:
            return stats
        
        # تبدیل به لیست دیکشنری
        rows_data = []
        for raw in raw_rows:
            row_dict = raw.data.copy()
            row_dict['_raw_id'] = raw.id
            row_dict['_row_number'] = raw.row_number
            rows_data.append(row_dict)
        
        # پردازش بر اساس نوع شیت
        if sheet_type == 'purchase':
            stats = self._process_purchases(rows_data, sheet_name)
        elif sheet_type == 'sale':
            if enable_grouping:
                stats = self._process_sales_with_grouping(rows_data, sheet_name)
            else:
                stats = self._process_sales(rows_data, sheet_name)
        elif sheet_type == 'bonus':
            stats = self._process_bonuses(rows_data, sheet_name)
        else:
            # نوع نامشخص - فقط علامت‌گذاری می‌کنیم
            for raw in raw_rows:
                raw.is_processed = True
                raw.processed_at = datetime.now()
            stats["processed_rows"] = len(raw_rows)
        
        self.db.commit()
        return stats
    
    def _process_purchases(
        self, 
        rows: List[Dict[str, Any]], 
        sheet_name: str
    ) -> Dict[str, int]:
        """
        پردازش خریدها (Consumed Sheet)
        """
        stats = {"processed_rows": 0, "new_products": 0, "new_purchases": 0, "errors": 0}
        
        for row in rows:
            try:
                # پیدا کردن فیلدهای کلیدی
                identifier = self._extract_field_by_role(row, 'identifier')
                value = self._extract_field_by_role(row, 'value')
                rate = self._extract_field_by_role(row, 'rate')
                tr_id = self._extract_field_by_role(row, 'transaction_id')
                date_field = self._extract_field_by_role(row, 'date')
                
                if not identifier:
                    continue
                
                # پیدا یا ایجاد Product
                product = self._get_or_create_product(
                    identifier=identifier,
                    initial_balance=value,
                    source_sheet=sheet_name,
                    extra_data=row
                )
                
                if not product:
                    continue
                
                # ثبت Purchase
                purchase = PurchaseV2(
                    product_id=product.id,
                    transaction_id=tr_id,
                    quantity=Decimal(str(value)) if value else 0,
                    rate=Decimal(str(rate)) if rate else None,
                    amount=Decimal(str(value)) * Decimal(str(rate)) if (value and rate) else None,
                    purchase_date=self._parse_date(date_field),
                    source_sheet=sheet_name,
                    raw_data_id=row.get('_raw_id'),
                    extra_data=row
                )
                
                self.db.add(purchase)
                stats["new_purchases"] += 1
                
                # علامت‌گذاری raw_data
                raw = self.db.query(RawData).get(row.get('_raw_id'))
                if raw:
                    raw.is_processed = True
                    raw.processed_at = datetime.now()
                
                stats["processed_rows"] += 1
                
            except Exception as e:
                stats["errors"] += 1
                print(f"❌ خطا در پردازش خرید: {e}")
        
        return stats
    
    def _process_sales_with_grouping(
        self, 
        rows: List[Dict[str, Any]], 
        sheet_name: str
    ) -> Dict[str, int]:
        """
        پردازش فروش با گروه‌بندی هوشمند
        """
        stats = {
            "processed_rows": 0, 
            "new_sales": 0, 
            "new_customers": 0, 
            "grouped_transactions": 0,
            "errors": 0
        }
        
        # ایجاد قانون گروه‌بندی
        grouping_fields = self._get_grouping_fields()
        value_field = self._get_value_field_name()
        
        rule = GroupingRule(
            grouping_fields=grouping_fields,
            sum_field=value_field,
            only_consecutive=True
        )
        
        # گروه‌بندی
        grouper = SmartGrouper(rule)
        grouped_transactions = grouper.group_rows(rows)
        
        # پردازش گروه‌ها
        for group in grouped_transactions:
            try:
                # استخراج فیلدهای کلیدی از اولین ردیف
                first_row = group.first_row_data
                
                identifier = self._extract_field_by_role(first_row, 'identifier')
                customer_code = self._extract_field_by_role(first_row, 'customer')
                rate = self._extract_field_by_role(first_row, 'rate')
                tr_id = self._extract_field_by_role(first_row, 'transaction_id')
                date_field = self._extract_field_by_role(first_row, 'date')
                
                if not identifier or not customer_code:
                    continue
                
                # پیدا کردن Product
                product = self._get_product_by_identifier(identifier)
                if not product:
                    continue
                
                # پیدا یا ایجاد Customer
                customer = self._get_or_create_customer(customer_code)
                
                # محاسبه مبلغ
                amount = Decimal(str(group.total_value)) * Decimal(str(rate)) if rate else None
                
                # ثبت Sale
                sale = SaleV2(
                    product_id=product.id,
                    customer_id=customer.id,
                    transaction_id=tr_id,
                    quantity=Decimal(str(group.total_value)),
                    rate=Decimal(str(rate)) if rate else None,
                    amount=amount,
                    sale_date=self._parse_date(date_field),
                    is_grouped=True if group.row_count > 1 else False,
                    grouped_row_count=group.row_count,
                    group_id=group.group_id,
                    source_sheet=sheet_name,
                    raw_data_ids=group.raw_data_ids,
                    extra_data=first_row
                )
                
                self.db.add(sale)
                stats["new_sales"] += 1
                
                if group.row_count > 1:
                    stats["grouped_transactions"] += 1
                
                # بروزرسانی Product
                product.total_sold = (product.total_sold or 0) + Decimal(str(group.total_value))
                product.current_balance = (product.initial_balance or 0) - (product.total_sold or 0)
                product.last_activity_at = datetime.now()
                
                # بروزرسانی Customer
                customer.total_purchases += 1
                customer.total_spent = (customer.total_spent or 0) + (amount or 0)
                customer.last_purchase_at = datetime.now()
                
                # علامت‌گذاری raw_data
                for raw_id in group.raw_data_ids:
                    raw = self.db.query(RawData).get(raw_id)
                    if raw:
                        raw.is_processed = True
                        raw.processed_at = datetime.now()
                
                stats["processed_rows"] += group.row_count
                
            except Exception as e:
                stats["errors"] += 1
                print(f"❌ خطا در پردازش گروه فروش: {e}")
        
        return stats
    
    def _process_sales(
        self, 
        rows: List[Dict[str, Any]], 
        sheet_name: str
    ) -> Dict[str, int]:
        """
        پردازش فروش بدون گروه‌بندی
        """
        # مشابه _process_sales_with_grouping اما بدون SmartGrouper
        # هر ردیف = یک Sale
        pass
    
    def _process_bonuses(
        self, 
        rows: List[Dict[str, Any]], 
        sheet_name: str
    ) -> Dict[str, int]:
        """
        پردازش بونوس‌ها/سیلور
        """
        stats = {"processed_rows": 0, "new_bonuses": 0, "errors": 0}
        
        for row in rows:
            try:
                identifier = self._extract_field_by_role(row, 'identifier')
                value = self._extract_field_by_role(row, 'value')
                date_field = self._extract_field_by_role(row, 'date')
                
                if not identifier:
                    continue
                
                # پیدا کردن Product
                product = self._get_product_by_identifier(identifier)
                if not product:
                    continue
                
                # ثبت Bonus
                bonus = BonusV2(
                    product_id=product.id,
                    quantity=Decimal(str(value)) if value else 0,
                    bonus_date=self._parse_date(date_field),
                    source_sheet=sheet_name,
                    raw_data_id=row.get('_raw_id'),
                    extra_data=row
                )
                
                self.db.add(bonus)
                stats["new_bonuses"] += 1
                
                # بروزرسانی Product
                product.total_bonus = (product.total_bonus or 0) + Decimal(str(value))
                
                # علامت‌گذاری raw_data
                raw = self.db.query(RawData).get(row.get('_raw_id'))
                if raw:
                    raw.is_processed = True
                    raw.processed_at = datetime.now()
                
                stats["processed_rows"] += 1
                
            except Exception as e:
                stats["errors"] += 1
                print(f"❌ خطا در پردازش بونوس: {e}")
        
        return stats
    
    # Helper Methods
    # ===============
    
    def _extract_field_by_role(self, row: Dict[str, Any], role_name: str) -> Any:
        """
        استخراج مقدار فیلد بر اساس نقش
        """
        # پیدا کردن فیلدهایی که این نقش را دارند
        roles = self.db.query(FieldRole).filter(
            FieldRole.name == role_name,
            FieldRole.is_active == True
        ).all()
        
        if not roles:
            return None
        
        # پیدا کردن CustomFieldهایی که این نقش را دارند
        for role in roles:
            fields = self.db.query(CustomField).filter(
                CustomField.role_id == role.id,
                CustomField.is_active == True
            ).all()
            
            for field in fields:
                value = row.get(field.name)
                if value is not None:
                    return value
        
        return None
    
    def _get_grouping_fields(self) -> List[str]:
        """
        دریافت فیلدهایی که برای گروه‌بندی استفاده می‌شوند
        """
        roles = self.db.query(FieldRole).filter(
            FieldRole.used_in_grouping == True,
            FieldRole.is_active == True
        ).order_by(FieldRole.display_order).all()
        
        field_names = []
        for role in roles:
            fields = self.db.query(CustomField).filter(
                CustomField.role_id == role.id,
                CustomField.is_active == True
            ).all()
            
            for field in fields:
                field_names.append(field.name)
        
        return field_names or ['date', 'code', 'customer', 'rate']
    
    def _get_value_field_name(self) -> str:
        """
        نام فیلدی که مقدار را نگه می‌دارد
        """
        role = self.db.query(FieldRole).filter(
            FieldRole.name == 'value',
            FieldRole.is_active == True
        ).first()
        
        if role:
            field = self.db.query(CustomField).filter(
                CustomField.role_id == role.id,
                CustomField.is_active == True
            ).first()
            
            if field:
                return field.name
        
        return 'Value'  # پیش‌فرض
    
    def _get_or_create_product(
        self, 
        identifier: str, 
        initial_balance: float = 0,
        source_sheet: str = None,
        extra_data: Dict = None
    ) -> Optional[ProductV2]:
        """
        پیدا یا ایجاد Product
        """
        product = self.db.query(ProductV2).filter(
            ProductV2.identifier == identifier
        ).first()
        
        if not product:
            product = ProductV2(
                identifier=identifier,
                initial_balance=Decimal(str(initial_balance)) if initial_balance else 0,
                current_balance=Decimal(str(initial_balance)) if initial_balance else 0,
                source_sheet=source_sheet,
                extra_data=extra_data
            )
            self.db.add(product)
            self.db.flush()  # برای دریافت ID
        
        return product
    
    def _get_product_by_identifier(self, identifier: str) -> Optional[ProductV2]:
        """
        پیدا کردن Product با شناسه
        """
        return self.db.query(ProductV2).filter(
            ProductV2.identifier == identifier
        ).first()
    
    def _get_or_create_customer(self, customer_code: str) -> CustomerV2:
        """
        پیدا یا ایجاد Customer
        """
        customer = self.db.query(CustomerV2).filter(
            CustomerV2.customer_code == customer_code
        ).first()
        
        if not customer:
            customer = CustomerV2(
                customer_code=customer_code,
                first_purchase_at=datetime.now()
            )
            self.db.add(customer)
            self.db.flush()
        
        return customer
    
    def _parse_date(self, date_str: Any) -> Optional[datetime]:
        """
        تبدیل رشته به تاریخ
        """
        if not date_str:
            return None
        
        if isinstance(date_str, datetime):
            return date_str
        
        # تلاش برای پارس تاریخ
        try:
            from dateutil import parser
            return parser.parse(str(date_str))
        except:
            return None
