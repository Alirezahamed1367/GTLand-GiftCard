"""
مدل پرداخت - Payment Model
"""
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, DECIMAL, Date, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from decimal import Decimal
from .base_financial import FinancialBase


class Payment(FinancialBase):
    """
    جدول پرداخت‌ها
    """
    __tablename__ = 'payments'
    
    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey('departments.id', ondelete='CASCADE'), nullable=False)
    
    # نوع پرداخت
    payment_type = Column(
        String(50), 
        nullable=False, 
        index=True,
        comment='نوع (customer_payment, supplier_payment, seller_commission)'
    )
    
    # ارتباطات
    customer_id = Column(Integer, ForeignKey('customers.id', ondelete='SET NULL'), nullable=True)
    supplier_id = Column(Integer, ForeignKey('suppliers.id', ondelete='SET NULL'), nullable=True)
    seller_id = Column(Integer, ForeignKey('sellers.id', ondelete='SET NULL'), nullable=True)
    
    # شناسایی
    payment_code = Column(String(100), unique=True, nullable=False, comment='کد پرداخت (PAY-20251113-0001)')
    
    # مبلغ
    amount_usdt = Column(DECIMAL(15, 4), default=Decimal('0'), comment='مبلغ (تتر)')
    amount_irr = Column(DECIMAL(20, 2), default=Decimal('0'), comment='مبلغ (تومان)')
    payment_currency = Column(String(10), nullable=False, comment='واحد پول (USDT, IRR)')
    exchange_rate = Column(DECIMAL(15, 2), nullable=True, comment='نرخ تبدیل')
    
    # اطلاعات پرداخت
    payment_method = Column(String(50), nullable=True, comment='روش پرداخت (bank_transfer, cash, crypto, card)')
    transaction_id = Column(String(255), nullable=True, comment='شماره تراکنش')
    payment_date = Column(Date, nullable=False, index=True, comment='تاریخ پرداخت')
    
    # وضعیت
    status = Column(String(20), default='completed', comment='وضعیت (completed, pending, failed, cancelled)')
    
    # تاریخ‌ها
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # رسید
    receipt_path = Column(String(500), nullable=True, comment='مسیر فایل رسید')
    notes = Column(Text, nullable=True)
    
    # روابط
    department = relationship("Department", back_populates="payments")
    customer = relationship("Customer", back_populates="payments")
    supplier = relationship("Supplier", back_populates="payments")
    seller = relationship("Seller", back_populates="payments")
    
    __table_args__ = (
        Index('idx_payment_code', 'payment_code'),
        Index('idx_payment_type', 'payment_type'),
        Index('idx_payment_date', 'payment_date'),
        Index('idx_payment_customer', 'customer_id'),
        Index('idx_payment_supplier', 'supplier_id'),
    )
    
    def __repr__(self):
        return f"<Payment(id={self.id}, code='{self.payment_code}', type='{self.payment_type}')>"
