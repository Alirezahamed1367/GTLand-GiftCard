"""
Simple Models - مدل‌های ساده و واضح برای سیستم جدید
====================================================
بر اساس Label به عنوان کلید اصلی
"""
from sqlalchemy import Column, Integer, String, Numeric, Text, DateTime, Boolean, ForeignKey, Index, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from decimal import Decimal
from enum import Enum

from .base_financial import FinancialBase


# ═══════════════════════════════════════════════════════════════
# 1. آکانت‌ها (اطلاعات اصلی هر خرید)
# ═══════════════════════════════════════════════════════════════

class Account(FinancialBase):
    """
    آکانت‌ها - هر خرید با Label یکتا
    
    مثال:
        Label: g450
        Email: test@example.com
        Supplier: mnar barno
        Status: Consumed
    """
    __tablename__ = 'accounts'
    
    id = Column(Integer, primary_key=True)
    
    # کلید اصلی
    label = Column(String(100), nullable=False, unique=True, index=True, comment="کد یکتا آکانت (g450, g451, ...)")
    
    # اطلاعات ثابت
    email = Column(String(300), nullable=True, index=True, comment="ایمیل آکانت")
    full_data = Column(Text, nullable=True, comment="داده کامل آکانت از شیت")
    
    # تامین‌کننده
    supplier = Column(String(200), nullable=True, comment="تامین‌کننده (mnar barno, amir, ...)")
    provider = Column(String(200), nullable=True, comment="ارائه‌دهنده")
    
    # وضعیت
    status = Column(String(50), nullable=True, index=True, comment="Consumed, Global, Silver Bonus")
    
    # منبع
    source_sheet = Column(String(200), nullable=True, comment="نام شیت خرید")
    
    # اطلاعات اضافی
    extra_data = Column(JSON, nullable=True, comment="سایر اطلاعات")
    
    # زمان‌ها
    created_at = Column(DateTime, default=datetime.now, index=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # روابط
    gold_purchases = relationship("AccountGold", back_populates="account", cascade="all, delete-orphan")
    silver_bonuses = relationship("AccountSilver", back_populates="account", cascade="all, delete-orphan")
    sales = relationship("Sale", back_populates="account", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Account(label='{self.label}', email='{self.email}')>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "label": self.label,
            "email": self.email,
            "supplier": self.supplier,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


# ═══════════════════════════════════════════════════════════════
# 2. خرید گلد (برای هر Label)
# ═══════════════════════════════════════════════════════════════

class AccountGold(FinancialBase):
    """
    خریدهای گلد - برای هر Label
    
    مثال:
        Label: g450
        Gold Quantity: 100
        Purchase Rate: 3.00
        Purchase Cost: 300.00$
    """
    __tablename__ = 'account_gold'
    
    id = Column(Integer, primary_key=True)
    
    # ارتباط با آکانت
    label = Column(String(100), ForeignKey('accounts.label'), nullable=False, index=True)
    account = relationship("Account", back_populates="gold_purchases")
    
    # مقدار گلد خریداری شده
    gold_quantity = Column(Numeric(20, 4), nullable=False, comment="مقدار گلد (100, 50, ...)")
    
    # نرخ خرید
    purchase_rate = Column(Numeric(20, 6), nullable=False, comment="نرخ خرید هر واحد گلد")
    
    # هزینه کل
    purchase_cost = Column(Numeric(20, 2), nullable=False, comment="gold_quantity × purchase_rate")
    
    # تاریخ خرید
    purchase_date = Column(DateTime, nullable=True, index=True)
    
    # شماره تراکنش
    transaction_id = Column(String(200), nullable=True)
    
    # سود گزارش شده توسط پرسنل (برای مغایرت‌گیری)
    staff_profit = Column(Numeric(20, 2), nullable=True, comment="سود گزارش شده توسط پرسنل فروش")
    
    # اطلاعات اضافی
    extra_data = Column(JSON, nullable=True)
    
    # زمان ثبت
    created_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<Sale(label='{self.label}', platform='{self.platform}', type='{self.sale_type}', qty={self.quantity})>"


# ═══════════════════════════════════════════════════════════════
# 3. بونوس سیلور (برای هر Label)
# ═══════════════════════════════════════════════════════════════

class AccountSilver(FinancialBase):
    """
    بونوس سیلور - رایگان با هر خرید
    
    مثال:
        Label: g450
        Silver Quantity: 20 (رایگان)
    """
    __tablename__ = 'account_silver'
    
    id = Column(Integer, primary_key=True)
    
    # ارتباط با آکانت
    label = Column(String(100), ForeignKey('accounts.label'), nullable=False, index=True)
    account = relationship("Account", back_populates="silver_bonuses")
    
    # مقدار سیلور رایگان
    silver_quantity = Column(Numeric(20, 4), nullable=False, comment="مقدار سیلور بونوس (20, 10, ...)")
    
    # تاریخ دریافت بونوس
    bonus_date = Column(DateTime, nullable=True)
    
    # اطلاعات اضافی
    extra_data = Column(JSON, nullable=True)
    
    # زمان ثبت
    created_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<AccountSilver(label='{self.label}', quantity={self.silver_quantity})>"


# ═══════════════════════════════════════════════════════════════
# 4. فروش‌ها (گلد یا سیلور)
# ═══════════════════════════════════════════════════════════════

class SaleType(str, Enum):
    """نوع فروش"""
    GOLD = "gold"
    SILVER = "silver"


class Sale(FinancialBase):
    """
    فروش‌ها - گلد یا سیلور
    
    مثال:
        Label: g450
        Type: gold
        Quantity: 10
        Rate: 4.50
        Amount: 45.00$
        Customer: PX
    """
    __tablename__ = 'sales'
    
    id = Column(Integer, primary_key=True)
    
    # ارتباط با آکانت
    label = Column(String(100), ForeignKey('accounts.label'), nullable=False, index=True)
    account = relationship("Account", back_populates="sales")
    
    # پلتفرم فروش (roblox, apple, nintendo, pubg, freefire, ...)
    # توجه: فعلاً String است - بعداً می‌توان به FK تبدیل کرد
    platform = Column(String(50), nullable=True, index=True, comment="پلتفرم فروش")
    
    # نوع فروش
    sale_type = Column(String(20), nullable=False, index=True, comment="gold یا silver")
    
    # مقدار فروش
    quantity = Column(Numeric(20, 4), nullable=False, comment="مقدار فروخته شده")
    
    # نرخ فروش
    sale_rate = Column(Numeric(20, 6), nullable=False, comment="نرخ فروش هر واحد")
    
    # مبلغ کل
    sale_amount = Column(Numeric(20, 2), nullable=False, comment="quantity × sale_rate")
    
    # مشتری
    customer = Column(String(200), nullable=True, index=True, comment="کد مشتری")
    
    # تاریخ فروش
    sale_date = Column(DateTime, nullable=True, index=True)
    
    # شماره تراکنش
    transaction_id = Column(String(200), nullable=True)
    
    # منبع
    source_sheet = Column(String(200), nullable=True, comment="Gift Bank PubG, Platforms")
    
    # سود گزارش شده توسط پرسنل (برای مغایرت‌گیری)
    staff_profit = Column(Numeric(20, 2), nullable=True, comment="سود گزارش شده توسط پرسنل فروش")
    
    # اطلاعات اضافی
    extra_data = Column(JSON, nullable=True)
    
    # زمان ثبت
    created_at = Column(DateTime, default=datetime.now)
    
    # Indexes
    __table_args__ = (
        Index('idx_sales_label_type', 'label', 'sale_type'),
        Index('idx_sales_customer_date', 'customer', 'sale_date'),
    )
    
    def __repr__(self):
        return f"<Sale(label='{self.label}', platform='{self.platform}', type='{self.sale_type}', quantity={self.quantity})>"


# ═══════════════════════════════════════════════════════════════
# 5. خلاصه محاسبات (Materialized View)
# ═══════════════════════════════════════════════════════════════

class AccountSummary(FinancialBase):
    """
    خلاصه محاسبات برای هر Label
    (این جدول به صورت خودکار از محاسبات پر می‌شود)
    
    شامل:
    - گلد: خرید، فروش، مانده، سود
    - سیلور: بونوس، فروش، مانده، سود
    - جمع کل
    """
    __tablename__ = 'account_summary'
    
    id = Column(Integer, primary_key=True)
    
    # کلید
    label = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(300), nullable=True, index=True)
    
    # ═══ گلد ═══
    total_gold_purchased = Column(Numeric(20, 4), default=0, comment="کل گلد خریداری شده")
    total_gold_sold = Column(Numeric(20, 4), default=0, comment="کل گلد فروخته شده")
    remaining_gold = Column(Numeric(20, 4), default=0, comment="مانده گلد")
    
    gold_purchase_cost = Column(Numeric(20, 2), default=0, comment="هزینه خرید گلد")
    gold_revenue = Column(Numeric(20, 2), default=0, comment="درآمد فروش گلد")
    gold_profit = Column(Numeric(20, 2), default=0, comment="سود گلد")
    gold_profit_percentage = Column(Numeric(10, 4), default=0, comment="درصد سود گلد")
    
    # ═══ سیلور ═══
    total_silver_bonus = Column(Numeric(20, 4), default=0, comment="کل سیلور بونوس")
    total_silver_sold = Column(Numeric(20, 4), default=0, comment="کل سیلور فروخته شده")
    remaining_silver = Column(Numeric(20, 4), default=0, comment="مانده سیلور")
    
    silver_revenue = Column(Numeric(20, 2), default=0, comment="درآمد فروش سیلور")
    silver_profit = Column(Numeric(20, 2), default=0, comment="سود سیلور (100% revenue)")
    
    # ═══ جمع کل ═══
    total_revenue = Column(Numeric(20, 2), default=0, comment="کل درآمد")
    total_profit = Column(Numeric(20, 2), default=0, comment="کل سود")
    total_cost = Column(Numeric(20, 2), default=0, comment="کل هزینه")
    
    # ═══ آمار ═══
    sale_count = Column(Integer, default=0, comment="تعداد فروش")
    unique_customers = Column(Integer, default=0, comment="تعداد مشتریان یکتا")
    last_sale_date = Column(DateTime, nullable=True, comment="آخرین فروش")
    
    # زمان‌ها
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<AccountSummary(label='{self.label}', total_profit={self.total_profit})>"
    
    def to_dict(self):
        return {
            "label": self.label,
            "email": self.email,
            "gold": {
                "purchased": float(self.total_gold_purchased) if self.total_gold_purchased else 0,
                "sold": float(self.total_gold_sold) if self.total_gold_sold else 0,
                "remaining": float(self.remaining_gold) if self.remaining_gold else 0,
                "cost": float(self.gold_purchase_cost) if self.gold_purchase_cost else 0,
                "revenue": float(self.gold_revenue) if self.gold_revenue else 0,
                "profit": float(self.gold_profit) if self.gold_profit else 0,
                "profit_pct": float(self.gold_profit_percentage) if self.gold_profit_percentage else 0
            },
            "silver": {
                "bonus": float(self.total_silver_bonus) if self.total_silver_bonus else 0,
                "sold": float(self.total_silver_sold) if self.total_silver_sold else 0,
                "remaining": float(self.remaining_silver) if self.remaining_silver else 0,
                "revenue": float(self.silver_revenue) if self.silver_revenue else 0,
                "profit": float(self.silver_profit) if self.silver_profit else 0
            },
            "total": {
                "revenue": float(self.total_revenue) if self.total_revenue else 0,
                "profit": float(self.total_profit) if self.total_profit else 0,
                "cost": float(self.total_cost) if self.total_cost else 0
            },
            "stats": {
                "sale_count": self.sale_count,
                "unique_customers": self.unique_customers,
                "last_sale_date": self.last_sale_date.isoformat() if self.last_sale_date else None
            }
        }


# ═══════════════════════════════════════════════════════════════
# 6. مشتریان
# ═══════════════════════════════════════════════════════════════

class Customer(FinancialBase):
    """
    مشتریان
    """
    __tablename__ = 'customers'
    
    id = Column(Integer, primary_key=True)
    
    # کد مشتری
    code = Column(String(200), unique=True, nullable=False, index=True)
    
    # نام (اختیاری)
    name = Column(String(300), nullable=True)
    
    # آمار
    total_purchases = Column(Integer, default=0, comment="تعداد خریدها")
    total_spent = Column(Numeric(20, 2), default=0, comment="مبلغ کل خرج شده")
    total_gold_bought = Column(Numeric(20, 4), default=0, comment="کل گلد خریداری شده")
    total_silver_bought = Column(Numeric(20, 4), default=0, comment="کل سیلور خریداری شده")
    
    # اطلاعات تماس (اختیاری)
    phone = Column(String(50), nullable=True)
    email = Column(String(200), nullable=True)
    
    # زمان‌ها
    first_purchase_at = Column(DateTime, nullable=True)
    last_purchase_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<Customer(code='{self.code}', purchases={self.total_purchases})>"
