"""
مدل معامله Silver - SilverTransaction Model
معاملات فروش Silver/Bonus
"""
from sqlalchemy import Column, Integer, String, Boolean, Text, TIMESTAMP, DECIMAL, Date, Time, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from decimal import Decimal
from .base_financial import FinancialBase


class SilverTransaction(FinancialBase):
    """
    جدول معاملات Silver/Bonus
    """
    __tablename__ = 'silver_transactions'
    
    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey('departments.id', ondelete='CASCADE'), nullable=False)
    
    # ارتباطات
    account_id = Column(Integer, ForeignKey('accounts.id', ondelete='CASCADE'), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey('customers.id', ondelete='SET NULL'), nullable=True, index=True)
    seller_id = Column(Integer, ForeignKey('sellers.id', ondelete='SET NULL'), nullable=True, index=True)
    
    # شناسایی
    transaction_code = Column(String(100), unique=True, nullable=False, comment='کد معامله (SLV-20251113-0001)')
    
    # محصول
    product_type = Column(String(100), nullable=False, comment='نوع محصول')
    product_name = Column(String(255), nullable=True, comment='نام محصول')
    
    # مقدار Silver
    silver_amount = Column(DECIMAL(15, 2), nullable=False, comment='مقدار Silver فروخته شده')
    silver_unit = Column(String(20), nullable=False, comment='واحد Silver')
    
    # قیمت
    sale_rate = Column(DECIMAL(10, 4), nullable=False, comment='ریت فروش')
    sale_price_usdt = Column(DECIMAL(15, 4), nullable=False, comment='قیمت فروش (تتر)')
    sale_price_irr = Column(DECIMAL(20, 2), nullable=True, comment='قیمت فروش (تومان)')
    payment_currency = Column(String(10), default='USDT', comment='واحد پول')
    
    # تاریخ
    transaction_date = Column(Date, nullable=False, index=True, comment='تاریخ معامله')
    transaction_time = Column(Time, nullable=True, comment='ساعت معامله')
    
    # وضعیت
    status = Column(String(20), default='completed', comment='وضعیت')
    is_paid = Column(Boolean, default=False, comment='آیا پرداخت شده؟')
    paid_at = Column(TIMESTAMP, nullable=True, comment='تاریخ پرداخت')
    
    # محاسبات (Silver همیشه سود است)
    profit_usdt = Column(DECIMAL(15, 4), nullable=False, comment='سود (تتر)')
    
    # کمیسیون
    seller_commission = Column(DECIMAL(15, 4), default=Decimal('0'), comment='کمیسیون فروشنده')
    
    # ارتباط با Sheets
    source_sheet_id = Column(Integer, nullable=True)
    source_row_number = Column(Integer, nullable=True)
    sales_data_id = Column(Integer, nullable=True, index=True)
    
    # تاریخ‌ها
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    notes = Column(Text, nullable=True)
    
    # روابط
    department = relationship("Department", back_populates="silver_transactions")
    account = relationship("Account", back_populates="silver_transactions")
    customer = relationship("Customer", back_populates="silver_transactions")
    seller = relationship("Seller", back_populates="silver_transactions")
    
    __table_args__ = (
        Index('idx_silver_transaction_code', 'transaction_code'),
        Index('idx_silver_transaction_date', 'transaction_date'),
        Index('idx_silver_transaction_account', 'account_id'),
        Index('idx_silver_transaction_customer', 'customer_id'),
    )
    
    def __repr__(self):
        return f"<SilverTransaction(id={self.id}, code='{self.transaction_code}')>"
    
    def calculate_profit(self):
        """محاسبه سود (Silver بدون هزینه است)"""
        self.profit_usdt = self.sale_price_usdt
