"""
تبدیل‌گر داده‌های مالی - Financial Data Converter

این ماژول داده‌های خام sales_data را به ساختار مالی تبدیل می‌کند
"""
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from decimal import Decimal
import re

from app.models import SalesData, SheetConfig
from app.models.financial import (
    FinancialSessionLocal,
    Department, 
    AccountInventory as Account, 
    Customer, 
    Sale as Transaction,
    SilverBonus as SilverTransaction
)
from app.core.logger import app_logger


class FinancialConverter:
    """
    کلاس تبدیل داده‌های sales_data به ساختار مالی
    """
    
    def __init__(self):
        """راه‌اندازی Converter"""
        self.logger = app_logger
        self.financial_db = FinancialSessionLocal()
        
        # کش برای سرعت بیشتر
        self.accounts_cache = {}  # {label: Account}
        self.customers_cache = {}  # {name: Customer}
        self.departments_cache = {}  # {id: Department}
        
        # بارگذاری کش
        self._load_cache()
    
    def _load_cache(self):
        """بارگذاری داده‌های پایه در کش"""
        try:
            # بارگذاری دپارتمان‌ها
            departments = self.financial_db.query(Department).all()
            for dept in departments:
                self.departments_cache[dept.id] = dept
                self.departments_cache[dept.code] = dept
            
            # بارگذاری آکانت‌ها
            accounts = self.financial_db.query(Account).all()
            for acc in accounts:
                self.accounts_cache[acc.label] = acc
            
            # بارگذاری مشتریان
            customers = self.financial_db.query(Customer).all()
            for cust in customers:
                self.customers_cache[cust.name] = cust
            
            self.logger.info(f"✅ کش بارگذاری شد: {len(accounts)} آکانت، {len(customers)} مشتری")
            
        except Exception as e:
            self.logger.error(f"خطا در بارگذاری کش: {str(e)}")
    
    def detect_department_from_sheet(self, sheet_name: str) -> Optional[Department]:
        """
        تشخیص دپارتمان از روی نام شیت
        
        Args:
            sheet_name: نام شیت
            
        Returns:
            Department یا None
        """
        sheet_lower = sheet_name.lower()
        
        # کلمات کلیدی برای تشخیص
        giftcard_keywords = ['gift', 'pubg', 'razer', 'xbox', 'psn', 'playstation', 'itunes', 'roblox']
        topup_keywords = ['topup', 'top-up', 'top up', 'cod', 'telegram']
        
        # جستجو در کلمات کلیدی
        for keyword in giftcard_keywords:
            if keyword in sheet_lower:
                return self.departments_cache.get('GIFTCARD')
        
        for keyword in topup_keywords:
            if keyword in sheet_lower:
                return self.departments_cache.get('TOPUP')
        
        # پیش‌فرض: Gift-Card
        return self.departments_cache.get('GIFTCARD')
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """
        تبدیل رشته تاریخ به datetime
        
        Args:
            date_str: رشته تاریخ (مثلاً "10/2/2025")
            
        Returns:
            datetime یا None
        """
        if not date_str:
            return None
        
        try:
            # فرمت‌های مختلف تاریخ
            formats = [
                "%m/%d/%Y",  # 10/2/2025
                "%d/%m/%Y",  # 2/10/2025
                "%Y-%m-%d",  # 2025-10-02
                "%Y/%m/%d",  # 2025/10/02
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(str(date_str).strip(), fmt)
                except:
                    continue
            
            self.logger.warning(f"فرمت تاریخ نامعتبر: {date_str}")
            return None
            
        except Exception as e:
            self.logger.error(f"خطا در پردازش تاریخ '{date_str}': {str(e)}")
            return None
    
    def get_or_create_account(
        self, 
        label: str, 
        department: Department,
        data: Dict
    ) -> Optional[Account]:
        """
        دریافت یا ایجاد آکانت
        
        Args:
            label: لیبل آکانت (G123, K450)
            department: دپارتمان
            data: داده‌های اضافی
            
        Returns:
            Account یا None
        """
        # جستجو در کش
        if label in self.accounts_cache:
            return self.accounts_cache[label]
        
        # جستجو در دیتابیس
        account = self.financial_db.query(Account).filter_by(label=label).first()
        
        if not account:
            # ایجاد آکانت جدید
            try:
                # تولید کد کالا
                count = self.financial_db.query(Account).filter_by(
                    department_id=department.id
                ).count()
                product_code = f"{department.product_code_prefix}{count + 1:04d}"
                
                account = Account(
                    department_id=department.id,
                    label=label,
                    product_code=product_code,
                    product_name=label,
                    initial_balance=Decimal('0'),  # باید از شیت خرید بیاید
                    current_balance=Decimal('0'),
                    purchase_rate=Decimal('0'),
                    purchase_price_usdt=Decimal('0'),
                    purchase_date=datetime.now().date(),
                    status='active'
                )
                
                self.financial_db.add(account)
                self.financial_db.commit()
                self.financial_db.refresh(account)
                
                # اضافه به کش
                self.accounts_cache[label] = account
                
                self.logger.info(f"✅ آکانت جدید ایجاد شد: {label} ({product_code})")
                
            except Exception as e:
                self.financial_db.rollback()
                self.logger.error(f"خطا در ایجاد آکانت {label}: {str(e)}")
                return None
        else:
            # اضافه به کش
            self.accounts_cache[label] = account
        
        return account
    
    def get_or_create_customer(
        self, 
        customer_name: str, 
        department: Department
    ) -> Optional[Customer]:
        """
        دریافت یا ایجاد مشتری
        
        Args:
            customer_name: نام مشتری (PX, P14)
            department: دپارتمان
            
        Returns:
            Customer یا None
        """
        if not customer_name or customer_name.strip() == '':
            return None
        
        customer_name = customer_name.strip()
        
        # جستجو در کش
        cache_key = f"{department.id}_{customer_name}"
        if cache_key in self.customers_cache:
            return self.customers_cache[cache_key]
        
        # جستجو در دیتابیس
        customer = self.financial_db.query(Customer).filter_by(
            department_id=department.id,
            name=customer_name
        ).first()
        
        if not customer:
            # ایجاد مشتری جدید
            try:
                # تولید کد مشتری
                count = self.financial_db.query(Customer).filter_by(
                    department_id=department.id
                ).count()
                customer_code = f"{department.customer_code_prefix}{count + 1:04d}"
                
                customer = Customer(
                    department_id=department.id,
                    customer_code=customer_code,
                    name=customer_name,
                    customer_type='regular',
                    is_active=True
                )
                
                self.financial_db.add(customer)
                self.financial_db.commit()
                self.financial_db.refresh(customer)
                
                # اضافه به کش
                self.customers_cache[cache_key] = customer
                
                self.logger.info(f"✅ مشتری جدید ایجاد شد: {customer_name} ({customer_code})")
                
            except Exception as e:
                self.financial_db.rollback()
                self.logger.error(f"خطا در ایجاد مشتری {customer_name}: {str(e)}")
                return None
        else:
            # اضافه به کش
            self.customers_cache[cache_key] = customer
        
        return customer
    
    def convert_sales_data_to_transaction(
        self, 
        sales_data: SalesData,
        sheet_config: SheetConfig
    ) -> Tuple[bool, Optional[Transaction], str]:
        """
        تبدیل یک رکورد sales_data به Transaction
        
        Args:
            sales_data: داده فروش
            sheet_config: تنظیمات شیت
            
        Returns:
            (موفقیت, Transaction یا None, پیام)
        """
        try:
            data = sales_data.data
            
            # استخراج فیلدها
            label = data.get('Label') or data.get('label') or data.get('LABEL')
            customer_name = data.get('Customer') or data.get('customer')
            rate = data.get('Rate For Sale') or data.get('rate') or data.get('Rate')
            price = data.get('Final Price Sale') or data.get('price') or data.get('Price')
            sold_date = data.get('Sold Date') or data.get('date') or data.get('Date')
            
            # اعتبارسنجی
            if not label:
                return False, None, "Label یافت نشد"
            
            if not rate or not price:
                return False, None, "ریت یا قیمت یافت نشد"
            
            # تشخیص دپارتمان
            department = self.detect_department_from_sheet(sheet_config.name)
            if not department:
                return False, None, "دپارتمان تشخیص داده نشد"
            
            # دریافت/ایجاد آکانت
            account = self.get_or_create_account(label, department, data)
            if not account:
                return False, None, f"خطا در ایجاد آکانت {label}"
            
            # دریافت/ایجاد مشتری
            customer = self.get_or_create_customer(customer_name, department) if customer_name else None
            
            # پردازش تاریخ
            transaction_date = self.parse_date(sold_date)
            if not transaction_date:
                transaction_date = datetime.now()
            
            # تولید کد معامله
            transaction_code = f"TRX-{transaction_date.strftime('%Y%m%d')}-{sales_data.id:06d}"
            
            # بررسی تکراری
            existing = self.financial_db.query(Transaction).filter_by(
                sales_data_id=sales_data.id
            ).first()
            if existing:
                return False, None, "این معامله قبلاً ثبت شده"
            
            # ایجاد Transaction
            transaction = Transaction(
                department_id=department.id,
                account_id=account.id,
                customer_id=customer.id if customer else None,
                transaction_code=transaction_code,
                product_type=self._detect_product_type(sheet_config.name),
                product_name=f"محصول از {label}",
                amount_sold=Decimal(str(price)),
                amount_unit='USDT',
                consumed_from_account=Decimal(str(price)),  # فرضی
                sale_rate=Decimal(str(rate)),
                sale_price_usdt=Decimal(str(price)),
                payment_currency='USDT',
                transaction_date=transaction_date.date(),
                status='completed',
                cost_usdt=Decimal('0'),  # باید محاسبه شود
                profit_usdt=Decimal('0'),  # باید محاسبه شود
                source_sheet_id=sheet_config.id,
                source_row_number=sales_data.row_number,
                sales_data_id=sales_data.id
            )
            
            # محاسبه سود
            if account.purchase_rate > 0:
                transaction.calculate_profit(account.purchase_rate)
            
            self.financial_db.add(transaction)
            self.financial_db.commit()
            self.financial_db.refresh(transaction)
            
            return True, transaction, "معامله با موفقیت ثبت شد"
            
        except Exception as e:
            self.financial_db.rollback()
            self.logger.error(f"خطا در تبدیل sales_data #{sales_data.id}: {str(e)}")
            return False, None, f"خطا: {str(e)}"
    
    def _detect_product_type(self, sheet_name: str) -> str:
        """تشخیص نوع محصول از روی نام شیت"""
        sheet_lower = sheet_name.lower()
        
        if 'pubg' in sheet_lower:
            return 'PUBG'
        elif 'cod' in sheet_lower or 'call of duty' in sheet_lower:
            return 'COD'
        elif 'roblox' in sheet_lower:
            return 'ROBLOX'
        elif 'ps' in sheet_lower or 'playstation' in sheet_lower:
            return 'PSN'
        elif 'xbox' in sheet_lower:
            return 'XBOX'
        elif 'razer' in sheet_lower:
            return 'RAZER'
        else:
            return 'OTHER'
    
    def convert_batch(
        self, 
        sheet_config_id: int,
        limit: int = 100
    ) -> Dict:
        """
        تبدیل دسته‌ای sales_data به Transaction
        
        Args:
            sheet_config_id: شناسه شیت
            limit: تعداد رکوردها
            
        Returns:
            آمار تبدیل
        """
        from app.models.base import SessionLocal
        
        main_db = SessionLocal()
        
        try:
            # دریافت تنظیمات شیت
            sheet_config = main_db.query(SheetConfig).filter_by(id=sheet_config_id).first()
            if not sheet_config:
                return {'success': False, 'message': 'Sheet Config یافت نشد'}
            
            # دریافت sales_data هایی که هنوز تبدیل نشده‌اند
            sales_data_list = main_db.query(SalesData).filter_by(
                sheet_config_id=sheet_config_id
            ).limit(limit).all()
            
            stats = {
                'total': len(sales_data_list),
                'success': 0,
                'failed': 0,
                'errors': []
            }
            
            for sales_data in sales_data_list:
                success, transaction, message = self.convert_sales_data_to_transaction(
                    sales_data, sheet_config
                )
                
                if success:
                    stats['success'] += 1
                else:
                    stats['failed'] += 1
                    stats['errors'].append({
                        'sales_data_id': sales_data.id,
                        'message': message
                    })
            
            main_db.close()
            return stats
            
        except Exception as e:
            main_db.close()
            self.logger.error(f"خطا در تبدیل دسته‌ای: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    def __del__(self):
        """بستن اتصال دیتابیس"""
        if hasattr(self, 'financial_db'):
            self.financial_db.close()
