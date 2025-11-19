"""
Stage 2: Processed Data Models - داده‌های پردازش شده
====================================================
تبدیل raw_data به مدل‌های کسب‌وکار: products, purchases, sales, bonuses, customers
"""
from sqlalchemy import Column, Integer, String, Numeric, Text, DateTime, Boolean, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from decimal import Decimal

from .base_financial import FinancialBase


class ProductV2(FinancialBase):
    """
    محصولات/اکانت‌ها
    
    هر محصول یک اکانت با موجودی داخلی است:
    - PUBG: CODE=G250, موجودی UC
    - Razer: Email, موجودی Gold
    - PSN: Code/Serial, موجودی Dollar
    """
    __tablename__ = 'v2_products'
    
    id = Column(Integer, primary_key=True)
    
    # شناسه محصول (از فیلدهایی که role=identifier دارند)
    identifier = Column(String(200), nullable=False, unique=True, index=True, comment="""
        شناسه محصول: CODE, Serial, Email, ...
    """)
    
    # نوع شناسه
    identifier_type = Column(String(50), nullable=True, comment="code, serial, email, phone")
    
    # پلتفرم
    platform = Column(String(100), nullable=True, index=True, comment="PUBG, Razer, PSN, XBOX, ...")
    
    # نوع محصول
    product_type = Column(String(100), nullable=True, comment="gift_card, gaming_account, voucher")
    
    # موجودی اولیه
    initial_balance = Column(Numeric(20, 4), default=0, comment="موجودی اولیه (UC, Gold, Dollar, ...)")
    
    # موجودی فعلی
    current_balance = Column(Numeric(20, 4), default=0, comment="موجودی فعلی")
    
    # واحد موجودی
    balance_unit = Column(String(50), nullable=True, comment="UC, Gold, Dollar, CP, ...")
    
    # مجموع فروش
    total_sold = Column(Numeric(20, 4), default=0, comment="مجموع فروش از این محصول")
    
    # مجموع بونوس
    total_bonus = Column(Numeric(20, 4), default=0, comment="مجموع بونوس/سیلور")
    
    # وضعیت
    status = Column(String(50), default='active', index=True, comment="""
        active, depleted (تمام شده), banned (مسدود), expired
    """)
    
    # اطلاعات اضافی (JSON)
    extra_data = Column(JSON, nullable=True, comment="""
        اطلاعات اضافی: email, password, serial, ...
    """)
    
    # منبع
    source_sheet = Column(String(200), nullable=True, comment="نام شیت منبع")
    raw_data_id = Column(Integer, ForeignKey('raw_data.id'), nullable=True)
    
    # زمان‌ها
    created_at = Column(DateTime, default=datetime.now, index=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    last_activity_at = Column(DateTime, nullable=True, comment="آخرین خرید/فروش")
    
    # روابط
    purchases = relationship("PurchaseV2", back_populates="product", cascade="all, delete-orphan")
    sales = relationship("SaleV2", back_populates="product", cascade="all, delete-orphan")
    bonuses = relationship("BonusV2", back_populates="product", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Product(id={self.id}, identifier='{self.identifier}', balance={self.current_balance})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "identifier": self.identifier,
            "platform": self.platform,
            "initial_balance": float(self.initial_balance) if self.initial_balance else 0,
            "current_balance": float(self.current_balance) if self.current_balance else 0,
            "balance_unit": self.balance_unit,
            "total_sold": float(self.total_sold) if self.total_sold else 0,
            "total_bonus": float(self.total_bonus) if self.total_bonus else 0,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PurchaseV2(FinancialBase):
    """
    خریدها
    
    ثبت خرید یک محصول/اکانت با موجودی اولیه
    """
    __tablename__ = 'v2_purchases'
    
    id = Column(Integer, primary_key=True)
    
    # محصول
    product_id = Column(Integer, ForeignKey('v2_products.id'), nullable=False, index=True)
    product = relationship("ProductV2", back_populates="purchases")
    
    # شماره تراکنش
    transaction_id = Column(String(200), nullable=True, index=True, comment="TR_ID")
    
    # مقدار خرید
    quantity = Column(Numeric(20, 4), nullable=False, comment="مقدار خریداری شده (UC, Gold, ...)")
    
    # نرخ خرید (به تتر/تومان)
    rate = Column(Numeric(20, 6), nullable=True, comment="نرخ خرید هر واحد")
    
    # مبلغ کل
    amount = Column(Numeric(20, 2), nullable=True, comment="مبلغ کل (تتر/تومان)")
    
    # واحد پول
    currency = Column(String(20), default='USDT', comment="USDT, IRT, USD")
    
    # تاریخ خرید
    purchase_date = Column(DateTime, nullable=True, index=True)
    
    # اطلاعات اضافی
    extra_data = Column(JSON, nullable=True)
    
    # منبع
    source_sheet = Column(String(200), nullable=True)
    raw_data_id = Column(Integer, ForeignKey('raw_data.id'), nullable=True)
    
    # زمان‌ها
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<Purchase(id={self.id}, product_id={self.product_id}, quantity={self.quantity})>"


class CustomerV2(FinancialBase):
    """
    مشتریان
    
    ردیابی مشتریان و خریدهای آن‌ها
    """
    __tablename__ = 'v2_customers'
    
    id = Column(Integer, primary_key=True)
    
    # شناسه مشتری
    customer_code = Column(String(200), nullable=False, unique=True, index=True, comment="""
        کد یا نام مشتری
    """)
    
    # نام کامل (اختیاری)
    full_name = Column(String(300), nullable=True)
    
    # اطلاعات تماس
    phone = Column(String(50), nullable=True)
    email = Column(String(200), nullable=True)
    
    # آمار
    total_purchases = Column(Integer, default=0, comment="تعداد کل خریدها")
    total_spent = Column(Numeric(20, 2), default=0, comment="مجموع مبلغ خرج شده")
    
    # وضعیت
    status = Column(String(50), default='active', comment="active, inactive, blocked")
    
    # اطلاعات اضافی
    extra_data = Column(JSON, nullable=True)
    
    # زمان‌ها
    first_purchase_at = Column(DateTime, nullable=True)
    last_purchase_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # روابط
    sales = relationship("SaleV2", back_populates="customer", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Customer(id={self.id}, code='{self.customer_code}')>"


class SaleV2(FinancialBase):
    """
    فروش‌ها
    
    ثبت فروش از یک محصول به یک مشتری
    (شامل فروش‌های گروه‌بندی شده)
    """
    __tablename__ = 'v2_sales'
    
    id = Column(Integer, primary_key=True)
    
    # محصول
    product_id = Column(Integer, ForeignKey('v2_products.id'), nullable=False, index=True)
    product = relationship("ProductV2", back_populates="sales")
    
    # مشتری
    customer_id = Column(Integer, ForeignKey('v2_customers.id'), nullable=False, index=True)
    customer = relationship("CustomerV2", back_populates="sales")
    
    # شماره تراکنش
    transaction_id = Column(String(200), nullable=True, index=True)
    
    # مقدار فروش
    quantity = Column(Numeric(20, 4), nullable=False, comment="مقدار فروخته شده")
    
    # نرخ فروش
    rate = Column(Numeric(20, 6), nullable=True, comment="نرخ فروش هر واحد")
    
    # مبلغ کل
    amount = Column(Numeric(20, 2), nullable=True, comment="مبلغ کل دریافتی")
    
    # واحد پول
    currency = Column(String(20), default='USDT')
    
    # سود/زیان
    profit = Column(Numeric(20, 2), nullable=True, comment="سود این فروش")
    profit_margin = Column(Numeric(10, 4), nullable=True, comment="درصد سود")
    
    # تاریخ فروش
    sale_date = Column(DateTime, nullable=True, index=True)
    
    # گروه‌بندی
    is_grouped = Column(Boolean, default=False, comment="آیا از چند ردیف گروه‌بندی شده؟")
    grouped_row_count = Column(Integer, default=1, comment="تعداد ردیف‌های گروه‌بندی شده")
    group_id = Column(String(64), nullable=True, index=True, comment="شناسه گروه")
    
    # منبع
    source_sheet = Column(String(200), nullable=True)
    raw_data_ids = Column(JSON, nullable=True, comment="لیست IDهای raw_data")
    
    # اطلاعات اضافی
    extra_data = Column(JSON, nullable=True)
    
    # زمان‌ها
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<Sale(id={self.id}, product_id={self.product_id}, customer_id={self.customer_id}, quantity={self.quantity})>"


class BonusV2(FinancialBase):
    """
    بونوس/سیلور
    
    ثبت بونوس‌های رایگان (سود 100%)
    """
    __tablename__ = 'v2_bonuses'
    
    id = Column(Integer, primary_key=True)
    
    # محصول
    product_id = Column(Integer, ForeignKey('v2_products.id'), nullable=False, index=True)
    product = relationship("ProductV2", back_populates="bonuses")
    
    # نوع بونوس
    bonus_type = Column(String(100), nullable=True, comment="silver, free_credit, promotion, ...")
    
    # مقدار بونوس
    quantity = Column(Numeric(20, 4), nullable=False, comment="مقدار بونوس")
    
    # منبع بونوس
    source = Column(String(200), nullable=True, comment="منبع بونوس: razer_activity, promotion, ...")
    
    # نرخ فروش (اگر فروخته شود)
    rate = Column(Numeric(20, 6), nullable=True)
    
    # درآمد کل (از فروش بونوس)
    revenue = Column(Numeric(20, 2), default=0, comment="درآمد از فروش بونوس (100% سود)")
    
    # تاریخ
    bonus_date = Column(DateTime, nullable=True, index=True)
    
    # وضعیت
    status = Column(String(50), default='available', comment="available, sold, expired")
    sold_date = Column(DateTime, nullable=True)
    
    # منبع
    source_sheet = Column(String(200), nullable=True)
    raw_data_id = Column(Integer, ForeignKey('raw_data.id'), nullable=True)
    
    # اطلاعات اضافی
    extra_data = Column(JSON, nullable=True)
    
    # زمان‌ها
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<Bonus(id={self.id}, product_id={self.product_id}, quantity={self.quantity}, status='{self.status}')>"


# Indexes برای بهبود عملکرد
Index('idx_v2_products_status', ProductV2.status, ProductV2.platform)
Index('idx_v2_purchases_date', PurchaseV2.purchase_date, PurchaseV2.product_id)
Index('idx_v2_sales_date', SaleV2.sale_date, SaleV2.product_id, SaleV2.customer_id)
Index('idx_v2_sales_grouped', SaleV2.is_grouped, SaleV2.group_id)
Index('idx_v2_bonuses_status', BonusV2.status, BonusV2.product_id)
Index('idx_v2_customers_status', CustomerV2.status, CustomerV2.last_purchase_at)
