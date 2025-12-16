"""
سازنده گزارش پیشرفته - کاربر می‌تواند گزارش سفارشی بسازد
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from decimal import Decimal
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from app.models.financial import (
    Account, AccountGold, AccountSilver, Sale, Platform, Customer,
    CustomReport
)
import pandas as pd


class AdvancedReportBuilder:
    """
    سازنده گزارش پیشرفته
    
    کاربر می‌تواند:
    1. نوع گزارش را انتخاب کند (Label, Platform, Customer, Custom)
    2. فیلترها را تعیین کند (تاریخ، پلتفرم، مشتری، ...)
    3. ستون‌های نمایشی را انتخاب کند
    4. تجمیع‌ها را مشخص کند (sum, avg, count, ...)
    5. مرتب‌سازی را تعیین کند
    """
    
    def __init__(self, session: Session):
        self.session = session
    
    def build_report(self, report_config: Dict[str, Any]) -> pd.DataFrame:
        """
        ساخت گزارش بر اساس پیکربندی
        
        Args:
            report_config: {
                'report_type': 'label'|'platform'|'customer'|'custom',
                'filters': {
                    'label': 'A1054',
                    'platform': 'roblox',
                    'customer': 'C001',
                    'date_from': '2024-01-01',
                    'date_to': '2024-12-31',
                    'sale_type': 'gold'|'silver'
                },
                'columns': ['label', 'platform', 'quantity', 'revenue', 'profit'],
                'aggregations': {'revenue': 'sum', 'quantity': 'sum'},
                'group_by': ['label', 'platform'],
                'sort_by': 'revenue',
                'sort_order': 'desc'
            }
        
        Returns:
            DataFrame با گزارش
        """
        report_type = report_config.get('report_type', 'label')
        
        if report_type == 'label':
            return self._build_label_report(report_config)
        elif report_type == 'platform':
            return self._build_platform_report(report_config)
        elif report_type == 'customer':
            return self._build_customer_report(report_config)
        elif report_type == 'custom':
            return self._build_custom_report(report_config)
        else:
            raise ValueError(f"نوع گزارش '{report_type}' پشتیبانی نمی‌شود")
    
    def _build_label_report(self, config: Dict[str, Any]) -> pd.DataFrame:
        """گزارش بر اساس Label"""
        from app.core.financial.calculation_engine import CalculationEngine
        
        calc_engine = CalculationEngine(self.session)
        filters = config.get('filters', {})
        
        # فیلتر Labels
        query = self.session.query(Account)
        
        if 'label' in filters:
            query = query.filter(Account.label == filters['label'])
        
        if 'email' in filters:
            query = query.filter(Account.email == filters['email'])
        
        if 'supplier' in filters:
            query = query.filter(Account.supplier == filters['supplier'])
        
        accounts = query.all()
        
        # محاسبه برای هر Label
        data = []
        for account in accounts:
            summary = calc_engine.calculate_label_summary(account.label)
            
            row = {
                'Label': account.label,
                'Email': account.email,
                'Supplier': account.supplier,
                'Gold Purchased': float(summary['gold']['purchased']),
                'Gold Sold': float(summary['gold']['sold']),
                'Gold Remaining': float(summary['gold']['remaining']),
                'Silver Bonus': float(summary['silver']['bonus']),
                'Silver Sold': float(summary['silver']['sold']),
                'Silver Remaining': float(summary['silver']['remaining']),
                'Total Cost': float(summary['total']['cost']),
                'Total Revenue': float(summary['total']['revenue']),
                'Gold Profit': float(summary['gold']['profit']),
                'Silver Profit': float(summary['silver']['profit']),
                'Total Profit': float(summary['total']['profit']),
                'Status': account.status
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # مرتب‌سازی
        sort_by = config.get('sort_by', 'Total Profit')
        sort_order = config.get('sort_order', 'desc')
        if sort_by in df.columns:
            df = df.sort_values(by=sort_by, ascending=(sort_order == 'asc'))
        
        return df
    
    def _build_platform_report(self, config: Dict[str, Any]) -> pd.DataFrame:
        """گزارش بر اساس پلتفرم"""
        filters = config.get('filters', {})
        
        # Query پایه
        query = self.session.query(
            Sale.platform,
            Sale.sale_type,
            func.count(Sale.id).label('transaction_count'),
            func.sum(Sale.quantity).label('total_quantity'),
            func.sum(Sale.sale_amount).label('total_revenue')
        ).group_by(Sale.platform, Sale.sale_type)
        
        # فیلترها
        if 'platform' in filters:
            query = query.filter(Sale.platform == filters['platform'])
        
        if 'sale_type' in filters:
            query = query.filter(Sale.sale_type == filters['sale_type'])
        
        if 'date_from' in filters:
            query = query.filter(Sale.sale_date >= filters['date_from'])
        
        if 'date_to' in filters:
            query = query.filter(Sale.sale_date <= filters['date_to'])
        
        results = query.all()
        
        # تبدیل به DataFrame
        data = []
        for row in results:
            data.append({
                'Platform': row.platform or 'N/A',
                'Type': row.sale_type,
                'Transactions': row.transaction_count,
                'Total Quantity': float(row.total_quantity or 0),
                'Total Revenue': float(row.total_revenue or 0),
                'Avg per Transaction': float(row.total_revenue / row.transaction_count) if row.transaction_count else 0
            })
        
        df = pd.DataFrame(data)
        
        # مرتب‌سازی
        sort_by = config.get('sort_by', 'Total Revenue')
        sort_order = config.get('sort_order', 'desc')
        if sort_by in df.columns:
            df = df.sort_values(by=sort_by, ascending=(sort_order == 'asc'))
        
        return df
    
    def _build_customer_report(self, config: Dict[str, Any]) -> pd.DataFrame:
        """گزارش بر اساس مشتری"""
        filters = config.get('filters', {})
        
        # Query پایه
        query = self.session.query(
            Sale.customer,
            func.count(Sale.id).label('purchase_count'),
            func.sum(Sale.quantity).label('total_quantity'),
            func.sum(Sale.sale_amount).label('total_spent')
        ).filter(Sale.customer.isnot(None)).group_by(Sale.customer)
        
        # فیلترها
        if 'customer' in filters:
            query = query.filter(Sale.customer == filters['customer'])
        
        if 'platform' in filters:
            query = query.filter(Sale.platform == filters['platform'])
        
        if 'date_from' in filters:
            query = query.filter(Sale.sale_date >= filters['date_from'])
        
        if 'date_to' in filters:
            query = query.filter(Sale.sale_date <= filters['date_to'])
        
        results = query.all()
        
        # تبدیل به DataFrame
        data = []
        for row in results:
            data.append({
                'Customer': row.customer,
                'Purchase Count': row.purchase_count,
                'Total Quantity': float(row.total_quantity or 0),
                'Total Spent': float(row.total_spent or 0),
                'Avg per Purchase': float(row.total_spent / row.purchase_count) if row.purchase_count else 0
            })
        
        df = pd.DataFrame(data)
        
        # مرتب‌سازی
        sort_by = config.get('sort_by', 'Total Spent')
        sort_order = config.get('sort_order', 'desc')
        if sort_by in df.columns:
            df = df.sort_values(by=sort_by, ascending=(sort_order == 'asc'))
        
        return df
    
    def _build_custom_report(self, config: Dict[str, Any]) -> pd.DataFrame:
        """گزارش سفارشی کامل"""
        # این متد به کاربر اجازه می‌دهد Query کاملاً سفارشی بسازد
        
        # Query پایه: همه فروش‌ها
        query = self.session.query(Sale)
        
        filters = config.get('filters', {})
        
        # اعمال فیلترها
        if 'label' in filters:
            query = query.filter(Sale.label == filters['label'])
        
        if 'platform' in filters:
            query = query.filter(Sale.platform == filters['platform'])
        
        if 'customer' in filters:
            query = query.filter(Sale.customer == filters['customer'])
        
        if 'sale_type' in filters:
            query = query.filter(Sale.sale_type == filters['sale_type'])
        
        if 'date_from' in filters:
            query = query.filter(Sale.sale_date >= filters['date_from'])
        
        if 'date_to' in filters:
            query = query.filter(Sale.sale_date <= filters['date_to'])
        
        sales = query.all()
        
        # تبدیل به DataFrame
        data = []
        for sale in sales:
            row = {
                'Label': sale.label,
                'Platform': sale.platform,
                'Type': sale.sale_type,
                'Quantity': float(sale.quantity),
                'Rate': float(sale.sale_rate),
                'Revenue': float(sale.sale_amount),
                'Customer': sale.customer,
                'Date': sale.sale_date.strftime('%Y-%m-%d') if sale.sale_date else None,
                'Staff Profit': float(sale.staff_profit) if sale.staff_profit else None
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # انتخاب ستون‌ها
        columns = config.get('columns')
        if columns:
            available_cols = [col for col in columns if col in df.columns]
            df = df[available_cols]
        
        # Group By & Aggregations
        group_by = config.get('group_by')
        aggregations = config.get('aggregations')
        
        if group_by and aggregations:
            df = df.groupby(group_by).agg(aggregations).reset_index()
        
        # مرتب‌سازی
        sort_by = config.get('sort_by')
        sort_order = config.get('sort_order', 'desc')
        if sort_by and sort_by in df.columns:
            df = df.sort_values(by=sort_by, ascending=(sort_order == 'asc'))
        
        return df
    
    def save_report_config(self, report_name: str, config: Dict[str, Any]) -> int:
        """ذخیره پیکربندی گزارش برای استفاده بعدی"""
        custom_report = CustomReport(
            report_name=report_name,
            report_type=config.get('report_type', 'custom'),
            filters=config.get('filters'),
            columns=config.get('columns'),
            aggregations=config.get('aggregations'),
            sort_by=config.get('sort_by')
        )
        self.session.add(custom_report)
        self.session.commit()
        
        return custom_report.id
    
    def load_report_config(self, report_id: int) -> Optional[Dict[str, Any]]:
        """بارگذاری پیکربندی ذخیره شده"""
        report = self.session.query(CustomReport).get(report_id)
        
        if not report:
            return None
        
        return {
            'report_name': report.report_name,
            'report_type': report.report_type,
            'filters': report.filters,
            'columns': report.columns,
            'aggregations': report.aggregations,
            'sort_by': report.sort_by
        }
    
    def get_saved_reports(self) -> List[Dict[str, Any]]:
        """دریافت لیست گزارش‌های ذخیره شده"""
        reports = self.session.query(CustomReport).all()
        
        return [
            {
                'id': r.id,
                'name': r.report_name,
                'type': r.report_type,
                'is_favorite': r.is_favorite,
                'created_date': r.created_date.strftime('%Y-%m-%d') if r.created_date else None
            }
            for r in reports
        ]
    
    def export_to_excel(self, df: pd.DataFrame, filepath: str, sheet_name: str = 'Report'):
        """صادرات گزارش به Excel"""
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # فرمت‌دهی
            worksheet = writer.sheets[sheet_name]
            
            # عرض ستون‌ها
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(cell.value)
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width


class ReportTemplates:
    """
    قالب‌های آماده گزارش
    """
    
    @staticmethod
    def daily_sales_summary() -> Dict[str, Any]:
        """خلاصه فروش روزانه"""
        today = date.today()
        return {
            'report_type': 'custom',
            'filters': {
                'date_from': today.strftime('%Y-%m-%d'),
                'date_to': today.strftime('%Y-%m-%d')
            },
            'columns': ['Platform', 'Type', 'Quantity', 'Revenue'],
            'group_by': ['Platform', 'Type'],
            'aggregations': {'Quantity': 'sum', 'Revenue': 'sum'},
            'sort_by': 'Revenue',
            'sort_order': 'desc'
        }
    
    @staticmethod
    def top_customers(limit: int = 10) -> Dict[str, Any]:
        """مشتریان برتر"""
        return {
            'report_type': 'customer',
            'sort_by': 'Total Spent',
            'sort_order': 'desc',
            'limit': limit
        }
    
    @staticmethod
    def platform_comparison() -> Dict[str, Any]:
        """مقایسه پلتفرم‌ها"""
        return {
            'report_type': 'platform',
            'sort_by': 'Total Revenue',
            'sort_order': 'desc'
        }
    
    @staticmethod
    def low_stock_accounts(threshold: int = 10) -> Dict[str, Any]:
        """آکانت‌های کم موجودی"""
        return {
            'report_type': 'label',
            'filters': {
                'gold_remaining_less_than': threshold
            },
            'sort_by': 'Gold Remaining',
            'sort_order': 'asc'
        }
