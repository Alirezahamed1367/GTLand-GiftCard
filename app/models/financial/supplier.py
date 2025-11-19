"""
مدل تأمین‌کننده - Supplier Model
"""
from sqlalchemy import Column, Integer, String, Boolean, Text, TIMESTAMP, DECIMAL, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from decimal import Decimal
from .base_financial import FinancialBase


class Supplier(FinancialBase):
    """
    جدول تأمین‌کنندگان (سورس‌ها)
    """
    __tablename__ = 'suppliers'
    
    id = Column(Integer, primary_key=True, index=True)
    
    # شناسایی
    supplier_code = Column(String(100), unique=True, nullable=False, index=True, comment='کد سورس (S-0001)')
    name = Column(String(255), nullable=False, index=True, comment='نام سورس')
    
    # حساب جاری
    account_balance_usdt = Column(DECIMAL(15, 4), default=Decimal('0'), comment='مانده حساب (تتر)')
    account_balance_irr = Column(DECIMAL(20, 2), default=Decimal('0'), comment='مانده حساب (تومان)')
    
    # اطلاعات تماس
    contact_person = Column(String(255), nullable=True, comment='شخص تماس')
    phone = Column(String(50), nullable=True, comment='تلفن')
    telegram = Column(String(100), nullable=True, comment='تلگرام')
    email = Column(String(255), nullable=True, comment='ایمیل')
    
    # آمار
    total_purchases_count = Column(Integer, default=0, comment='تعداد خریدها')
    total_purchases_usdt = Column(DECIMAL(15, 4), default=Decimal('0'), comment='مجموع خرید (تتر)')
    total_payments_usdt = Column(DECIMAL(15, 4), default=Decimal('0'), comment='مجموع پرداخت (تتر)')
    
    # وضعیت
    is_active = Column(Boolean, default=True, comment='فعال/غیرفعال')
    reliability_score = Column(Integer, default=3, comment='امتیاز اعتماد (1-5)')
    
    # تاریخ‌ها
    created_at = Column(TIMESTAMP, server_default=func.now(), comment='تاریخ ایجاد')
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    last_purchase_at = Column(TIMESTAMP, nullable=True, comment='آخرین خرید')
    
    notes = Column(Text, nullable=True, comment='یادداشت‌ها')
    
    # روابط
    accounts = relationship("Account", back_populates="supplier")
    payments = relationship("Payment", back_populates="supplier")
    
    __table_args__ = (
        Index('idx_supplier_code', 'supplier_code'),
        Index('idx_supplier_name', 'name'),
    )
    
    def __repr__(self):
        return f"<Supplier(id={self.id}, code='{self.supplier_code}', name='{self.name}')>"
