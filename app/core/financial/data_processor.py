"""
Data Processor - پردازشگر داده‌های خام به سیستم جدید
========================================================
تبدیل raw_data به Account, AccountGold, AccountSilver, Sale
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.financial import (
    RawData,
    Account,
    AccountGold,
    AccountSilver,
    Sale,
    SaleType,
    Customer,
    FieldRole
)
from app.core.logger import app_logger


class DataProcessor:
    """
    پردازشگر داده‌های خام
    
    تبدیل raw_data به مدل‌های Label-Based
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.logger = app_logger
    
    def process_raw_data(
        self,
        batch_id: int,
        field_mappings: Dict[str, str]
    ) -> Dict[str, int]:
        """
        پردازش یک batch از داده‌های خام
        
        Args:
            batch_id: شناسه batch
            field_mappings: نگاشت فیلدها {"label": "Account ID", "gold": "Gold Amount", ...}
            
        Returns:
            آمار پردازش
        """
        stats = {
            "processed_rows": 0,
            "new_accounts": 0,
            "new_purchases": 0,
            "new_sales": 0,
            "errors": 0
        }
        
        # دریافت داده‌های خام
        raw_rows = self.db.query(RawData).filter_by(
            batch_id=batch_id,
            status='pending'
        ).all()
        
        for row in raw_rows:
            try:
                data = row.data
                
                # استخراج label (کلید اصلی)
                label = self._extract_field(data, field_mappings.get('label'))
                if not label:
                    self.logger.warning(f"ردیف {row.row_number}: Label یافت نشد")
                    row.status = 'error'
                    row.error_message = "Label not found"
                    stats["errors"] += 1
                    continue
                
                # ایجاد یا دریافت Account
                account = self._get_or_create_account(label, data, field_mappings)
                if account:
                    stats["new_accounts"] += 1
                
                # پردازش بر اساس نوع داده
                sheet_type = row.source_name.lower()
                
                if 'consumed' in sheet_type or 'purchase' in sheet_type:
                    # پردازش خرید (Gold + Silver)
                    self._process_purchase(label, data, field_mappings)
                    stats["new_purchases"] += 1
                
                elif 'sale' in sheet_type or 'gift' in sheet_type or 'platform' in sheet_type:
                    # پردازش فروش
                    self._process_sale(label, data, field_mappings)
                    stats["new_sales"] += 1
                
                row.status = 'processed'
                stats["processed_rows"] += 1
                
            except Exception as e:
                self.logger.error(f"خطا در پردازش ردیف {row.row_number}: {str(e)}")
                row.status = 'error'
                row.error_message = str(e)
                stats["errors"] += 1
        
        self.db.commit()
        return stats
    
    def _get_or_create_account(
        self,
        label: str,
        data: Dict,
        mappings: Dict[str, str]
    ) -> Optional[Account]:
        """ایجاد یا دریافت Account"""
        account = self.db.query(Account).filter_by(label=label).first()
        
        if not account:
            email = self._extract_field(data, mappings.get('email'))
            supplier = self._extract_field(data, mappings.get('supplier'))
            status = self._extract_field(data, mappings.get('status'), 'Consumed')
            
            account = Account(
                label=label,
                email=email,
                supplier=supplier,
                status=status
            )
            self.db.add(account)
            self.db.flush()
            self.logger.info(f"آکانت جدید: {label}")
        
        return account
    
    def _process_purchase(
        self,
        label: str,
        data: Dict,
        mappings: Dict[str, str]
    ):
        """پردازش خرید (Gold + Silver)"""
        # Gold
        gold_qty = self._extract_decimal(data, mappings.get('gold_quantity'))
        purchase_rate = self._extract_decimal(data, mappings.get('purchase_rate'))
        
        if gold_qty and purchase_rate:
            gold = AccountGold(
                label=label,
                gold_quantity=gold_qty,
                purchase_rate=purchase_rate,
                purchase_cost=gold_qty * purchase_rate,
                purchase_date=datetime.now()
            )
            self.db.add(gold)
            self.logger.info(f"خرید گلد: {label} - {gold_qty} @ {purchase_rate}")
        
        # Silver
        silver_qty = self._extract_decimal(data, mappings.get('silver_quantity'))
        if silver_qty:
            silver = AccountSilver(
                label=label,
                silver_quantity=silver_qty,
                bonus_date=datetime.now()
            )
            self.db.add(silver)
            self.logger.info(f"بونوس سیلور: {label} - {silver_qty}")
    
    def _process_sale(
        self,
        label: str,
        data: Dict,
        mappings: Dict[str, str]
    ):
        """پردازش فروش"""
        # تشخیص نوع (gold یا silver)
        sale_type_field = self._extract_field(data, mappings.get('sale_type'))
        sale_type = 'gold' if 'gold' in str(sale_type_field).lower() else 'silver'
        
        quantity = self._extract_decimal(data, mappings.get('quantity'))
        rate = self._extract_decimal(data, mappings.get('rate'))
        customer = self._extract_field(data, mappings.get('customer'), 'Unknown')
        
        if quantity and rate:
            sale = Sale(
                label=label,
                sale_type=sale_type,
                quantity=quantity,
                sale_rate=rate,
                sale_amount=quantity * rate,
                customer=customer,
                sale_date=datetime.now()
            )
            self.db.add(sale)
            self.logger.info(f"فروش: {label} - {sale_type} - {quantity} @ {rate}")
    
    def _extract_field(
        self,
        data: Dict,
        field_name: Optional[str],
        default: str = None
    ) -> Optional[str]:
        """استخراج فیلد از data"""
        if not field_name or field_name not in data:
            return default
        
        value = data.get(field_name)
        if value is None or str(value).strip() == '':
            return default
        
        return str(value).strip()
    
    def _extract_decimal(
        self,
        data: Dict,
        field_name: Optional[str]
    ) -> Optional[Decimal]:
        """استخراج مقدار عددی"""
        value = self._extract_field(data, field_name)
        if not value:
            return None
        
        try:
            # حذف کاراکترهای غیرعددی
            value = value.replace(',', '')
            return Decimal(value)
        except:
            return None
