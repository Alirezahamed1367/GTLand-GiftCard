"""
مدل مشتری - Customer Model
"""
from sqlalchemy import Column, Integer, String, Boolean, Text, TIMESTAMP, DECIMAL, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from decimal import Decimal
from .base_financial import FinancialBase


class Customer(FinancialBase):
    """
    جدول مشتریان
    """
    __tablename__ = 'customers'
    
    # ستون‌های اصلی
    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(
        Integer, 
        ForeignKey('departments.id', ondelete='CASCADE'),
        nullable=False,
        comment='شناسه دپارتمان'
    )
    
    # شناسایی
    customer_code = Column(String(100), unique=True, nullable=False, index=True, comment='کد مشتری (C1-0001)')
    name = Column(String(255), nullable=False, index=True, comment='نام مشتری')
    
    # دسته‌بندی
    customer_type = Column(
        String(50), 
        default='regular',
        comment='نوع مشتری (wholesale, retail, vip, regular)'
    )
    
    # حساب جاری
    account_balance_usdt = Column(DECIMAL(15, 4), default=Decimal('0'), comment='مانده حساب (تتر)')
    account_balance_irr = Column(DECIMAL(20, 2), default=Decimal('0'), comment='مانده حساب (تومان)')
    
    # اطلاعات تماس
    phone = Column(String(50), nullable=True, comment='تلفن')
    telegram = Column(String(100), nullable=True, comment='تلگرام')
    email = Column(String(255), nullable=True, comment='ایمیل')
    
    # آمار
    total_purchases_count = Column(Integer, default=0, comment='تعداد خریدها')
    total_purchases_usdt = Column(DECIMAL(15, 4), default=Decimal('0'), comment='مجموع خرید (تتر)')
    total_purchases_irr = Column(DECIMAL(20, 2), default=Decimal('0'), comment='مجموع خرید (تومان)')
    total_payments_usdt = Column(DECIMAL(15, 4), default=Decimal('0'), comment='مجموع پرداخت (تتر)')
    total_payments_irr = Column(DECIMAL(20, 2), default=Decimal('0'), comment='مجموع پرداخت (تومان)')
    
    # وضعیت
    is_active = Column(Boolean, default=True, comment='فعال/غیرفعال')
    credit_limit = Column(DECIMAL(15, 4), default=Decimal('0'), comment='سقف اعتبار')
    
    # تاریخ‌ها
    created_at = Column(TIMESTAMP, server_default=func.now(), comment='تاریخ ایجاد')
    updated_at = Column(
        TIMESTAMP, 
        server_default=func.now(), 
        onupdate=func.now(), 
        comment='تاریخ بروزرسانی'
    )
    last_purchase_at = Column(TIMESTAMP, nullable=True, comment='آخرین خرید')
    
    # توضیحات
    notes = Column(Text, nullable=True, comment='یادداشت‌ها')
    
    # روابط
    department = relationship("Department", back_populates="customers")
    transactions = relationship("Transaction", back_populates="customer")
    silver_transactions = relationship("SilverTransaction", back_populates="customer")
    payments = relationship("Payment", back_populates="customer")
    
    # ایندکس‌ها
    __table_args__ = (
        Index('idx_customer_code', 'customer_code'),
        Index('idx_customer_name', 'name'),
        Index('idx_customer_department', 'department_id'),
        Index('idx_customer_type', 'customer_type'),
    )
    
    def __repr__(self):
        return f"<Customer(id={self.id}, code='{self.customer_code}', name='{self.name}')>"
    
    def update_balance(self, amount_usdt=0, amount_irr=0, operation='add'):
        """بروزرسانی مانده حساب"""
        if operation == 'add':
            self.account_balance_usdt += Decimal(str(amount_usdt))
            self.account_balance_irr += Decimal(str(amount_irr))
        elif operation == 'subtract':
            self.account_balance_usdt -= Decimal(str(amount_usdt))
            self.account_balance_irr -= Decimal(str(amount_irr))
    
    def to_dict(self):
        """تبدیل به دیکشنری"""
        return {
            'id': self.id,
            'department_id': self.department_id,
            'customer_code': self.customer_code,
            'name': self.name,
            'customer_type': self.customer_type,
            'account_balance_usdt': float(self.account_balance_usdt),
            'account_balance_irr': float(self.account_balance_irr),
            'phone': self.phone,
            'telegram': self.telegram,
            'email': self.email,
            'total_purchases_count': self.total_purchases_count,
            'total_purchases_usdt': float(self.total_purchases_usdt),
            'total_purchases_irr': float(self.total_purchases_irr),
            'total_payments_usdt': float(self.total_payments_usdt),
            'total_payments_irr': float(self.total_payments_irr),
            'is_active': self.is_active,
            'credit_limit': float(self.credit_limit),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_purchase_at': self.last_purchase_at.isoformat() if self.last_purchase_at else None,
            'notes': self.notes,
        }
