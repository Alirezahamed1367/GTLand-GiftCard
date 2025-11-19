"""
مدل فروشنده - Seller Model
"""
from sqlalchemy import Column, Integer, String, Boolean, Text, TIMESTAMP, DECIMAL, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from decimal import Decimal
from .base_financial import FinancialBase


class Seller(FinancialBase):
    """
    جدول فروشندگان (پرسنل)
    """
    __tablename__ = 'sellers'
    
    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey('departments.id', ondelete='CASCADE'), nullable=False)
    
    # شناسایی
    seller_code = Column(String(100), unique=True, nullable=False, index=True, comment='کد فروشنده (SEL-001)')
    name = Column(String(255), nullable=False, comment='نام فروشنده')
    username = Column(String(100), unique=True, nullable=True, comment='نام کاربری')
    
    # کمیسیون
    commission_rate = Column(DECIMAL(5, 2), default=Decimal('0'), comment='درصد کمیسیون')
    commission_type = Column(String(20), default='percentage', comment='نوع کمیسیون (percentage, fixed)')
    
    # آمار
    total_sales_count = Column(Integer, default=0, comment='تعداد فروش‌ها')
    total_sales_usdt = Column(DECIMAL(15, 4), default=Decimal('0'), comment='مجموع فروش (تتر)')
    total_commission_usdt = Column(DECIMAL(15, 4), default=Decimal('0'), comment='مجموع کمیسیون (تتر)')
    
    # وضعیت
    is_active = Column(Boolean, default=True, comment='فعال/غیرفعال')
    
    # تاریخ‌ها
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    notes = Column(Text, nullable=True)
    
    # روابط
    department = relationship("Department", back_populates="sellers")
    transactions = relationship("Transaction", back_populates="seller")
    silver_transactions = relationship("SilverTransaction", back_populates="seller")
    payments = relationship("Payment", back_populates="seller")
    
    __table_args__ = (
        Index('idx_seller_code', 'seller_code'),
        Index('idx_seller_department', 'department_id'),
    )
    
    def __repr__(self):
        return f"<Seller(id={self.id}, code='{self.seller_code}', name='{self.name}')>"
