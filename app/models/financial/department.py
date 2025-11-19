"""
مدل دپارتمان - Department Model
"""
from sqlalchemy import Column, Integer, String, Boolean, Text, TIMESTAMP, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base_financial import FinancialBase


class Department(FinancialBase):
    """
    جدول دپارتمان‌ها (Top-Up و Gift-Card)
    """
    __tablename__ = 'departments'
    
    # ستون‌های اصلی
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, comment='کد دپارتمان (TOPUP, GIFTCARD)')
    name = Column(String(255), nullable=False, comment='نام دپارتمان')
    
    # Prefix‌ها برای شماره‌گذاری خودکار
    warehouse_prefix = Column(String(10), default='W1-', comment='پیشوند شماره انبار')
    product_code_prefix = Column(String(10), default='P1-', comment='پیشوند کد کالا')
    customer_code_prefix = Column(String(10), default='C1-', comment='پیشوند کد مشتری')
    
    # وضعیت
    is_active = Column(Boolean, default=True, comment='فعال/غیرفعال')
    
    # توضیحات
    description = Column(Text, nullable=True, comment='توضیحات')
    
    # تاریخ‌ها
    created_at = Column(TIMESTAMP, server_default=func.now(), comment='تاریخ ایجاد')
    updated_at = Column(
        TIMESTAMP, 
        server_default=func.now(), 
        onupdate=func.now(), 
        comment='تاریخ بروزرسانی'
    )
    
    # روابط
    accounts = relationship("Account", back_populates="department", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="department", cascade="all, delete-orphan")
    sellers = relationship("Seller", back_populates="department", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="department")
    silver_transactions = relationship("SilverTransaction", back_populates="department")
    payments = relationship("Payment", back_populates="department")
    product_types = relationship("ProductType", back_populates="department")
    
    # ایندکس‌ها
    __table_args__ = (
        Index('idx_department_code', 'code'),
        Index('idx_department_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<Department(id={self.id}, code='{self.code}', name='{self.name}')>"
    
    def to_dict(self):
        """تبدیل به دیکشنری"""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'warehouse_prefix': self.warehouse_prefix,
            'product_code_prefix': self.product_code_prefix,
            'customer_code_prefix': self.customer_code_prefix,
            'is_active': self.is_active,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
