"""
پردازشگر پویا - با استفاده از Field Mapping
این پردازشگر از Mapping های تعریف شده توسط کاربر استفاده می‌کند
"""
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Optional, Any
from app.models.financial import (
    SheetImport, RawData, FieldMapping, 
    Account, AccountGold, AccountSilver, Sale, Platform,
    SheetType, TargetField, DataType, TransferStatus
)
import logging

logger = logging.getLogger(__name__)


class DynamicDataProcessor:
    """
    پردازشگر پویا - داده‌های خام را بر اساس Mapping پردازش می‌کند
    
    جریان کار:
    1. بارگذاری Mappings برای یک SheetImport
    2. خواندن RawData های پردازش نشده
    3. استخراج فیلدها بر اساس Mapping
    4. ایجاد/به‌روزرسانی Account, AccountGold, AccountSilver, Sale
    5. علامت‌گذاری processed=True
    """
    
    def __init__(self, session: Session):
        self.session = session
        self.mappings: Dict[TargetField, FieldMapping] = {}
        self.sheet_import: Optional[SheetImport] = None
    
    def process_sheet(self, sheet_import_id: int) -> Dict[str, Any]:
        """
        پردازش یک شیت کامل
        
        Returns:
            Dict با آمار: total, processed, errors
        """
        # بارگذاری SheetImport
        self.sheet_import = self.session.query(SheetImport).get(sheet_import_id)
        if not self.sheet_import:
            raise ValueError(f"SheetImport با ID {sheet_import_id} یافت نشد")
        
        # بارگذاری Mappings
        self._load_mappings(sheet_import_id)
        
        if not self.mappings:
            raise ValueError("هیچ Field Mapping تعریف نشده! ابتدا Mapping را انجام دهید.")
        
        # بررسی نوع شیت
        sheet_type = self.sheet_import.sheet_type
        
        # خواندن داده‌های پردازش نشده و منتقل نشده
        raw_data_list = self.session.query(RawData).filter_by(
            sheet_import_id=sheet_import_id,
            processed=False,
            transferred=False  # 🆕 فقط داده‌های منتقل نشده
        ).all()
        
        stats = {
            'total': len(raw_data_list),
            'processed': 0,
            'errors': 0,
            'error_details': []
        }
        
        logger.info(f"شروع پردازش {stats['total']} سطر از شیت '{self.sheet_import.sheet_name}'")
        
        # پردازش هر سطر
        for raw_data in raw_data_list:
            try:
                if sheet_type == SheetType.PURCHASE:
                    self._process_purchase_row(raw_data)
                elif sheet_type == SheetType.SALE:
                    self._process_sale_row(raw_data)
                elif sheet_type == SheetType.BONUS:
                    self._process_bonus_row(raw_data)
                else:
                    logger.warning(f"نوع شیت '{sheet_type}' پشتیبانی نمی‌شود")
                    continue
                
                # علامت‌گذاری به عنوان پردازش شده
                raw_data.processed = True
                
                # 🆕 علامت‌گذاری به عنوان منتقل شده
                raw_data.transferred = True
                raw_data.transferred_at = datetime.now()
                raw_data.transfer_status = TransferStatus.TRANSFERRED
                
                stats['processed'] += 1
                
            except Exception as e:
                stats['errors'] += 1
                error_msg = f"سطر {raw_data.row_number}: {str(e)}"
                stats['error_details'].append(error_msg)
                raw_data.processing_errors = error_msg
                
                # 🆕 علامت‌گذاری خطا در انتقال
                raw_data.transfer_status = TransferStatus.FAILED
                raw_data.transfer_error = error_msg
                
                logger.error(error_msg)
        
        # به‌روزرسانی آمار SheetImport
        self.sheet_import.processed_rows = stats['processed']
        
        # Commit
        self.session.commit()
        
        logger.info(f"پردازش تکمیل شد: {stats['processed']} موفق، {stats['errors']} خطا")
        
        return stats
    
    def _load_mappings(self, sheet_import_id: int):
        """بارگذاری Mappings به صورت Dict"""
        mappings = self.session.query(FieldMapping).filter_by(
            sheet_import_id=sheet_import_id
        ).all()
        
        self.mappings = {m.target_field: m for m in mappings}
        
        logger.info(f"بارگذاری {len(self.mappings)} Field Mapping")
    
    def _extract_field(self, raw_data: RawData, target_field: TargetField) -> Optional[Any]:
        """
        استخراج مقدار یک فیلد از RawData بر اساس Mapping
        
        Args:
            raw_data: داده خام
            target_field: نقش فیلد مورد نظر
        
        Returns:
            مقدار استخراج شده یا None
        """
        if target_field not in self.mappings:
            return None
        
        mapping = self.mappings[target_field]
        source_column = mapping.source_column
        
        # استخراج مقدار خام
        raw_value = raw_data.data.get(source_column)
        
        if raw_value is None or raw_value == '':
            if mapping.is_required:
                raise ValueError(f"فیلد '{source_column}' اجباری است ولی خالی است")
            return mapping.default_value
        
        # تبدیل بر اساس نوع داده
        try:
            if mapping.data_type == DataType.TEXT:
                return str(raw_value).strip()
            
            elif mapping.data_type == DataType.DECIMAL:
                # پاک‌سازی عدد (حذف کاما، فاصله، ...)
                clean_value = str(raw_value).replace(',', '').replace('/', '.').strip()
                return Decimal(clean_value) if clean_value else None
            
            elif mapping.data_type == DataType.INTEGER:
                clean_value = str(raw_value).replace(',', '').strip()
                return int(float(clean_value)) if clean_value else None
            
            elif mapping.data_type == DataType.DATE:
                # پردازش تاریخ (ساده‌سازی شده - باید بر اساس فرمت دقیق باشد)
                if isinstance(raw_value, datetime):
                    return raw_value
                # TODO: پردازش فرمت‌های مختلف تاریخ
                return None
            
            elif mapping.data_type == DataType.BOOLEAN:
                return str(raw_value).lower() in ('true', 'yes', '1', 'بله', 'فعال')
            
        except Exception as e:
            raise ValueError(f"خطا در تبدیل '{source_column}': {str(e)}")
        
        return raw_value
    
    def _process_purchase_row(self, raw_data: RawData):
        """پردازش یک سطر خرید"""
        # استخراج فیلدها
        label = self._extract_field(raw_data, TargetField.ACCOUNT_ID)
        email = self._extract_field(raw_data, TargetField.EMAIL)
        supplier = self._extract_field(raw_data, TargetField.SUPPLIER)
        gold_quantity = self._extract_field(raw_data, TargetField.GOLD_QUANTITY)
        purchase_rate = self._extract_field(raw_data, TargetField.PURCHASE_RATE)
        purchase_cost = self._extract_field(raw_data, TargetField.PURCHASE_COST)
        purchase_date = self._extract_field(raw_data, TargetField.PURCHASE_DATE)
        silver_bonus = self._extract_field(raw_data, TargetField.SILVER_BONUS)
        
        if not label:
            raise ValueError("Label (account_id) یافت نشد")
        
        # ایجاد/به‌روزرسانی Account
        account = self.session.query(Account).filter_by(label=label).first()
        
        if not account:
            account = Account(
                label=label,
                email=email,
                supplier=supplier,
                status='active'
            )
            self.session.add(account)
            logger.info(f"✅ Account جدید: {label}")
        else:
            # به‌روزرسانی اطلاعات
            if email:
                account.email = email
            if supplier:
                account.supplier = supplier
        
        # ایجاد AccountGold
        if gold_quantity:
            # محاسبه خودکار purchase_cost اگر نباشد
            if not purchase_cost and purchase_rate:
                purchase_cost = gold_quantity * purchase_rate
            elif not purchase_rate and purchase_cost:
                purchase_rate = purchase_cost / gold_quantity if gold_quantity > 0 else Decimal(0)
            
            gold_purchase = AccountGold(
                label=label,
                gold_quantity=gold_quantity,
                purchase_rate=purchase_rate or Decimal(0),
                purchase_cost=purchase_cost or Decimal(0),
                purchase_date=purchase_date
            )
            self.session.add(gold_purchase)
            logger.debug(f"  → Gold: {gold_quantity} @ {purchase_rate}")
        
        # ایجاد AccountSilver (بونوس)
        if silver_bonus:
            silver = AccountSilver(
                label=label,
                silver_quantity=silver_bonus
            )
            self.session.add(silver)
            logger.debug(f"  → Silver Bonus: {silver_bonus}")
    
    def _process_sale_row(self, raw_data: RawData):
        """پردازش یک سطر فروش با محاسبه دقیق بهای تمام شده"""
        # استخراج فیلدها
        label = self._extract_field(raw_data, TargetField.ACCOUNT_ID)
        sale_quantity = self._extract_field(raw_data, TargetField.SALE_QUANTITY)
        sale_rate = self._extract_field(raw_data, TargetField.SALE_RATE)
        sale_type = self._extract_field(raw_data, TargetField.SALE_TYPE)
        customer_code = self._extract_field(raw_data, TargetField.CUSTOMER_CODE)
        sale_date = self._extract_field(raw_data, TargetField.SALE_DATE)
        staff_profit = self._extract_field(raw_data, TargetField.STAFF_PROFIT)
        
        if not label:
            raise ValueError("Label (account_id) یافت نشد")
        
        if not sale_quantity or not sale_rate:
            raise ValueError("مقدار فروش یا نرخ فروش یافت نشد")
        
        # بررسی وجود Account
        account = self.session.query(Account).filter_by(label=label).first()
        if not account:
            raise ValueError(f"Account با label '{label}' یافت نشد. ابتدا خرید را وارد کنید.")
        
        # تشخیص نوع فروش (اگر مشخص نشده)
        if not sale_type:
            sale_type = 'gold'  # پیش‌فرض
        else:
            sale_type = sale_type.lower()
        
        # محاسبه مبلغ فروش
        sale_amount = sale_quantity * sale_rate
        
        # 🚀 محاسبه بهای تمام شده
        cost_basis = self._calculate_cost_basis(account, sale_type, sale_quantity)
        
        # 🚀 محاسبه سود
        profit = sale_amount - cost_basis
        
        # ایجاد Sale
        sale = Sale(
            label=label,
            platform=self.sheet_import.platform,  # از SheetImport
            sale_type=sale_type,
            quantity=sale_quantity,
            sale_rate=sale_rate,
            sale_amount=sale_amount,
            cost_basis=cost_basis,  # ✅ اضافه شد
            profit=profit,  # ✅ اضافه شد
            customer=customer_code,
            sale_date=sale_date,
            staff_profit=staff_profit,
            source_sheet=self.sheet_import.sheet_name
        )
        self.session.add(sale)
        logger.debug(f"✅ Sale: {label} → {sale_quantity} {sale_type} @ {sale_rate} | Cost: {cost_basis}, Profit: {profit}")
    
    def _calculate_cost_basis(self, account: Account, sale_type: str, quantity: Decimal) -> Decimal:
        """
        محاسبه بهای تمام شده بر اساس نرخ خرید آکانت
        
        نکته مهم: هر آکانت یکبار خریداری می‌شود با یک نرخ ثابت.
        این نرخ برای تمام فروش‌های آن آکانت استفاده می‌شود.
        """
        if sale_type == 'gold':
            # پیدا کردن خریدهای گلد این آکانت
            gold_purchases = self.session.query(AccountGold).filter_by(
                label=account.label
            ).all()
            
            if not gold_purchases:
                logger.warning(f"⚠️ Account '{account.label}' هیچ خرید گلدی ندارد! Cost=0")
                return Decimal('0')
            
            # محاسبه میانگین وزنی نرخ خرید
            total_gold = sum(p.gold_quantity for p in gold_purchases)
            total_cost = sum(p.purchase_cost for p in gold_purchases)
            
            if total_gold == 0:
                return Decimal('0')
            
            avg_price = total_cost / total_gold
            cost_basis = avg_price * quantity
            
            logger.debug(f"  Gold: {quantity} × {avg_price} = {cost_basis}")
            return cost_basis
        
        elif sale_type == 'silver':
            # سیلور رایگان است → Cost = 0
            logger.debug(f"  Silver: رایگان → Cost=0")
            return Decimal('0')
        
        else:
            logger.warning(f"⚠️ نوع فروش نامشخص: {sale_type}, Cost=0")
            return Decimal('0')
    
    def _process_bonus_row(self, raw_data: RawData):
        """پردازش یک سطر بونوس/سیلور"""
        label = self._extract_field(raw_data, TargetField.ACCOUNT_ID)
        silver_bonus = self._extract_field(raw_data, TargetField.SILVER_BONUS)
        
        if not label:
            raise ValueError("Label (account_id) یافت نشد")
        
        if not silver_bonus:
            raise ValueError("مقدار Silver یافت نشد")
        
        # بررسی Account
        account = self.session.query(Account).filter_by(label=label).first()
        if not account:
            raise ValueError(f"Account با label '{label}' یافت نشد")
        
        # ایجاد AccountSilver
        silver = AccountSilver(
            label=label,
            silver_quantity=silver_bonus
        )
        self.session.add(silver)
        logger.debug(f"✅ Silver Bonus: {label} → {silver_bonus}")


class DiscrepancyChecker:
    """
    بررسی مغایرت‌ها - مقایسه سود محاسبه شده با سود پرسنل
    """
    
    def __init__(self, session: Session):
        self.session = session
    
    def check_all_accounts(self) -> List[Dict[str, Any]]:
        """
        بررسی تمام آکانت‌ها برای مغایرت
        
        Returns:
            لیست مغایرت‌ها
        """
        from app.core.financial.calculation_engine import CalculationEngine
        
        calc_engine = CalculationEngine(self.session)
        discrepancies = []
        
        # بارگذاری تمام Account ها
        accounts = self.session.query(Account).all()
        
        for account in accounts:
            label = account.label
            
            # محاسبه سود سیستم
            summary = calc_engine.calculate_label_summary(label)
            calculated_profit = summary.get('total_profit', Decimal(0))
            
            # گرفتن سود پرسنل (از Sale های این label)
            sales = self.session.query(Sale).filter_by(label=label).all()
            staff_profits = [s.staff_profit for s in sales if s.staff_profit]
            
            if not staff_profits:
                continue  # سود پرسنل ثبت نشده
            
            staff_profit_total = sum(staff_profits)
            
            # محاسبه اختلاف
            diff = calculated_profit - staff_profit_total
            diff_percent = (diff / calculated_profit * 100) if calculated_profit else Decimal(0)
            
            # اگر اختلاف معنادار باشد (بیشتر از 1%)
            if abs(diff_percent) > 1:
                discrepancies.append({
                    'label': label,
                    'calculated_profit': float(calculated_profit),
                    'staff_profit': float(staff_profit_total),
                    'discrepancy': float(diff),
                    'discrepancy_percent': float(diff_percent)
                })
                
                logger.warning(
                    f"⚠️ مغایرت {label}: "
                    f"محاسبه={calculated_profit}, پرسنل={staff_profit_total}, "
                    f"اختلاف={diff} ({diff_percent:.2f}%)"
                )
        
        return discrepancies
    
    def save_discrepancy_report(self, discrepancies: List[Dict[str, Any]]):
        """ذخیره گزارش مغایرت‌ها در دیتابیس"""
        from app.models.financial import DiscrepancyReport
        
        # حذف گزارش‌های قبلی
        self.session.query(DiscrepancyReport).delete()
        
        # ایجاد گزارش‌های جدید
        for disc in discrepancies:
            report = DiscrepancyReport(
                label=disc['label'],
                calculated_profit=str(disc['calculated_profit']),
                staff_profit=str(disc['staff_profit']),
                discrepancy=str(disc['discrepancy']),
                discrepancy_percent=f"{disc['discrepancy_percent']:.2f}%"
            )
            self.session.add(report)
        
        self.session.commit()
        logger.info(f"✅ {len(discrepancies)} مغایرت ذخیره شد")


def create_platform_if_not_exists(session: Session, platform_code: str, platform_name: str = None):
    """ایجاد Platform اگر وجود نداشته باشد"""
    platform = session.query(Platform).filter_by(code=platform_code).first()
    
    if not platform:
        platform = Platform(
            code=platform_code,
            name=platform_name or platform_code.title(),
            is_active=True
        )
        session.add(platform)
        session.commit()
        logger.info(f"✅ Platform جدید: {platform_code}")
    
    return platform
