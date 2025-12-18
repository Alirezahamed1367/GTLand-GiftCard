"""
سیستم جامع گزارش‌دهی مالی
این ماژول تمام گزارشات مورد نیاز یک سیستم خرید و فروش را فراهم می‌کند
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, extract
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
import pandas as pd

from app.models.financial import (
    Account, AccountGold, AccountSilver, Sale, 
    Platform, SheetImport
)
from app.core.financial import CalculationEngine


class ComprehensiveReportBuilder:
    """
    سازنده گزارشات جامع
    
    گزارشات موجود:
    1. گزارش خلاصه کل (Dashboard Summary)
    2. گزارش روزانه (Daily Report)
    3. گزارش ماهانه (Monthly Report)
    4. گزارش همه آکانت‌ها (All Accounts Report)
    5. گزارش موجودی (Inventory Report)
    6. گزارش سود/زیان (P&L Report)
    7. گزارش تامین‌کنندگان (Suppliers Report)
    8. گزارش پلتفرم‌ها (Platforms Report)
    9. گزارش مشتریان (Customers Report)
    10. گزارش مقایسه‌ای (Comparative Report)
    """
    
    def __init__(self, session: Session):
        self.session = session
        self.calc_engine = CalculationEngine(session)
    
    # ═══════════════════════════════════════════════════════════════
    # 1. گزارش خلاصه کل (Dashboard)
    # ═══════════════════════════════════════════════════════════════
    
    def generate_dashboard_summary(self) -> Dict:
        """
        گزارش خلاصه کل سیستم
        
        Returns:
            {
                'total_accounts': int,
                'total_investments': Decimal,
                'total_sales_revenue': Decimal,
                'total_profit': Decimal,
                'profit_margin': float,
                'gold_inventory': Decimal,
                'silver_inventory': Decimal,
                'active_platforms': int,
                'total_customers': int,
                'today_sales': Decimal,
                'this_month_sales': Decimal,
                'top_accounts': List[Dict],
                'recent_transactions': List[Dict]
            }
        """
        # تعداد کل آکانت‌ها
        total_accounts = self.session.query(Account).count()
        
        # کل سرمایه‌گذاری (خرید Gold)
        total_investments = self.session.query(
            func.sum(AccountGold.purchase_cost)
        ).scalar() or Decimal(0)
        
        # کل درآمد فروش
        total_sales_revenue = self.session.query(
            func.sum(Sale.sale_amount)
        ).scalar() or Decimal(0)
        
        # محاسبه سود کل
        all_accounts = self.session.query(Account).all()
        total_profit = Decimal(0)
        total_gold_inventory = Decimal(0)
        total_silver_inventory = Decimal(0)
        
        for account in all_accounts:
            summary = self.calc_engine.calculate_label_summary(account.label)
            if summary:
                total_profit += Decimal(str(summary['total']['profit']))
                total_gold_inventory += Decimal(str(summary['gold']['remaining']))
                total_silver_inventory += Decimal(str(summary['silver']['remaining']))
        
        # Profit Margin
        profit_margin = float(total_profit / total_investments * 100) if total_investments > 0 else 0
        
        # تعداد پلتفرم‌های فعال
        active_platforms = self.session.query(Platform).filter_by(is_active=True).count()
        
        # تعداد مشتریان منحصر به فرد
        total_customers = self.session.query(
            func.count(func.distinct(Sale.customer))
        ).filter(Sale.customer.isnot(None)).scalar() or 0
        
        # فروش امروز
        today = datetime.now().date()
        today_sales = self.session.query(
            func.sum(Sale.sale_amount)
        ).filter(
            func.date(Sale.sale_date) == today
        ).scalar() or Decimal(0)
        
        # فروش این ماه
        this_month = datetime.now().replace(day=1)
        this_month_sales = self.session.query(
            func.sum(Sale.sale_amount)
        ).filter(
            Sale.sale_date >= this_month
        ).scalar() or Decimal(0)
        
        # برترین آکانت‌ها (بیشترین سود)
        top_accounts = []
        for account in all_accounts[:10]:  # 10 تای اول
            summary = self.calc_engine.calculate_label_summary(account.label)
            if summary:
                top_accounts.append({
                    'label': account.label,
                    'profit': float(summary['total']['profit']),
                    'revenue': float(summary['total']['revenue']),
                    'gold_remaining': float(summary['gold']['remaining']),
                    'silver_remaining': float(summary['silver']['remaining'])
                })
        
        # مرتب‌سازی بر اساس سود
        top_accounts.sort(key=lambda x: x['profit'], reverse=True)
        top_accounts = top_accounts[:5]  # 5 تای برتر
        
        # آخرین تراکنش‌ها
        recent_sales = self.session.query(Sale).order_by(
            Sale.sale_date.desc()
        ).limit(10).all()
        
        recent_transactions = [
            {
                'label': sale.label,
                'type': sale.sale_type,
                'quantity': float(sale.quantity),
                'amount': float(sale.sale_amount),
                'platform': sale.platform,
                'date': sale.sale_date.strftime('%Y-%m-%d %H:%M') if sale.sale_date else None
            }
            for sale in recent_sales
        ]
        
        return {
            'total_accounts': total_accounts,
            'total_investments': float(total_investments),
            'total_sales_revenue': float(total_sales_revenue),
            'total_profit': float(total_profit),
            'profit_margin': round(profit_margin, 2),
            'gold_inventory': float(total_gold_inventory),
            'silver_inventory': float(total_silver_inventory),
            'active_platforms': active_platforms,
            'total_customers': total_customers,
            'today_sales': float(today_sales),
            'this_month_sales': float(this_month_sales),
            'top_accounts': top_accounts,
            'recent_transactions': recent_transactions
        }
    
    # ═══════════════════════════════════════════════════════════════
    # 2. گزارش روزانه
    # ═══════════════════════════════════════════════════════════════
    
    def generate_daily_report(self, date: datetime = None) -> Dict:
        """
        گزارش روزانه
        
        Args:
            date: تاریخ (پیش‌فرض امروز)
        
        Returns:
            {
                'date': str,
                'total_sales_count': int,
                'total_sales_revenue': Decimal,
                'gold_sold': Decimal,
                'silver_sold': Decimal,
                'by_platform': List[Dict],
                'by_account': List[Dict],
                'hourly_breakdown': List[Dict]
            }
        """
        if date is None:
            date = datetime.now()
        
        # اگر date از نوع datetime.date است، مستقیم استفاده کن
        if isinstance(date, datetime):
            target_date = date.date()
        else:
            target_date = date
        
        # فروش‌های این روز
        daily_sales = self.session.query(Sale).filter(
            func.date(Sale.sale_date) == target_date
        ).all()
        
        # آمار کلی
        total_sales_count = len(daily_sales)
        total_sales_revenue = sum(sale.sale_amount for sale in daily_sales)
        
        gold_sold = sum(
            sale.quantity for sale in daily_sales if sale.sale_type == 'gold'
        )
        
        silver_sold = sum(
            sale.quantity for sale in daily_sales if sale.sale_type == 'silver'
        )
        
        # به تفکیک پلتفرم
        by_platform = {}
        for sale in daily_sales:
            platform = sale.platform or 'Unknown'
            if platform not in by_platform:
                by_platform[platform] = {
                    'sales_count': 0,
                    'revenue': Decimal(0),
                    'gold_qty': Decimal(0),
                    'silver_qty': Decimal(0)
                }
            
            by_platform[platform]['sales_count'] += 1
            by_platform[platform]['revenue'] += sale.sale_amount
            
            if sale.sale_type == 'gold':
                by_platform[platform]['gold_qty'] += sale.quantity
            else:
                by_platform[platform]['silver_qty'] += sale.quantity
        
        # به تفکیک آکانت
        by_account = {}
        for sale in daily_sales:
            label = sale.label
            if label not in by_account:
                by_account[label] = {
                    'sales_count': 0,
                    'revenue': Decimal(0),
                    'profit': Decimal(0)
                }
            
            by_account[label]['sales_count'] += 1
            by_account[label]['revenue'] += sale.sale_amount
        
        # محاسبه سود برای هر آکانت
        for label in by_account.keys():
            summary = self.calc_engine.calculate_label_summary(label)
            if summary:
                by_account[label]['profit'] = Decimal(str(summary['total']['profit']))
        
        # تفکیک ساعتی
        hourly_breakdown = {}
        for sale in daily_sales:
            if sale.sale_date:
                hour = sale.sale_date.hour
                if hour not in hourly_breakdown:
                    hourly_breakdown[hour] = {
                        'sales_count': 0,
                        'revenue': Decimal(0)
                    }
                
                hourly_breakdown[hour]['sales_count'] += 1
                hourly_breakdown[hour]['revenue'] += sale.sale_amount
        
        return {
            'date': target_date.strftime('%Y-%m-%d'),
            'total_sales_count': total_sales_count,
            'total_sales_revenue': float(total_sales_revenue),
            'gold_sold': float(gold_sold),
            'silver_sold': float(silver_sold),
            'by_platform': [
                {
                    'platform': k,
                    'sales_count': v['sales_count'],
                    'revenue': float(v['revenue']),
                    'gold_qty': float(v['gold_qty']),
                    'silver_qty': float(v['silver_qty'])
                }
                for k, v in by_platform.items()
            ],
            'by_account': [
                {
                    'label': k,
                    'sales_count': v['sales_count'],
                    'revenue': float(v['revenue']),
                    'profit': float(v['profit'])
                }
                for k, v in by_account.items()
            ],
            'hourly_breakdown': [
                {
                    'hour': k,
                    'sales_count': v['sales_count'],
                    'revenue': float(v['revenue'])
                }
                for k, v in sorted(hourly_breakdown.items())
            ]
        }
    
    # ═══════════════════════════════════════════════════════════════
    # 3. گزارش ماهانه
    # ═══════════════════════════════════════════════════════════════
    
    def generate_monthly_report(self, year: int = None, month: int = None) -> Dict:
        """
        گزارش ماهانه
        
        Args:
            year: سال (پیش‌فرض سال جاری)
            month: ماه (پیش‌فرض ماه جاری)
        
        Returns:
            گزارش جامع ماهانه
        """
        now = datetime.now()
        year = year or now.year
        month = month or now.month
        
        # محدوده تاریخ
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        # فروش‌های این ماه
        monthly_sales = self.session.query(Sale).filter(
            and_(
                Sale.sale_date >= start_date,
                Sale.sale_date < end_date
            )
        ).all()
        
        # خریدهای این ماه
        monthly_purchases = self.session.query(AccountGold).filter(
            and_(
                AccountGold.purchase_date >= start_date,
                AccountGold.purchase_date < end_date
            )
        ).all()
        
        # آمار کلی
        total_sales_revenue = sum(sale.sale_amount for sale in monthly_sales)
        total_purchases_cost = sum(p.purchase_cost for p in monthly_purchases)
        
        # تفکیک روزانه
        daily_stats = {}
        for sale in monthly_sales:
            if sale.sale_date:
                day = sale.sale_date.day
                if day not in daily_stats:
                    daily_stats[day] = {
                        'sales_count': 0,
                        'revenue': Decimal(0),
                        'gold_qty': Decimal(0),
                        'silver_qty': Decimal(0)
                    }
                
                daily_stats[day]['sales_count'] += 1
                daily_stats[day]['revenue'] += sale.sale_amount
                
                if sale.sale_type == 'gold':
                    daily_stats[day]['gold_qty'] += sale.quantity
                else:
                    daily_stats[day]['silver_qty'] += sale.quantity
        
        return {
            'year': year,
            'month': month,
            'month_name': start_date.strftime('%B'),
            'total_sales_count': len(monthly_sales),
            'total_sales_revenue': float(total_sales_revenue),
            'total_purchases_count': len(monthly_purchases),
            'total_purchases_cost': float(total_purchases_cost),
            'net_profit': float(total_sales_revenue - total_purchases_cost),
            'daily_stats': [
                {
                    'day': k,
                    'sales_count': v['sales_count'],
                    'revenue': float(v['revenue']),
                    'gold_qty': float(v['gold_qty']),
                    'silver_qty': float(v['silver_qty'])
                }
                for k, v in sorted(daily_stats.items())
            ]
        }
    
    # ═══════════════════════════════════════════════════════════════
    # 4. گزارش همه آکانت‌ها
    # ═══════════════════════════════════════════════════════════════
    
    def generate_all_accounts_report(self, sort_by: str = 'profit') -> pd.DataFrame:
        """
        گزارش همه آکانت‌ها
        
        Args:
            sort_by: مرتب‌سازی بر اساس ('profit', 'revenue', 'cost', 'label')
        
        Returns:
            DataFrame با اطلاعات کامل همه آکانت‌ها
        """
        all_accounts = self.session.query(Account).all()
        
        data = []
        for account in all_accounts:
            summary = self.calc_engine.calculate_label_summary(account.label)
            if summary:
                data.append({
                    'Label': account.label,
                    'Email': account.email or '',
                    'Supplier': account.supplier or '',
                    'Status': account.status or '',
                    'Gold_Purchased': float(summary['gold']['purchased']),
                    'Gold_Sold': float(summary['gold']['sold']),
                    'Gold_Remaining': float(summary['gold']['remaining']),
                    'Silver_Bonus': float(summary['silver']['bonus']),
                    'Silver_Sold': float(summary['silver']['sold']),
                    'Silver_Remaining': float(summary['silver']['remaining']),
                    'Total_Cost': float(summary['total']['cost']),
                    'Total_Revenue': float(summary['total']['revenue']),
                    'Total_Profit': float(summary['total']['profit']),
                    'Profit_Margin_%': round(summary['gold'].get('profit_pct', 0), 2),
                    'Created_At': account.created_at.strftime('%Y-%m-%d') if account.created_at else ''
                })
        
        df = pd.DataFrame(data)
        
        # مرتب‌سازی
        sort_map = {
            'profit': 'Total_Profit',
            'revenue': 'Total_Revenue',
            'cost': 'Total_Cost',
            'label': 'Label'
        }
        
        if sort_by in sort_map:
            df = df.sort_values(by=sort_map[sort_by], ascending=False)
        
        return df
    
    # ═══════════════════════════════════════════════════════════════
    # 5. گزارش موجودی
    # ═══════════════════════════════════════════════════════════════
    
    def generate_inventory_report(self, low_stock_threshold: float = 100) -> Dict:
        """
        گزارش موجودی فعلی
        
        Args:
            low_stock_threshold: حد موجودی کم
        
        Returns:
            گزارش کامل موجودی
        """
        all_accounts = self.session.query(Account).all()
        
        total_gold = Decimal(0)
        total_silver = Decimal(0)
        low_gold_accounts = []
        low_silver_accounts = []
        out_of_stock_gold = []
        out_of_stock_silver = []
        
        inventory_details = []
        
        for account in all_accounts:
            summary = self.calc_engine.calculate_label_summary(account.label)
            if summary:
                gold_rem = Decimal(str(summary['gold']['remaining']))
                silver_rem = Decimal(str(summary['silver']['remaining']))
                
                total_gold += gold_rem
                total_silver += silver_rem
                
                inventory_details.append({
                    'label': account.label,
                    'gold_remaining': float(gold_rem),
                    'silver_remaining': float(silver_rem),
                    'gold_value': float(gold_rem * Decimal(str(summary['gold'].get('purchase_rate', 0)))),
                    'status': 'OK' if gold_rem > low_stock_threshold else 'Low Stock' if gold_rem > 0 else 'Out of Stock'
                })
                
                # موجودی کم
                if 0 < gold_rem <= low_stock_threshold:
                    low_gold_accounts.append(account.label)
                
                if 0 < silver_rem <= low_stock_threshold:
                    low_silver_accounts.append(account.label)
                
                # تمام شده
                if gold_rem <= 0:
                    out_of_stock_gold.append(account.label)
                
                if silver_rem <= 0:
                    out_of_stock_silver.append(account.label)
        
        return {
            'total_gold_inventory': float(total_gold),
            'total_silver_inventory': float(total_silver),
            'total_accounts': len(all_accounts),
            'low_gold_accounts_count': len(low_gold_accounts),
            'low_silver_accounts_count': len(low_silver_accounts),
            'out_of_stock_gold_count': len(out_of_stock_gold),
            'out_of_stock_silver_count': len(out_of_stock_silver),
            'low_gold_accounts': low_gold_accounts,
            'low_silver_accounts': low_silver_accounts,
            'out_of_stock_gold': out_of_stock_gold,
            'out_of_stock_silver': out_of_stock_silver,
            'inventory_details': inventory_details
        }
    
    # ═══════════════════════════════════════════════════════════════
    # 6. گزارش تامین‌کنندگان
    # ═══════════════════════════════════════════════════════════════
    
    def generate_suppliers_report(self) -> pd.DataFrame:
        """
        گزارش به تفکیک تامین‌کننده
        
        Returns:
            DataFrame با آمار هر تامین‌کننده
        """
        suppliers_stats = {}
        
        all_accounts = self.session.query(Account).all()
        
        for account in all_accounts:
            supplier = account.supplier or 'Unknown'
            
            if supplier not in suppliers_stats:
                suppliers_stats[supplier] = {
                    'accounts_count': 0,
                    'total_gold_purchased': Decimal(0),
                    'total_cost': Decimal(0),
                    'total_revenue': Decimal(0),
                    'total_profit': Decimal(0)
                }
            
            suppliers_stats[supplier]['accounts_count'] += 1
            
            summary = self.calc_engine.calculate_label_summary(account.label)
            if summary:
                suppliers_stats[supplier]['total_gold_purchased'] += Decimal(str(summary['gold']['purchased']))
                suppliers_stats[supplier]['total_cost'] += Decimal(str(summary['total']['cost']))
                suppliers_stats[supplier]['total_revenue'] += Decimal(str(summary['total']['revenue']))
                suppliers_stats[supplier]['total_profit'] += Decimal(str(summary['total']['profit']))
        
        data = [
            {
                'Supplier': k,
                'Accounts_Count': v['accounts_count'],
                'Total_Gold_Purchased': float(v['total_gold_purchased']),
                'Total_Cost': float(v['total_cost']),
                'Total_Revenue': float(v['total_revenue']),
                'Total_Profit': float(v['total_profit']),
                'Profit_Margin_%': round(float(v['total_profit'] / v['total_cost'] * 100), 2) if v['total_cost'] > 0 else 0
            }
            for k, v in suppliers_stats.items()
        ]
        
        df = pd.DataFrame(data)
        df = df.sort_values(by='Total_Profit', ascending=False)
        
        return df
    
    # ═══════════════════════════════════════════════════════════════
    # 7. گزارش پلتفرم‌ها
    # ═══════════════════════════════════════════════════════════════
    
    def generate_platforms_report(self) -> pd.DataFrame:
        """
        گزارش به تفکیک پلتفرم
        
        Returns:
            DataFrame با آمار هر پلتفرم
        """
        platforms_stats = {}
        
        all_sales = self.session.query(Sale).all()
        
        for sale in all_sales:
            platform = sale.platform or 'Unknown'
            
            if platform not in platforms_stats:
                platforms_stats[platform] = {
                    'sales_count': 0,
                    'gold_sold': Decimal(0),
                    'silver_sold': Decimal(0),
                    'total_revenue': Decimal(0),
                    'unique_accounts': set()
                }
            
            platforms_stats[platform]['sales_count'] += 1
            platforms_stats[platform]['total_revenue'] += sale.sale_amount
            platforms_stats[platform]['unique_accounts'].add(sale.label)
            
            if sale.sale_type == 'gold':
                platforms_stats[platform]['gold_sold'] += sale.quantity
            else:
                platforms_stats[platform]['silver_sold'] += sale.quantity
        
        data = [
            {
                'Platform': k,
                'Sales_Count': v['sales_count'],
                'Gold_Sold': float(v['gold_sold']),
                'Silver_Sold': float(v['silver_sold']),
                'Total_Revenue': float(v['total_revenue']),
                'Unique_Accounts': len(v['unique_accounts']),
                'Avg_Sale_Amount': round(float(v['total_revenue'] / v['sales_count']), 2) if v['sales_count'] > 0 else 0
            }
            for k, v in platforms_stats.items()
        ]
        
        df = pd.DataFrame(data)
        df = df.sort_values(by='Total_Revenue', ascending=False)
        
        return df
    
    # ═══════════════════════════════════════════════════════════════
    # 8. گزارش مشتریان
    # ═══════════════════════════════════════════════════════════════
    
    def generate_customers_report(self, top_n: int = 50) -> pd.DataFrame:
        """
        گزارش مشتریان برتر
        
        Args:
            top_n: تعداد مشتریان برتر
        
        Returns:
            DataFrame با آمار مشتریان
        """
        customers_stats = {}
        
        all_sales = self.session.query(Sale).filter(
            Sale.customer.isnot(None)
        ).all()
        
        for sale in all_sales:
            customer = sale.customer
            
            if customer not in customers_stats:
                customers_stats[customer] = {
                    'purchases_count': 0,
                    'total_spent': Decimal(0),
                    'gold_bought': Decimal(0),
                    'silver_bought': Decimal(0),
                    'last_purchase_date': None
                }
            
            customers_stats[customer]['purchases_count'] += 1
            customers_stats[customer]['total_spent'] += sale.sale_amount
            
            if sale.sale_type == 'gold':
                customers_stats[customer]['gold_bought'] += sale.quantity
            else:
                customers_stats[customer]['silver_bought'] += sale.quantity
            
            if sale.sale_date:
                if customers_stats[customer]['last_purchase_date'] is None or \
                   sale.sale_date > customers_stats[customer]['last_purchase_date']:
                    customers_stats[customer]['last_purchase_date'] = sale.sale_date
        
        data = [
            {
                'Customer': k,
                'Purchases_Count': v['purchases_count'],
                'Total_Spent': float(v['total_spent']),
                'Gold_Bought': float(v['gold_bought']),
                'Silver_Bought': float(v['silver_bought']),
                'Avg_Purchase': round(float(v['total_spent'] / v['purchases_count']), 2) if v['purchases_count'] > 0 else 0,
                'Last_Purchase': v['last_purchase_date'].strftime('%Y-%m-%d') if v['last_purchase_date'] else ''
            }
            for k, v in customers_stats.items()
        ]
        
        df = pd.DataFrame(data)
        df = df.sort_values(by='Total_Spent', ascending=False).head(top_n)
        
        return df
    
    # ═══════════════════════════════════════════════════════════════
    # 9. گزارش مقایسه‌ای
    # ═══════════════════════════════════════════════════════════════
    
    def generate_comparative_report(self, period: str = 'monthly') -> Dict:
        """
        گزارش مقایسه‌ای (این ماه با ماه قبل، امروز با دیروز، ...)
        
        Args:
            period: 'daily' یا 'monthly'
        
        Returns:
            گزارش مقایسه‌ای
        """
        now = datetime.now()
        
        if period == 'daily':
            # امروز
            current_report = self.generate_daily_report(now)
            
            # دیروز
            yesterday = now - timedelta(days=1)
            previous_report = self.generate_daily_report(yesterday)
            
            current_label = 'امروز'
            previous_label = 'دیروز'
            
        else:  # monthly
            # این ماه
            current_report = self.generate_monthly_report(now.year, now.month)
            
            # ماه قبل
            if now.month == 1:
                prev_year = now.year - 1
                prev_month = 12
            else:
                prev_year = now.year
                prev_month = now.month - 1
            
            previous_report = self.generate_monthly_report(prev_year, prev_month)
            
            current_label = 'این ماه'
            previous_label = 'ماه قبل'
        
        # محاسبه تغییرات
        current_revenue = current_report.get('total_sales_revenue', 0)
        previous_revenue = previous_report.get('total_sales_revenue', 0)
        
        revenue_change = current_revenue - previous_revenue
        revenue_change_pct = (revenue_change / previous_revenue * 100) if previous_revenue > 0 else 0
        
        current_sales = current_report.get('total_sales_count', 0)
        previous_sales = previous_report.get('total_sales_count', 0)
        
        sales_change = current_sales - previous_sales
        sales_change_pct = (sales_change / previous_sales * 100) if previous_sales > 0 else 0
        
        return {
            'period': period,
            'current': {
                'label': current_label,
                'revenue': current_revenue,
                'sales_count': current_sales
            },
            'previous': {
                'label': previous_label,
                'revenue': previous_revenue,
                'sales_count': previous_sales
            },
            'changes': {
                'revenue_change': revenue_change,
                'revenue_change_pct': round(revenue_change_pct, 2),
                'sales_change': sales_change,
                'sales_change_pct': round(sales_change_pct, 2),
                'trend': 'up' if revenue_change > 0 else 'down' if revenue_change < 0 else 'stable'
            }
        }
    
    # ═══════════════════════════════════════════════════════════════
    # Export به Excel
    # ═══════════════════════════════════════════════════════════════
    
    def export_all_reports_to_excel(self, filepath: str):
        """
        Export تمام گزارشات به یک فایل Excel
        
        Args:
            filepath: مسیر فایل خروجی
        """
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # 1. همه آکانت‌ها
            self.generate_all_accounts_report().to_excel(
                writer, sheet_name='All Accounts', index=False
            )
            
            # 2. تامین‌کنندگان
            self.generate_suppliers_report().to_excel(
                writer, sheet_name='Suppliers', index=False
            )
            
            # 3. پلتفرم‌ها
            self.generate_platforms_report().to_excel(
                writer, sheet_name='Platforms', index=False
            )
            
            # 4. مشتریان
            self.generate_customers_report().to_excel(
                writer, sheet_name='Top Customers', index=False
            )
            
            # 5. Dashboard (به صورت دیکشنری)
            dashboard = self.generate_dashboard_summary()
            dashboard_df = pd.DataFrame([
                {'Metric': k, 'Value': str(v)}
                for k, v in dashboard.items()
                if not isinstance(v, (list, dict))
            ])
            dashboard_df.to_excel(writer, sheet_name='Dashboard', index=False)
        
        print(f"✅ گزارشات با موفقیت در {filepath} ذخیره شد!")
