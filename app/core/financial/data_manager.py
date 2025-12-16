"""
DataManager: مدیریت داده‌های سیستم جدید Label-Based
=======================================================

این کلاس رابط کامل برای کار با سیستم Label-Based فراهم می‌کند:
- مدیریت Accounts
- مدیریت AccountGold و AccountSilver
- مدیریت Sales
- Query و فیلتر
"""

from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Any
from datetime import datetime
from decimal import Decimal

from app.models.financial import (
    get_financial_session,
    Account,
    AccountGold,
    AccountSilver,
    Sale,
    SaleType,
    Customer
)
from app.core.logger import app_logger


class DataManager:
    """
    مدیریت کامل داده‌های سیستم مالی
    
    مثال:
        dm = DataManager()
        account = dm.create_account("g450", "test@example.com")
        gold = dm.add_gold_purchase("g450", 100, 3.00)
        sale = dm.add_sale("g450", "gold", 10, 4.50, "PX")
    """
    
    def __init__(self, session: Optional[Session] = None):
        """
        Args:
            session: SQLAlchemy session (اگر None باشد خودش می‌سازد)
        """
        self.session = session or get_financial_session()
        self._auto_close = session is None
        self.logger = app_logger
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._auto_close:
            self.session.close()
    
    # ═══════════════════════════════════════════════════════════════
    # ACCOUNTS
    # ═══════════════════════════════════════════════════════════════
    
    def create_account(
        self,
        label: str,
        email: Optional[str] = None,
        supplier: Optional[str] = None,
        status: str = "Consumed",
        source_sheet: Optional[str] = None
    ) -> Account:
        """ایجاد آکانت جدید"""
        account = Account(
            label=label,
            email=email,
            supplier=supplier,
            status=status,
            source_sheet=source_sheet
        )
        self.session.add(account)
        self.session.commit()
        self.logger.info(f"آکانت ایجاد شد: {label}")
        return account
    
    def get_account(self, label: str) -> Optional[Account]:
        """دریافت آکانت با label"""
        return self.session.query(Account).filter_by(label=label).first()
    
    def get_accounts_by_email(self, email: str) -> List[Account]:
        """دریافت تمام آکانت‌های یک ایمیل"""
        return self.session.query(Account).filter_by(email=email).all()
    
    # ═══════════════════════════════════════════════════════════════
    # GOLD PURCHASES
    # ═══════════════════════════════════════════════════════════════
    
    def add_gold_purchase(
        self,
        label: str,
        quantity: Decimal,
        rate: Decimal,
        purchase_date: Optional[datetime] = None
    ) -> AccountGold:
        """اضافه کردن خرید گلد"""
        cost = quantity * rate
        gold = AccountGold(
            label=label,
            gold_quantity=quantity,
            purchase_rate=rate,
            purchase_cost=cost,
            purchase_date=purchase_date or datetime.now()
        )
        self.session.add(gold)
        self.session.commit()
        self.logger.info(f"خرید گلد: {label} - {quantity} @ {rate}")
        return gold
    
    # ═══════════════════════════════════════════════════════════════
    # SILVER BONUSES
    # ═══════════════════════════════════════════════════════════════
    
    def add_silver_bonus(
        self,
        label: str,
        quantity: Decimal,
        bonus_date: Optional[datetime] = None
    ) -> AccountSilver:
        """اضافه کردن بونوس سیلور"""
        silver = AccountSilver(
            label=label,
            silver_quantity=quantity,
            bonus_date=bonus_date or datetime.now()
        )
        self.session.add(silver)
        self.session.commit()
        self.logger.info(f"بونوس سیلور: {label} - {quantity}")
        return silver
    
    # ═══════════════════════════════════════════════════════════════
    # SALES
    # ═══════════════════════════════════════════════════════════════
    
    def add_sale(
        self,
        label: str,
        sale_type: str,
        quantity: Decimal,
        rate: Decimal,
        customer: str,
        sale_date: Optional[datetime] = None,
        source_sheet: Optional[str] = None
    ) -> Sale:
        """اضافه کردن فروش"""
        amount = quantity * rate
        sale = Sale(
            label=label,
            sale_type=sale_type,
            quantity=quantity,
            sale_rate=rate,
            sale_amount=amount,
            customer=customer,
            sale_date=sale_date or datetime.now(),
            source_sheet=source_sheet
        )
        self.session.add(sale)
        self.session.commit()
        self.logger.info(f"فروش: {label} - {sale_type} - {quantity} @ {rate}")
        return sale
    
    def get_sales_by_label(self, label: str) -> List[Sale]:
        """دریافت تمام فروش‌های یک label"""
        return self.session.query(Sale).filter_by(label=label).all()
    
    # ═══════════════════════════════════════════════════════════════
    # CUSTOMERS
    # ═══════════════════════════════════════════════════════════════
    
    def get_or_create_customer(self, code: str, name: Optional[str] = None) -> Customer:
        """دریافت یا ایجاد مشتری"""
        customer = self.session.query(Customer).filter_by(code=code).first()
        if not customer:
            customer = Customer(code=code, name=name)
            self.session.add(customer)
            self.session.commit()
            self.logger.info(f"مشتری ایجاد شد: {code}")
        return customer
    
    def close(self):
        """بستن session"""
        if self._auto_close:
            self.session.close()
