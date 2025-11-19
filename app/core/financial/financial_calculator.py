"""
ماشین حساب مالی - Financial Calculator
محاسبات سود/زیان و آمار
"""
from typing import Dict, List
from decimal import Decimal
from datetime import datetime, date

from app.models.financial import (
    FinancialSessionLocal,
    AccountInventory as Account, 
    Sale as Transaction, 
    SilverBonus as SilverTransaction
)
from app.core.logger import app_logger


class FinancialCalculator:
    """
    کلاس محاسبات مالی
    """
    
    def __init__(self):
        """راه‌اندازی Calculator"""
        self.logger = app_logger
    
    def calculate_account_profit(self, account_id: int) -> Dict:
        """
        محاسبه سود/زیان یک آکانت
        
        Returns:
            Dict با اطلاعات سود/زیان
        """
        db = FinancialSessionLocal()
        
        try:
            account = db.query(Account).filter_by(id=account_id).first()
            if not account:
                return {}
            
            # محاسبه سود Gold
            gold_sales = db.query(Transaction).filter_by(
                account_id=account_id,
                status='completed'
            ).all()
            
            total_gold_sales = sum(t.sale_price_usdt for t in gold_sales)
            gold_profit = total_gold_sales - account.purchase_price_usdt
            
            # محاسبه سود Silver
            silver_sales = db.query(SilverTransaction).filter_by(
                account_id=account_id,
                status='completed'
            ).all()
            
            total_silver_sales = sum(st.sale_price_usdt for st in silver_sales)
            
            # سود کل
            total_profit = gold_profit + total_silver_sales
            
            result = {
                'account_label': account.label,
                'purchase_price': float(account.purchase_price_usdt),
                'gold_sales': float(total_gold_sales),
                'gold_profit': float(gold_profit),
                'silver_sales': float(total_silver_sales),
                'silver_profit': float(total_silver_sales),  # Silver تماماً سود است
                'total_profit': float(total_profit),
                'profit_margin': float((total_profit / account.purchase_price_usdt * 100)) if account.purchase_price_usdt > 0 else 0,
                'gold_transactions_count': len(gold_sales),
                'silver_transactions_count': len(silver_sales)
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"خطا در محاسبه سود آکانت {account_id}: {str(e)}")
            return {}
        finally:
            db.close()
    
    def calculate_department_profit(
        self,
        department_id: int,
        date_from: date = None,
        date_to: date = None
    ) -> Dict:
        """محاسبه سود/زیان یک دپارتمان"""
        db = FinancialSessionLocal()
        
        try:
            # دریافت تمام آکانت‌های دپارتمان
            accounts = db.query(Account).filter_by(department_id=department_id).all()
            
            total_purchase = Decimal('0')
            total_gold_sales = Decimal('0')
            total_silver_sales = Decimal('0')
            
            for account in accounts:
                total_purchase += account.purchase_price_usdt
                
                # فیلتر تاریخی
                query = db.query(Transaction).filter_by(
                    account_id=account.id,
                    status='completed'
                )
                if date_from:
                    query = query.filter(Transaction.transaction_date >= date_from)
                if date_to:
                    query = query.filter(Transaction.transaction_date <= date_to)
                
                transactions = query.all()
                total_gold_sales += sum(t.sale_price_usdt for t in transactions)
                
                # Silver
                silver_query = db.query(SilverTransaction).filter_by(
                    account_id=account.id,
                    status='completed'
                )
                if date_from:
                    silver_query = silver_query.filter(SilverTransaction.transaction_date >= date_from)
                if date_to:
                    silver_query = silver_query.filter(SilverTransaction.transaction_date <= date_to)
                
                silver_trans = silver_query.all()
                total_silver_sales += sum(st.sale_price_usdt for st in silver_trans)
            
            total_profit = (total_gold_sales - total_purchase) + total_silver_sales
            
            return {
                'department_id': department_id,
                'accounts_count': len(accounts),
                'total_purchase': float(total_purchase),
                'gold_sales': float(total_gold_sales),
                'silver_sales': float(total_silver_sales),
                'total_sales': float(total_gold_sales + total_silver_sales),
                'total_profit': float(total_profit),
                'profit_margin': float((total_profit / total_purchase * 100)) if total_purchase > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"خطا در محاسبه سود دپارتمان {department_id}: {str(e)}")
            return {}
        finally:
            db.close()


# نمونه سینگلتون
financial_calculator = FinancialCalculator()
