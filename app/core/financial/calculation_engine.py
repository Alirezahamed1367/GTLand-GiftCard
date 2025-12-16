"""
Calculation Engine - موتور محاسبات قدرتمند
==========================================
محاسبه سود/زیان گلد و سیلور به صورت جداگانه
"""
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.financial.simple_models import (
    Account, AccountGold, AccountSilver, Sale, 
    AccountSummary, Customer, SaleType
)


class CalculationEngine:
    """
    موتور محاسبات
    
    ویژگی‌ها:
    - محاسبه سود گلد و سیلور به صورت جداگانه
    - جمع‌بندی به تفکیک Label
    - جمع‌بندی به تفکیک Email
    - محاسبه آمار مشتریان
    - سوزاندن مانده‌ها
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    # ═══════════════════════════════════════════════════════════════
    # محاسبات Label
    # ═══════════════════════════════════════════════════════════════
    
    def calculate_label_summary(self, label: str) -> Dict:
        """
        محاسبه خلاصه کامل برای یک Label
        
        Returns:
            {
                'label': 'g450',
                'email': 'test@example.com',
                'gold': {...},
                'silver': {...},
                'total': {...},
                'stats': {...}
            }
        """
        # دریافت آکانت
        account = self.db.query(Account).filter(Account.label == label).first()
        if not account:
            return None
        
        # دریافت خرید گلد
        gold_purchase = self.db.query(AccountGold).filter(
            AccountGold.label == label
        ).first()
        
        # دریافت بونوس سیلور
        silver_bonus = self.db.query(AccountSilver).filter(
            AccountSilver.label == label
        ).first()
        
        # دریافت فروش‌های گلد
        gold_sales = self.db.query(Sale).filter(
            and_(
                Sale.label == label,
                Sale.sale_type == SaleType.GOLD.value
            )
        ).all()
        
        # دریافت فروش‌های سیلور
        silver_sales = self.db.query(Sale).filter(
            and_(
                Sale.label == label,
                Sale.sale_type == SaleType.SILVER.value
            )
        ).all()
        
        # ═══ محاسبات گلد ═══
        if gold_purchase:
            total_gold_purchased = float(gold_purchase.gold_quantity)
            total_gold_sold = sum(float(s.quantity) for s in gold_sales)
            remaining_gold = total_gold_purchased - total_gold_sold
            
            purchase_rate = float(gold_purchase.purchase_rate)
            gold_purchase_cost = float(gold_purchase.purchase_cost)
            
            # درآمد گلد
            gold_revenue = sum(float(s.sale_amount) for s in gold_sales)
            
            # هزینه گلدهای فروخته شده
            gold_cost_of_sold = total_gold_sold * purchase_rate
            
            # سود گلد
            gold_profit = gold_revenue - gold_cost_of_sold
            
            # درصد سود
            gold_profit_pct = (gold_profit / gold_cost_of_sold * 100) if gold_cost_of_sold > 0 else 0
        else:
            total_gold_purchased = 0
            total_gold_sold = 0
            remaining_gold = 0
            gold_purchase_cost = 0
            gold_revenue = 0
            gold_profit = 0
            gold_profit_pct = 0
        
        # ═══ محاسبات سیلور ═══
        if silver_bonus:
            total_silver_bonus = float(silver_bonus.silver_quantity)
            total_silver_sold = sum(float(s.quantity) for s in silver_sales)
            remaining_silver = total_silver_bonus - total_silver_sold
            
            # درآمد سیلور
            silver_revenue = sum(float(s.sale_amount) for s in silver_sales)
            
            # سود سیلور (100% چون رایگان است)
            silver_profit = silver_revenue
        else:
            total_silver_bonus = 0
            total_silver_sold = 0
            remaining_silver = 0
            silver_revenue = 0
            silver_profit = 0
        
        # ═══ جمع کل ═══
        total_revenue = gold_revenue + silver_revenue
        total_profit = gold_profit + silver_profit
        total_cost = gold_purchase_cost
        
        # ═══ آمار ═══
        all_sales = gold_sales + silver_sales
        sale_count = len(all_sales)
        
        unique_customers = len(set(s.customer for s in all_sales if s.customer))
        
        last_sale_date = max(
            (s.sale_date for s in all_sales if s.sale_date),
            default=None
        )
        
        return {
            'label': label,
            'email': account.email,
            'supplier': account.supplier,
            'status': account.status,
            'gold': {
                'purchased': total_gold_purchased,
                'sold': total_gold_sold,
                'remaining': remaining_gold,
                'purchase_rate': purchase_rate if gold_purchase else 0,
                'cost': gold_purchase_cost,
                'revenue': gold_revenue,
                'profit': gold_profit,
                'profit_pct': gold_profit_pct
            },
            'silver': {
                'bonus': total_silver_bonus,
                'sold': total_silver_sold,
                'remaining': remaining_silver,
                'revenue': silver_revenue,
                'profit': silver_profit
            },
            'total': {
                'revenue': total_revenue,
                'profit': total_profit,
                'cost': total_cost
            },
            'stats': {
                'sale_count': sale_count,
                'unique_customers': unique_customers,
                'last_sale_date': last_sale_date
            }
        }
    
    def update_account_summary(self, label: str) -> AccountSummary:
        """
        بروزرسانی جدول خلاصه برای یک Label
        """
        summary_data = self.calculate_label_summary(label)
        if not summary_data:
            return None
        
        # پیدا یا ایجاد
        summary = self.db.query(AccountSummary).filter(
            AccountSummary.label == label
        ).first()
        
        if not summary:
            summary = AccountSummary(label=label)
            self.db.add(summary)
        
        # بروزرسانی
        summary.email = summary_data['email']
        
        # گلد
        summary.total_gold_purchased = Decimal(str(summary_data['gold']['purchased']))
        summary.total_gold_sold = Decimal(str(summary_data['gold']['sold']))
        summary.remaining_gold = Decimal(str(summary_data['gold']['remaining']))
        summary.gold_purchase_cost = Decimal(str(summary_data['gold']['cost']))
        summary.gold_revenue = Decimal(str(summary_data['gold']['revenue']))
        summary.gold_profit = Decimal(str(summary_data['gold']['profit']))
        summary.gold_profit_percentage = Decimal(str(summary_data['gold']['profit_pct']))
        
        # سیلور
        summary.total_silver_bonus = Decimal(str(summary_data['silver']['bonus']))
        summary.total_silver_sold = Decimal(str(summary_data['silver']['sold']))
        summary.remaining_silver = Decimal(str(summary_data['silver']['remaining']))
        summary.silver_revenue = Decimal(str(summary_data['silver']['revenue']))
        summary.silver_profit = Decimal(str(summary_data['silver']['profit']))
        
        # جمع
        summary.total_revenue = Decimal(str(summary_data['total']['revenue']))
        summary.total_profit = Decimal(str(summary_data['total']['profit']))
        summary.total_cost = Decimal(str(summary_data['total']['cost']))
        
        # آمار
        summary.sale_count = summary_data['stats']['sale_count']
        summary.unique_customers = summary_data['stats']['unique_customers']
        summary.last_sale_date = summary_data['stats']['last_sale_date']
        
        summary.last_updated = datetime.now()
        
        self.db.commit()
        return summary
    
    # ═══════════════════════════════════════════════════════════════
    # محاسبات Email (جمع همه Labels)
    # ═══════════════════════════════════════════════════════════════
    
    def calculate_email_summary(self, email: str) -> Dict:
        """
        جمع همه Label‌های یک Email
        
        Returns:
            {
                'email': 'test@example.com',
                'labels': ['g450', 'g451', 'g452'],
                'gold': {...},
                'silver': {...},
                'total': {...}
            }
        """
        # پیدا کردن همه Labels این Email
        accounts = self.db.query(Account).filter(Account.email == email).all()
        
        if not accounts:
            return None
        
        labels = [acc.label for acc in accounts]
        
        # محاسبه برای هر Label
        summaries = [self.calculate_label_summary(label) for label in labels]
        summaries = [s for s in summaries if s]  # حذف None
        
        if not summaries:
            return None
        
        # جمع‌بندی
        return {
            'email': email,
            'labels': labels,
            'label_count': len(labels),
            'gold': {
                'total_purchased': sum(s['gold']['purchased'] for s in summaries),
                'total_sold': sum(s['gold']['sold'] for s in summaries),
                'total_remaining': sum(s['gold']['remaining'] for s in summaries),
                'total_cost': sum(s['gold']['cost'] for s in summaries),
                'total_revenue': sum(s['gold']['revenue'] for s in summaries),
                'total_profit': sum(s['gold']['profit'] for s in summaries)
            },
            'silver': {
                'total_bonus': sum(s['silver']['bonus'] for s in summaries),
                'total_sold': sum(s['silver']['sold'] for s in summaries),
                'total_remaining': sum(s['silver']['remaining'] for s in summaries),
                'total_revenue': sum(s['silver']['revenue'] for s in summaries),
                'total_profit': sum(s['silver']['profit'] for s in summaries)
            },
            'total': {
                'revenue': sum(s['total']['revenue'] for s in summaries),
                'profit': sum(s['total']['profit'] for s in summaries),
                'cost': sum(s['total']['cost'] for s in summaries)
            },
            'details': summaries  # جزئیات هر Label
        }
    
    # ═══════════════════════════════════════════════════════════════
    # محاسبات Customer
    # ═══════════════════════════════════════════════════════════════
    
    def calculate_customer_summary(self, customer_code: str) -> Dict:
        """
        خلاصه خریدهای یک مشتری
        """
        # تمام فروش‌ها به این مشتری
        sales = self.db.query(Sale).filter(Sale.customer == customer_code).all()
        
        if not sales:
            return None
        
        # جداسازی گلد و سیلور
        gold_sales = [s for s in sales if s.sale_type == SaleType.GOLD.value]
        silver_sales = [s for s in sales if s.sale_type == SaleType.SILVER.value]
        
        # Labels خریداری شده
        unique_labels = list(set(s.label for s in sales))
        
        return {
            'customer': customer_code,
            'total_purchases': len(sales),
            'total_spent': sum(float(s.sale_amount) for s in sales),
            'gold': {
                'quantity': sum(float(s.quantity) for s in gold_sales),
                'amount': sum(float(s.sale_amount) for s in gold_sales)
            },
            'silver': {
                'quantity': sum(float(s.quantity) for s in silver_sales),
                'amount': sum(float(s.sale_amount) for s in silver_sales)
            },
            'labels': unique_labels,
            'first_purchase': min(s.sale_date for s in sales if s.sale_date),
            'last_purchase': max(s.sale_date for s in sales if s.sale_date)
        }
    
    def update_customer(self, customer_code: str) -> Customer:
        """
        بروزرسانی آمار مشتری
        """
        summary = self.calculate_customer_summary(customer_code)
        if not summary:
            return None
        
        # پیدا یا ایجاد
        customer = self.db.query(Customer).filter(
            Customer.code == customer_code
        ).first()
        
        if not customer:
            customer = Customer(code=customer_code)
            self.db.add(customer)
        
        # بروزرسانی
        customer.total_purchases = summary['total_purchases']
        customer.total_spent = Decimal(str(summary['total_spent']))
        customer.total_gold_bought = Decimal(str(summary['gold']['quantity']))
        customer.total_silver_bought = Decimal(str(summary['silver']['quantity']))
        customer.first_purchase_at = summary['first_purchase']
        customer.last_purchase_at = summary['last_purchase']
        
        self.db.commit()
        return customer
    
    # ═══════════════════════════════════════════════════════════════
    # عملیات خاص
    # ═══════════════════════════════════════════════════════════════
    
    def burn_remaining_gold(self, label: str) -> Decimal:
        """
        سوزاندن مانده گلد و تبدیل به زیان
        
        Returns:
            مقدار زیان
        """
        summary = self.calculate_label_summary(label)
        if not summary:
            return Decimal('0')
        
        remaining_gold = summary['gold']['remaining']
        purchase_rate = summary['gold']['purchase_rate']
        
        if remaining_gold <= 0:
            return Decimal('0')
        
        # زیان = مانده × نرخ خرید
        loss = Decimal(str(remaining_gold)) * Decimal(str(purchase_rate))
        
        # ثبت در متادیتا
        account = self.db.query(Account).filter(Account.label == label).first()
        if account:
            if not account.metadata:
                account.metadata = {}
            account.metadata['burned_gold'] = {
                'quantity': remaining_gold,
                'loss': float(loss),
                'date': datetime.now().isoformat()
            }
            self.db.commit()
        
        return loss
    
    def get_all_labels_summary(self) -> List[Dict]:
        """
        خلاصه همه Label‌ها
        """
        accounts = self.db.query(Account).all()
        summaries = []
        
        for account in accounts:
            summary = self.calculate_label_summary(account.label)
            if summary:
                summaries.append(summary)
        
        return summaries
    
    def get_total_system_summary(self) -> Dict:
        """
        خلاصه کل سیستم
        """
        all_summaries = self.get_all_labels_summary()
        
        if not all_summaries:
            return {
                'total_accounts': 0,
                'gold': {},
                'silver': {},
                'total': {}
            }
        
        return {
            'total_accounts': len(all_summaries),
            'gold': {
                'total_purchased': sum(s['gold']['purchased'] for s in all_summaries),
                'total_sold': sum(s['gold']['sold'] for s in all_summaries),
                'total_remaining': sum(s['gold']['remaining'] for s in all_summaries),
                'total_cost': sum(s['gold']['cost'] for s in all_summaries),
                'total_revenue': sum(s['gold']['revenue'] for s in all_summaries),
                'total_profit': sum(s['gold']['profit'] for s in all_summaries)
            },
            'silver': {
                'total_bonus': sum(s['silver']['bonus'] for s in all_summaries),
                'total_sold': sum(s['silver']['sold'] for s in all_summaries),
                'total_remaining': sum(s['silver']['remaining'] for s in all_summaries),
                'total_revenue': sum(s['silver']['revenue'] for s in all_summaries),
                'total_profit': sum(s['silver']['profit'] for s in all_summaries)
            },
            'total': {
                'revenue': sum(s['total']['revenue'] for s in all_summaries),
                'profit': sum(s['total']['profit'] for s in all_summaries),
                'cost': sum(s['total']['cost'] for s in all_summaries)
            }
        }
