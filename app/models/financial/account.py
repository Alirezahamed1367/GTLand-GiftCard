"""
مدل آکانت - Account Model
آکانت‌های خریداری شده که به عنوان موجودی انبار محسوب می‌شوند
"""
from sqlalchemy import Column, Integer, String, Boolean, Text, TIMESTAMP, DECIMAL, Date, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from decimal import Decimal
from .base_financial import FinancialBase


class Account(FinancialBase):
    """
    جدول آکانت‌های خریداری شده (موجودی انبار)
    """
    __tablename__ = 'accounts'
    
    # ستون‌های اصلی
    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(
        Integer, 
        ForeignKey('departments.id', ondelete='CASCADE'),
        nullable=False,
        comment='شناسه دپارتمان'
    )
    
    # شناسایی (کالا)
    label = Column(String(100), unique=True, nullable=False, index=True, comment='لیبل آکانت (G123, K450)')
    product_code = Column(String(100), unique=True, nullable=False, index=True, comment='کد کالا (P1-0001)')
    product_name = Column(String(255), nullable=False, comment='نام کالا (همان label)')
    
    # اطلاعات آکانت
    email = Column(String(255), nullable=True, comment='ایمیل آکانت')
    platform = Column(String(100), nullable=True, comment='پلتفرم (iTunes, Razer, PSN, ...)')
    region = Column(String(50), nullable=True, comment='ریجن (US, SE, TR, ...)')
    
    # موجودی اولیه (Gold)
    initial_balance = Column(DECIMAL(15, 2), nullable=False, comment='موجودی اولیه')
    balance_unit = Column(String(20), default='USD', comment='واحد موجودی (CP, USD, EUR, ...)')
    current_balance = Column(DECIMAL(15, 2), nullable=False, comment='موجودی فعلی')
    
    # خرید
    purchase_rate = Column(DECIMAL(10, 4), nullable=False, comment='ریت خرید')
    purchase_price_usdt = Column(DECIMAL(15, 4), nullable=False, comment='قیمت خرید (تتر)')
    purchase_price_irr = Column(DECIMAL(20, 2), nullable=True, comment='قیمت خرید (تومان)')
    purchase_date = Column(Date, nullable=False, index=True, comment='تاریخ خرید')
    supplier_id = Column(
        Integer, 
        ForeignKey('suppliers.id', ondelete='SET NULL'),
        nullable=True,
        comment='شناسه تأمین‌کننده'
    )
    
    # Silver/Bonus
    silver_earned = Column(DECIMAL(15, 2), default=Decimal('0'), comment='مقدار Silver دریافتی')
    silver_unit = Column(String(20), nullable=True, comment='واحد Silver')
    silver_remaining = Column(DECIMAL(15, 2), default=Decimal('0'), comment='Silver باقیمانده')
    
    # وضعیت
    status = Column(
        String(20), 
        default='active', 
        index=True,
        comment='وضعیت (active, depleted, archived, suspended)'
    )
    is_finished = Column(Boolean, default=False, comment='آیا تمام شده؟')
    finished_at = Column(TIMESTAMP, nullable=True, comment='تاریخ اتمام')
    finish_reason = Column(String(100), nullable=True, comment='دلیل اتمام (depleted, damaged, other)')
    
    # آمار فروش
    total_sales_count = Column(Integer, default=0, comment='تعداد فروش‌ها')
    total_sales_amount_usdt = Column(DECIMAL(15, 4), default=Decimal('0'), comment='مجموع فروش (تتر)')
    total_sales_amount_irr = Column(DECIMAL(20, 2), default=Decimal('0'), comment='مجموع فروش (تومان)')
    
    # محاسبات سود/زیان (محاسباتی)
    gold_profit_usdt = Column(DECIMAL(15, 4), default=Decimal('0'), comment='سود/زیان Gold (تتر)')
    silver_profit_usdt = Column(DECIMAL(15, 4), default=Decimal('0'), comment='سود Silver (تتر)')
    total_profit_usdt = Column(DECIMAL(15, 4), default=Decimal('0'), comment='سود کل (تتر)')
    
    # باقیمانده
    remnant_balance = Column(DECIMAL(15, 2), default=Decimal('0'), comment='باقیمانده غیرقابل استفاده')
    remnant_status = Column(
        String(20), 
        default='usable',
        comment='وضعیت باقیمانده (usable, waste, archived)'
    )
    remnant_note = Column(Text, nullable=True, comment='توضیحات باقیمانده')
    
    # تاریخ‌ها
    created_at = Column(TIMESTAMP, server_default=func.now(), comment='تاریخ ایجاد')
    updated_at = Column(
        TIMESTAMP, 
        server_default=func.now(), 
        onupdate=func.now(), 
        comment='تاریخ بروزرسانی'
    )
    
    # توضیحات
    notes = Column(Text, nullable=True, comment='یادداشت‌ها')
    
    # روابط
    department = relationship("Department", back_populates="accounts")
    supplier = relationship("Supplier", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account")
    silver_transactions = relationship("SilverTransaction", back_populates="account")
    
    # ایندکس‌ها
    __table_args__ = (
        Index('idx_account_label', 'label'),
        Index('idx_account_product_code', 'product_code'),
        Index('idx_account_status', 'status'),
        Index('idx_account_department', 'department_id'),
        Index('idx_account_purchase_date', 'purchase_date'),
    )
    
    def __repr__(self):
        return f"<Account(id={self.id}, label='{self.label}', status='{self.status}')>"
    
    def calculate_profits(self):
        """محاسبه سود/زیان"""
        # سود Gold = فروش - خرید
        self.gold_profit_usdt = self.total_sales_amount_usdt - self.purchase_price_usdt
        
        # سود Silver (همیشه مثبت است)
        # محاسبه در SilverTransaction انجام می‌شود
        
        # سود کل
        self.total_profit_usdt = self.gold_profit_usdt + self.silver_profit_usdt
    
    def update_current_balance(self, consumed_amount):
        """بروزرسانی موجودی فعلی"""
        self.current_balance -= Decimal(str(consumed_amount))
        if self.current_balance <= 0:
            self.current_balance = Decimal('0')
            self.is_finished = True
            self.status = 'depleted'
            self.finished_at = func.now()
    
    def to_dict(self):
        """تبدیل به دیکشنری"""
        return {
            'id': self.id,
            'department_id': self.department_id,
            'label': self.label,
            'product_code': self.product_code,
            'product_name': self.product_name,
            'email': self.email,
            'platform': self.platform,
            'region': self.region,
            'initial_balance': float(self.initial_balance),
            'balance_unit': self.balance_unit,
            'current_balance': float(self.current_balance),
            'purchase_rate': float(self.purchase_rate),
            'purchase_price_usdt': float(self.purchase_price_usdt),
            'purchase_price_irr': float(self.purchase_price_irr) if self.purchase_price_irr else None,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None,
            'supplier_id': self.supplier_id,
            'silver_earned': float(self.silver_earned),
            'silver_unit': self.silver_unit,
            'silver_remaining': float(self.silver_remaining),
            'status': self.status,
            'is_finished': self.is_finished,
            'finished_at': self.finished_at.isoformat() if self.finished_at else None,
            'finish_reason': self.finish_reason,
            'total_sales_count': self.total_sales_count,
            'total_sales_amount_usdt': float(self.total_sales_amount_usdt),
            'total_sales_amount_irr': float(self.total_sales_amount_irr),
            'gold_profit_usdt': float(self.gold_profit_usdt),
            'silver_profit_usdt': float(self.silver_profit_usdt),
            'total_profit_usdt': float(self.total_profit_usdt),
            'remnant_balance': float(self.remnant_balance),
            'remnant_status': self.remnant_status,
            'remnant_note': self.remnant_note,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'notes': self.notes,
        }
