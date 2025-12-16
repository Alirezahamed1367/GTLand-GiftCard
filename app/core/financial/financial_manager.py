"""
مدیریت دیتابیس مالی - Financial Database Manager
"""
from typing import List, Optional, Dict, Tuple
from datetime import datetime
from decimal import Decimal

from app.models.financial import (
    FinancialSessionLocal,
    Account,
    AccountGold,
    AccountSilver,
    Sale,
    Customer
)
from app.core.logger import app_logger


class FinancialManager:
    """
    کلاس مدیریت عملیات دیتابیس مالی
    """
    
    def __init__(self):
        """راه‌اندازی مدیر دیتابیس مالی"""
        self.logger = app_logger
    
    def get_session(self):
        """دریافت session جدید"""
        return FinancialSessionLocal()
    
    # ==================== Department ====================
    
    def get_all_departments(self, active_only: bool = True) -> List[Department]:
        """دریافت تمام دپارتمان‌ها"""
        db = self.get_session()
        query = db.query(Department)
        if active_only:
            query = query.filter(Department.is_active == True)
        departments = query.all()
        db.close()
        return departments
    
    # ==================== Account ====================
    
    def get_all_accounts(
        self, 
        department_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[Account]:
        """دریافت تمام آکانت‌ها"""
        db = self.get_session()
        query = db.query(Account)
        
        if department_id:
            query = query.filter(Account.department_id == department_id)
        if status:
            query = query.filter(Account.status == status)
        
        accounts = query.all()
        db.close()
        return accounts
    
    def get_account_by_label(self, label: str) -> Optional[Account]:
        """دریافت آکانت بر اساس Label"""
        db = self.get_session()
        account = db.query(Account).filter_by(label=label).first()
        db.close()
        return account
    
    # ==================== Customer ====================
    
    def get_all_customers(
        self, 
        department_id: Optional[int] = None
    ) -> List[Customer]:
        """دریافت تمام مشتریان"""
        db = self.get_session()
        query = db.query(Customer)
        
        if department_id:
            query = query.filter(Customer.department_id == department_id)
        
        customers = query.all()
        db.close()
        return customers
    
    # ==================== Transaction ====================
    
    def get_transactions(
        self,
        account_id: Optional[int] = None,
        customer_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Transaction]:
        """دریافت معاملات با فیلتر"""
        db = self.get_session()
        query = db.query(Transaction)
        
        if account_id:
            query = query.filter(Transaction.account_id == account_id)
        if customer_id:
            query = query.filter(Transaction.customer_id == customer_id)
        if date_from:
            query = query.filter(Transaction.transaction_date >= date_from)
        if date_to:
            query = query.filter(Transaction.transaction_date <= date_to)
        
        transactions = query.order_by(Transaction.transaction_date.desc()).limit(limit).all()
        db.close()
        return transactions
    
    # ==================== Statistics ====================
    
    def get_account_statistics(self, account_id: int) -> Dict:
        """دریافت آمار یک آکانت"""
        db = self.get_session()
        
        account = db.query(Account).filter_by(id=account_id).first()
        if not account:
            db.close()
            return {}
        
        stats = {
            'label': account.label,
            'initial_balance': float(account.initial_balance),
            'current_balance': float(account.current_balance),
            'purchase_price': float(account.purchase_price_usdt),
            'total_sales': float(account.total_sales_amount_usdt),
            'total_profit': float(account.total_profit_usdt),
            'gold_profit': float(account.gold_profit_usdt),
            'silver_profit': float(account.silver_profit_usdt),
            'sales_count': account.total_sales_count,
            'status': account.status
        }
        
        db.close()
        return stats


# نمونه سینگلتون
financial_manager = FinancialManager()
