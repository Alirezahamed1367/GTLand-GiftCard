"""
Smart Financial Converter - با استفاده از Data Analyzer
فقط sheets شناسایی شده را با mapping صحیح تبدیل می‌کند
"""
from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from app.models.sales_data import SalesData
from app.models.financial import (
    FinancialSessionLocal, 
    Sale as Transaction, 
    AccountInventory as Account, 
    Customer, 
    Department
)
from app.core.database import SessionLocal
from app.core.logger import app_logger
from .data_analyzer import DataAnalyzer, SheetAnalysis


class SmartFinancialConverter:
    """
    مبدل هوشمند مالی - با تحلیل خودکار sheets
    """
    
    def __init__(self):
        self.logger = app_logger
        self.analyzer = DataAnalyzer()
        self.sheet_analyses: Dict[int, SheetAnalysis] = {}
    
    def initialize(self):
        """راه‌اندازی و تحلیل sheets"""
        self.logger.info("🔍 تحلیل sheets...")
        analyses = self.analyzer.analyze_all_sheets()
        
        for analysis in analyses:
            self.sheet_analyses[analysis.sheet_id] = analysis
            
        sale_sheets = [a for a in analyses if a.sheet_type == 'sale' and a.confidence > 0.5]
        self.logger.info(f"✅ {len(sale_sheets)} sale sheet شناسایی شد")
        
        return len(sale_sheets) > 0
    
    def convert_sale_record(self, sales_data: SalesData, analysis: SheetAnalysis, 
                           financial_db, phase1_db) -> Optional[Transaction]:
        """
        تبدیل یک رکورد فروش به Transaction
        با استفاده از field mapping شناسایی شده
        """
        try:
            data = sales_data.data
            if not data:
                return None
            
            mapping = analysis.field_mapping
            
            # استخراج فیلدهای اصلی با mapping
            label = data.get(mapping.label) if mapping.label else None
            customer_name = data.get(mapping.customer) if mapping.customer else None
            rate_str = data.get(mapping.rate) if mapping.rate else None
            price_str = data.get(mapping.price) if mapping.price else None
            
            # اعتبارسنجی
            if not label or not customer_name:
                return None
            
            # تبدیل rate و price
            try:
                rate = Decimal(str(rate_str).replace(',', '')) if rate_str else Decimal('0')
                price = Decimal(str(price_str).replace(',', '')) if price_str else Decimal('0')
            except:
                return None
            
            if rate <= 0 or price <= 0:
                return None
            
            # پیدا کردن دپارتمان
            dept_code = self._detect_department(analysis.sheet_name)
            department = financial_db.query(Department).filter(
                Department.code == dept_code
            ).first()
            
            if not department:
                self.logger.warning(f"دپارتمان {dept_code} یافت نشد")
                return None
            
            # پیدا یا ساخت Account
            account = self._get_or_create_account(
                financial_db, label, department.id, sales_data.id
            )
            
            # پیدا یا ساخت Customer
            customer = self._get_or_create_customer(
                financial_db, customer_name, department.id
            )
            
            # چک duplicate
            existing = financial_db.query(Transaction).filter(
                Transaction.sales_data_id == sales_data.id
            ).first()
            
            if existing:
                return None
            
            # تولید transaction_code
            from datetime import date
            today = date.today()
            last_trx = financial_db.query(Transaction).order_by(Transaction.id.desc()).first()
            if last_trx and last_trx.transaction_code:
                try:
                    last_num = int(last_trx.transaction_code.split('-')[-1])
                    new_num = last_num + 1
                except:
                    new_num = 1
            else:
                new_num = 1
            
            transaction_code = f"TRX-{today.strftime('%Y%m%d')}-{new_num:04d}"
            
            # محاسبه cost و profit (نمیدونیم قیمت خرید واقعی، فرض صفر)
            cost_usdt = Decimal('0')  # تا وقتی account purchase price وارد بشه
            profit_usdt = price - cost_usdt
            
            # ساخت Transaction
            transaction = Transaction(
                account_id=account.id,
                customer_id=customer.id,
                department_id=department.id,
                transaction_code=transaction_code,
                product_type='PUBG',
                product_name='Unknown',
                amount_sold=Decimal('0'),  # نمیدونیم چقدر فروخته
                amount_unit='UC',
                consumed_from_account=Decimal('0'),
                sale_rate=rate,
                sale_price_usdt=price,
                payment_currency='USDT',
                transaction_date=today,
                status='completed',
                is_paid=True,
                cost_usdt=cost_usdt,
                profit_usdt=profit_usdt,
                profit_margin=Decimal('0'),
                notes=f"Imported from {analysis.sheet_name}",
                sales_data_id=sales_data.id
            )
            
            financial_db.add(transaction)
            financial_db.flush()
            
            # بروزرسانی آمار Account
            account.total_sales_amount_usdt += price
            account.total_sales_count += 1
            
            return transaction
            
        except Exception as e:
            self.logger.error(f"خطا در تبدیل sales_data #{sales_data.id}: {str(e)}")
            return None
    
    def _detect_department(self, sheet_name: str) -> str:
        """تشخیص دپارتمان از نام sheet"""
        sheet_lower = sheet_name.lower()
        
        # PUBG = GIFTCARD Department
        if 'pubg' in sheet_lower or 'gift' in sheet_lower:
            return 'GIFTCARD'
        
        # RG = TOPUP Department  
        if 'rg' in sheet_lower or 'topup' in sheet_lower or 'top-up' in sheet_lower:
            return 'TOPUP'
        
        return 'GIFTCARD'  # default
    
    def _get_or_create_account(self, db, label: str, dept_id: int, sales_data_id: int) -> Account:
        """پیدا کردن یا ساخت Account"""
        account = db.query(Account).filter(
            Account.label == label,
            Account.department_id == dept_id
        ).first()
        
        if not account:
            # ساخت product_code
            dept = db.query(Department).get(dept_id)
            last_account = db.query(Account).filter(
                Account.department_id == dept_id
            ).order_by(Account.id.desc()).first()
            
            if last_account and last_account.product_code:
                try:
                    last_num = int(last_account.product_code.split('-')[1])
                    new_num = last_num + 1
                except:
                    new_num = 1
            else:
                new_num = 1
            
            product_code = f"P{dept.id}-{new_num:04d}"
            
            account = Account(
                department_id=dept_id,
                label=label,
                product_code=product_code,
                initial_balance=Decimal('0'),  # نمیدونیم موجودی اولیه چیه
                current_balance=Decimal('0'),
                balance_unit='UC',
                purchase_price_usdt=Decimal('0'),  # نمیدونیم قیمت خرید چیه
                status='active',
                notes=f"Auto-created from sales_data #{sales_data_id}"
            )
            db.add(account)
            db.flush()
            
            self.logger.info(f"✅ Account جدید: {label} ({product_code})")
        
        return account
    
    def _get_or_create_customer(self, db, name: str, dept_id: int) -> Customer:
        """پیدا کردن یا ساخت Customer"""
        customer = db.query(Customer).filter(
            Customer.name == name
        ).first()
        
        if not customer:
            dept = db.query(Department).get(dept_id)
            last_customer = db.query(Customer).filter(
                Customer.department_id == dept_id
            ).order_by(Customer.id.desc()).first()
            
            if last_customer and last_customer.customer_code:
                try:
                    last_num = int(last_customer.customer_code.split('-')[1])
                    new_num = last_num + 1
                except:
                    new_num = 1
            else:
                new_num = 1
            
            customer_code = f"C{dept.id}-{new_num:04d}"
            
            customer = Customer(
                department_id=dept_id,
                name=name,
                customer_code=customer_code,
                account_balance_usdt=Decimal('0'),
                account_balance_irr=Decimal('0'),
                status='active'
            )
            db.add(customer)
            db.flush()
            
            self.logger.info(f"✅ Customer جدید: {name} ({customer_code})")
        
        return customer
    
    def convert_batch(self, limit: int = 100, skip_existing: bool = True) -> Dict[str, Any]:
        """
        تبدیل دسته‌ای رکوردها
        فقط sale sheets با confidence > 50% را پردازش می‌کند
        """
        if not self.sheet_analyses:
            self.initialize()
        
        phase1_db = SessionLocal()
        financial_db = FinancialSessionLocal()
        
        stats = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
        
        try:
            # فقط sale sheets
            sale_sheet_ids = [
                sid for sid, analysis in self.sheet_analyses.items()
                if analysis.sheet_type == 'sale' and analysis.confidence > 0.5
            ]
            
            if not sale_sheet_ids:
                self.logger.warning("هیچ sale sheet معتبری یافت نشد")
                return stats
            
            self.logger.info(f"🔄 پردازش {len(sale_sheet_ids)} sale sheet...")
            
            # گرفتن رکوردها
            query = phase1_db.query(SalesData).filter(
                SalesData.sheet_config_id.in_(sale_sheet_ids)
            )
            
            if skip_existing:
                # رکوردهایی که قبلاً convert نشدن
                converted_ids = {t.sales_data_id for t in financial_db.query(Transaction.sales_data_id).all()}
                query = query.filter(~SalesData.id.in_(converted_ids))
            
            records = query.limit(limit).all()
            
            self.logger.info(f"📦 {len(records)} رکورد برای تبدیل...")
            
            for record in records:
                stats['processed'] += 1
                
                analysis = self.sheet_analyses.get(record.sheet_config_id)
                if not analysis:
                    stats['skipped'] += 1
                    continue
                
                transaction = self.convert_sale_record(record, analysis, financial_db, phase1_db)
                
                if transaction:
                    stats['successful'] += 1
                    if stats['successful'] % 10 == 0:
                        financial_db.commit()
                        self.logger.info(f"✅ {stats['successful']} رکورد تبدیل شد...")
                else:
                    stats['failed'] += 1
            
            financial_db.commit()
            self.logger.info(f"✅ تبدیل تکمیل: {stats['successful']} موفق، {stats['failed']} ناموفق")
            
        except Exception as e:
            financial_db.rollback()
            self.logger.error(f"❌ خطا در تبدیل دسته‌ای: {str(e)}")
            stats['errors'].append(str(e))
        finally:
            phase1_db.close()
            financial_db.close()
        
        return stats


if __name__ == "__main__":
    converter = SmartFinancialConverter()
    
    print("\n🚀 Smart Financial Converter")
    print("="*80)
    
    if converter.initialize():
        print("\n📊 تحلیل Sheets:")
        for sid, analysis in converter.sheet_analyses.items():
            if analysis.sheet_type == 'sale':
                print(f"  ✅ {analysis.sheet_name}: {analysis.total_records:,} records")
        
        print("\n🔄 شروع تبدیل...")
        stats = converter.convert_batch(limit=100)
        
        print(f"\n📈 نتایج:")
        print(f"  پردازش شده: {stats['processed']}")
        print(f"  موفق: {stats['successful']}")
        print(f"  ناموفق: {stats['failed']}")
        print(f"  رد شده: {stats['skipped']}")
        
        if stats['errors']:
            print(f"\n❌ خطاها:")
            for error in stats['errors'][:5]:
                print(f"  - {error}")
    else:
        print("❌ هیچ sale sheet معتبری یافت نشد")
    
    print("="*80 + "\n")
