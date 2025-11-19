"""
Financial Core Models - مدل‌های اصلی سیستم مالی
این ماژول شامل جداول اصلی معاملات، انبار، مشتریان و ... است
"""
from sqlalchemy import (
    Column, Integer, String, Text, TIMESTAMP, DECIMAL, 
    Boolean, Date, ForeignKey, Index, JSON, BigInteger
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from decimal import Decimal
from .base_financial import FinancialBase


# ═══════════════════════════════════════════════════════════
#                   1. ACCOUNT INVENTORY (انبار آکانت‌ها)
# ═══════════════════════════════════════════════════════════

class AccountInventory(FinancialBase):
    """
    انبار آکانت‌ها - هر آکانت خریداری شده یک کالا است
    """
    __tablename__ = 'accounts_inventory'
    
    # شناسه‌ها
    account_id = Column(Integer, primary_key=True, autoincrement=True)
    account_code = Column(String(50), unique=True, nullable=False, index=True, comment='کد کالا (سیستمی)')
    account_label = Column(String(100), nullable=False, index=True, comment='لیبل (از شیت)')
    
    # مشخصات آکانت
    email = Column(String(255), index=True, comment='ایمیل آکانت')
    password = Column(String(255), comment='پسورد')
    
    # دسته‌بندی
    department_id = Column(Integer, ForeignKey('departments.department_id'))
    platform_id = Column(Integer, ForeignKey('platforms.platform_id'))
    region_id = Column(Integer, ForeignKey('regions.region_id'))
    unit_type_id = Column(Integer, ForeignKey('unit_types.unit_id'), nullable=False)
    
    # خرید اولیه
    initial_balance = Column(DECIMAL(20, 4), nullable=False, comment='موجودی اولیه')
    purchase_rate = Column(DECIMAL(20, 4), nullable=False, comment='ریت خرید')
    purchase_cost = Column(DECIMAL(20, 4), nullable=False, comment='بهای تمام شده (تتر)')
    purchase_date = Column(Date, nullable=False, index=True)
    supplier = Column(String(255), comment='سورس/تامین‌کننده')
    
    # موجودی فعلی
    current_balance_gold = Column(DECIMAL(20, 4), default=0, comment='موجودی فعلی گلد')
    current_balance_silver = Column(DECIMAL(20, 4), default=0, comment='موجودی فعلی سیلور')
    
    # وضعیت
    status = Column(String(20), default='active', index=True, comment='active, depleted, suspended')
    is_recharged = Column(Boolean, default=False, comment='آیا ریشارژ شده؟')
    parent_account_id = Column(Integer, ForeignKey('accounts_inventory.account_id'), comment='اگر ریشارژ شده')
    
    # لینک به Phase 1
    source_sheet_id = Column(Integer, index=True, comment='sales_data.id از Phase 1')
    source_data = Column(JSON, comment='داده خام از شیت')
    
    # یادداشت
    notes = Column(Text)
    
    # تاریخ‌ها
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # روابط
    department = relationship("Department", back_populates="accounts")
    platform = relationship("Platform", back_populates="accounts")
    region = relationship("Region", back_populates="accounts")
    unit_type = relationship("UnitType", back_populates="accounts")
    parent_account = relationship("AccountInventory", remote_side=[account_id], backref="recharge_history")
    
    purchases = relationship("Purchase", back_populates="account")
    sales = relationship("Sale", back_populates="account")
    silver_bonuses = relationship("SilverBonus", back_populates="account")
    profit_loss = relationship("AccountProfitLoss", back_populates="account", uselist=False)
    
    __table_args__ = (
        Index('idx_account_label', 'account_label'),
        Index('idx_account_email', 'email'),
        Index('idx_account_status', 'status'),
        Index('idx_account_date', 'purchase_date'),
        Index('idx_account_dept', 'department_id'),
    )
    
    def __repr__(self):
        return f"<AccountInventory({self.account_code}: {self.account_label})>"


# ═══════════════════════════════════════════════════════════
#                   2. PURCHASES (خریدها)
# ═══════════════════════════════════════════════════════════

class Purchase(FinancialBase):
    """
    خریدها - ثبت هر بار خرید/ریشارژ آکانت
    """
    __tablename__ = 'purchases'
    
    purchase_id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('accounts_inventory.account_id'), nullable=False, index=True)
    purchase_date = Column(Date, nullable=False, index=True)
    supplier = Column(String(255), comment='سورس/تامین‌کننده')
    
    # مبالغ
    amount = Column(DECIMAL(20, 4), nullable=False, comment='مقدار شارژ')
    unit_type_id = Column(Integer, ForeignKey('unit_types.unit_id'), nullable=False)
    rate = Column(DECIMAL(20, 4), nullable=False, comment='ریت خرید')
    cost = Column(DECIMAL(20, 4), nullable=False, comment='هزینه (تتر)')
    
    # لینک به Phase 1
    source_sheet_id = Column(Integer, index=True)
    source_data = Column(JSON)
    
    notes = Column(Text)
    
    # تاریخ‌ها
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # روابط
    account = relationship("AccountInventory", back_populates="purchases")
    unit_type = relationship("UnitType")
    
    __table_args__ = (
        Index('idx_purchase_date', 'purchase_date'),
        Index('idx_purchase_account', 'account_id'),
    )
    
    def __repr__(self):
        return f"<Purchase({self.purchase_id}: {self.amount} @ {self.rate})>"


# ═══════════════════════════════════════════════════════════
#                   3. CUSTOMERS (مشتریان)
# ═══════════════════════════════════════════════════════════

class Customer(FinancialBase):
    """
    مشتریان - دارای حساب تفصیلی
    """
    __tablename__ = 'customers'
    
    customer_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_code = Column(String(50), unique=True, nullable=False, index=True, comment='کد مشتری (یکتا)')
    customer_name = Column(String(255), nullable=False, index=True, comment='نام مشتری')
    phone = Column(String(50), comment='تلفن')
    email = Column(String(255), comment='ایمیل')
    
    # مالی
    balance = Column(DECIMAL(20, 4), default=0, comment='مانده حساب (+ بدهکار، - بستانکار)')
    total_purchases = Column(DECIMAL(20, 4), default=0, comment='جمع خریدها')
    total_payments = Column(DECIMAL(20, 4), default=0, comment='جمع پرداخت‌ها')
    
    # وضعیت
    is_active = Column(Boolean, default=True, index=True)
    notes = Column(Text)
    
    # تاریخ‌ها
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # روابط
    sales = relationship("Sale", back_populates="customer")
    ledger = relationship("CustomerLedger", back_populates="customer", order_by="CustomerLedger.transaction_date")
    payments = relationship("CustomerPayment", back_populates="customer")
    
    __table_args__ = (
        Index('idx_customer_name', 'customer_name'),
        Index('idx_customer_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<Customer({self.customer_code}: {self.customer_name})>"


# ═══════════════════════════════════════════════════════════
#                   4. SALES (فروش‌ها)
# ═══════════════════════════════════════════════════════════

class Sale(FinancialBase):
    """
    فروش‌ها - ثبت هر معامله فروش
    """
    __tablename__ = 'sales'
    
    sale_id = Column(Integer, primary_key=True, autoincrement=True)
    sale_date = Column(Date, nullable=False, index=True)
    
    # آکانت و مشتری
    account_id = Column(Integer, ForeignKey('accounts_inventory.account_id'), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey('customers.customer_id'), nullable=False, index=True)
    
    # محصول
    product_name = Column(String(255), nullable=False, comment='نام محصول فروخته شده')
    platform_id = Column(Integer, ForeignKey('platforms.platform_id'))
    product_type = Column(String(20), nullable=False, index=True, comment='gold یا silver')
    
    # مقادیر
    amount_consumed = Column(DECIMAL(20, 4), nullable=False, comment='میزان کسر شده از آکانت')
    unit_type_id = Column(Integer, ForeignKey('unit_types.unit_id'), nullable=False)
    
    # قیمت
    sale_rate = Column(DECIMAL(20, 4), nullable=False, comment='ریت فروش')
    sale_price = Column(DECIMAL(20, 4), nullable=False, comment='قیمت (تتر)')
    sale_price_irt = Column(DECIMAL(20, 2), comment='قیمت (تومان) - اختیاری')
    
    # پرداخت
    payment_status = Column(String(20), default='pending', index=True, comment='paid, pending, debt')
    payment_method = Column(String(50), comment='usdt, irt, cash')
    
    # سود (محاسبه خودکار)
    profit_amount = Column(DECIMAL(20, 4), comment='سود این فروش')
    
    # لینک به Phase 1
    source_sheet_id = Column(Integer, index=True)
    source_data = Column(JSON)
    
    notes = Column(Text)
    
    # تاریخ‌ها
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # روابط
    account = relationship("AccountInventory", back_populates="sales")
    customer = relationship("Customer", back_populates="sales")
    platform = relationship("Platform", back_populates="sales")
    unit_type = relationship("UnitType")
    
    __table_args__ = (
        Index('idx_sale_date', 'sale_date'),
        Index('idx_sale_account', 'account_id'),
        Index('idx_sale_customer', 'customer_id'),
        Index('idx_sale_type', 'product_type'),
        Index('idx_sale_status', 'payment_status'),
    )
    
    def __repr__(self):
        return f"<Sale({self.sale_id}: {self.product_name} @ {self.sale_price})>"


# ═══════════════════════════════════════════════════════════
#                   5. SILVER BONUSES (بونوس سیلور)
# ═══════════════════════════════════════════════════════════

class SilverBonus(FinancialBase):
    """
    بونوس سیلور - ثبت دریافت بونوس
    """
    __tablename__ = 'silver_bonuses'
    
    bonus_id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('accounts_inventory.account_id'), nullable=False, index=True)
    platform_id = Column(Integer, ForeignKey('platforms.platform_id'), comment='کجا بونوس گرفت')
    
    gold_consumed = Column(DECIMAL(20, 4), nullable=False, comment='چقدر گلد خرج کرد')
    silver_received = Column(DECIMAL(20, 4), nullable=False, comment='چقدر سیلور گرفت')
    received_date = Column(Date, nullable=False, index=True)
    
    # لینک به Phase 1
    source_sheet_id = Column(Integer, index=True)
    source_data = Column(JSON)
    
    notes = Column(Text)
    
    # تاریخ‌ها
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # روابط
    account = relationship("AccountInventory", back_populates="silver_bonuses")
    platform = relationship("Platform", back_populates="silver_bonuses")
    
    __table_args__ = (
        Index('idx_bonus_date', 'received_date'),
        Index('idx_bonus_account', 'account_id'),
    )
    
    def __repr__(self):
        return f"<SilverBonus({self.bonus_id}: {self.silver_received} silver)>"


# ═══════════════════════════════════════════════════════════
#                   6. CUSTOMER LEDGER (دفتر حساب مشتریان)
# ═══════════════════════════════════════════════════════════

class CustomerLedger(FinancialBase):
    """
    دفتر حساب مشتریان - ثبت تمام تراکنش‌ها
    """
    __tablename__ = 'customer_ledger'
    
    ledger_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('customers.customer_id'), nullable=False, index=True)
    transaction_date = Column(Date, nullable=False, index=True)
    transaction_type = Column(String(50), nullable=False, comment='sale, payment, refund, adjustment')
    reference_id = Column(Integer, comment='sale_id یا payment_id')
    
    # مبالغ
    debit = Column(DECIMAL(20, 4), default=0, comment='بدهکار (فروش)')
    credit = Column(DECIMAL(20, 4), default=0, comment='بستانکار (پرداخت)')
    balance = Column(DECIMAL(20, 4), nullable=False, comment='مانده پس از این تراکنش')
    
    description = Column(String(500), comment='شرح تراکنش')
    notes = Column(Text)
    
    # تاریخ‌ها
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # روابط
    customer = relationship("Customer", back_populates="ledger")
    
    __table_args__ = (
        Index('idx_ledger_customer', 'customer_id'),
        Index('idx_ledger_date', 'transaction_date'),
        Index('idx_ledger_type', 'transaction_type'),
    )
    
    def __repr__(self):
        return f"<CustomerLedger({self.ledger_id}: {self.description})>"


# ═══════════════════════════════════════════════════════════
#                   7. CUSTOMER PAYMENTS (پرداخت‌های مشتریان)
# ═══════════════════════════════════════════════════════════

class CustomerPayment(FinancialBase):
    """
    پرداخت‌های مشتریان
    """
    __tablename__ = 'customer_payments'
    
    payment_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('customers.customer_id'), nullable=False, index=True)
    payment_date = Column(Date, nullable=False, index=True)
    amount = Column(DECIMAL(20, 4), nullable=False, comment='مبلغ پرداختی')
    payment_method = Column(String(50), comment='usdt, irt, cash, bank_transfer')
    reference_number = Column(String(255), comment='شماره پیگیری/تراکنش')
    
    # لینک به Phase 1
    source_sheet_id = Column(Integer, index=True)
    source_data = Column(JSON)
    
    notes = Column(Text)
    
    # تاریخ‌ها
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # روابط
    customer = relationship("Customer", back_populates="payments")
    
    __table_args__ = (
        Index('idx_payment_customer', 'customer_id'),
        Index('idx_payment_date', 'payment_date'),
    )
    
    def __repr__(self):
        return f"<CustomerPayment({self.payment_id}: {self.amount})>"


# ═══════════════════════════════════════════════════════════
#                   8. ACCOUNT PROFIT/LOSS (سود/زیان هر آکانت)
# ═══════════════════════════════════════════════════════════

class AccountProfitLoss(FinancialBase):
    """
    سود/زیان هر آکانت - محاسبه خودکار
    """
    __tablename__ = 'account_profit_loss'
    
    account_id = Column(Integer, ForeignKey('accounts_inventory.account_id'), primary_key=True)
    
    # هزینه
    purchase_cost = Column(DECIMAL(20, 4), default=0, comment='بهای تمام شده')
    
    # فروش
    total_gold_sales = Column(DECIMAL(20, 4), default=0, comment='جمع فروش گلد')
    total_silver_sales = Column(DECIMAL(20, 4), default=0, comment='جمع فروش سیلور')
    
    # سود
    profit_from_gold = Column(DECIMAL(20, 4), default=0, comment='سود فروش گلد')
    profit_from_silver = Column(DECIMAL(20, 4), default=0, comment='سود فروش سیلور (100%))')
    total_profit = Column(DECIMAL(20, 4), default=0, comment='سود کل')
    
    # موجودی باقیمانده
    remaining_gold = Column(DECIMAL(20, 4), default=0)
    remaining_silver = Column(DECIMAL(20, 4), default=0)
    remaining_value = Column(DECIMAL(20, 4), default=0, comment='ارزش فعلی باقیمانده')
    
    # وضعیت
    status = Column(String(20), default='active', comment='active, closed, written_off')
    
    # تاریخ‌ها
    calculated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # روابط
    account = relationship("AccountInventory", back_populates="profit_loss")
    
    def __repr__(self):
        return f"<AccountProfitLoss({self.account_id}: Profit={self.total_profit})>"
