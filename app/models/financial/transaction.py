"""
مدل معامله - Transaction Model  
معاملات فروش محصولات (Gold)
"""
from sqlalchemy import Column, Integer, String, Boolean, Text, TIMESTAMP, DECIMAL, Date, Time, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from decimal import Decimal
from .base_financial import FinancialBase


class Transaction(FinancialBase):
    """
    جدول معاملات فروش (Gold)
    """
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey('departments.id', ondelete='CASCADE'), nullable=False)
    
    # ارتباطات
    account_id = Column(Integer, ForeignKey('accounts.id', ondelete='CASCADE'), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey('customers.id', ondelete='SET NULL'), nullable=True, index=True)
    seller_id = Column(Integer, ForeignKey('sellers.id', ondelete='SET NULL'), nullable=True, index=True)
    
    # شناسایی
    transaction_code = Column(String(100), unique=True, nullable=False, comment='کد معامله (TRX-20251113-0001)')
    
    # محصول فروخته شده
    product_type = Column(String(100), nullable=False, index=True, comment='نوع محصول (COD, PUBG, PS5, ...)')
    product_name = Column(String(255), nullable=True, comment='نام دقیق محصول')
    
    # مقدار
    amount_sold = Column(DECIMAL(15, 2), nullable=False, comment='مقدار فروخته شده')
    amount_unit = Column(String(20), nullable=False, comment='واحد (CP, UC, USD, ...)')
    consumed_from_account = Column(DECIMAL(15, 2), nullable=False, comment='مقدار کسر شده از آکانت')
    
    # قیمت‌گذاری
    sale_rate = Column(DECIMAL(10, 4), nullable=False, comment='ریت فروش')
    sale_price_usdt = Column(DECIMAL(15, 4), nullable=False, comment='قیمت فروش (تتر)')
    sale_price_irr = Column(DECIMAL(20, 2), nullable=True, comment='قیمت فروش (تومان)')
    payment_currency = Column(String(10), default='USDT', comment='واحد پول (USDT, IRR)')
    
    # تاریخ
    transaction_date = Column(Date, nullable=False, index=True, comment='تاریخ معامله')
    transaction_time = Column(Time, nullable=True, comment='ساعت معامله')
    
    # وضعیت
    status = Column(String(20), default='completed', comment='وضعیت (completed, pending, cancelled, refunded)')
    is_paid = Column(Boolean, default=False, comment='آیا پرداخت شده؟')
    paid_at = Column(TIMESTAMP, nullable=True, comment='تاریخ پرداخت')
    
    # محاسبات
    cost_usdt = Column(DECIMAL(15, 4), nullable=False, comment='بهای تمام شده')
    profit_usdt = Column(DECIMAL(15, 4), nullable=False, comment='سود')
    profit_margin = Column(DECIMAL(5, 2), nullable=True, comment='درصد سود')
    
    # کمیسیون فروشنده
    seller_commission = Column(DECIMAL(15, 4), default=Decimal('0'), comment='کمیسیون فروشنده')
    
    # ارتباط با Google Sheets
    source_sheet_id = Column(Integer, nullable=True, comment='شناسه sheet_config')
    source_row_number = Column(Integer, nullable=True, comment='شماره ردیف در شیت')
    sales_data_id = Column(Integer, nullable=True, index=True, comment='شناسه sales_data')
    
    # تاریخ‌ها
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    notes = Column(Text, nullable=True)
    
    # روابط
    department = relationship("Department", back_populates="transactions")
    account = relationship("Account", back_populates="transactions")
    customer = relationship("Customer", back_populates="transactions")
    seller = relationship("Seller", back_populates="transactions")
    
    __table_args__ = (
        Index('idx_transaction_code', 'transaction_code'),
        Index('idx_transaction_date', 'transaction_date'),
        Index('idx_transaction_account', 'account_id'),
        Index('idx_transaction_customer', 'customer_id'),
        Index('idx_transaction_product_type', 'product_type'),
        Index('idx_transaction_sales_data', 'sales_data_id'),
    )
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, code='{self.transaction_code}', product='{self.product_type}')>"
    
    def calculate_profit(self, account_purchase_rate):
        """محاسبه سود"""
        # بهای تمام شده = (مقدار مصرفی از آکانت * ریت خرید) / 100
        self.cost_usdt = (self.consumed_from_account * account_purchase_rate) / Decimal('100')
        
        # سود = فروش - بهای تمام شده
        self.profit_usdt = self.sale_price_usdt - self.cost_usdt
        
        # درصد سود
        if self.cost_usdt > 0:
            self.profit_margin = (self.profit_usdt / self.cost_usdt) * Decimal('100')
        else:
            self.profit_margin = Decimal('0')
