"""
مدل‌های سیستم پویا برای Field Mapping
این سیستم به کاربر اجازه می‌دهد تا نقش هر ستون را خودش تعریف کند
"""
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.models.financial.base_financial import FinancialBase


class SheetType(enum.Enum):
    """نوع شیت"""
    PURCHASE = "purchase"  # خرید
    SALE = "sale"          # فروش
    BONUS = "bonus"        # بونوس/سیلور
    OTHER = "other"        # سایر


class DataType(enum.Enum):
    """نوع داده فیلد"""
    TEXT = "text"
    DECIMAL = "decimal"
    INTEGER = "integer"
    DATE = "date"
    BOOLEAN = "boolean"


class TargetField(enum.Enum):
    """نقش‌های ممکن برای فیلدها"""
    # فیلدهای اصلی
    ACCOUNT_ID = "account_id"          # Label
    EMAIL = "email"
    SUPPLIER = "supplier"
    
    # فیلدهای خرید
    GOLD_QUANTITY = "gold_quantity"
    PURCHASE_RATE = "purchase_rate"
    PURCHASE_COST = "purchase_cost"
    PURCHASE_DATE = "purchase_date"
    
    # فیلدهای بونوس
    SILVER_BONUS = "silver_bonus"
    
    # فیلدهای فروش
    SALE_QUANTITY = "sale_quantity"
    SALE_RATE = "sale_rate"
    SALE_TYPE = "sale_type"            # gold/silver
    CUSTOMER_CODE = "customer_code"
    SALE_DATE = "sale_date"
    
    # فیلد مغایرت‌گیری
    STAFF_PROFIT = "staff_profit"      # سود گزارش شده توسط پرسنل
    
    # سایر
    NOTES = "notes"
    STATUS = "status"
    IGNORE = "ignore"                  # نادیده گرفته می‌شود


class SheetImport(FinancialBase):
    """
    اطلاعات شیت‌های Import شده
    """
    __tablename__ = 'sheet_imports'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sheet_name = Column(String(200), nullable=False)
    import_date = Column(DateTime, default=datetime.now, nullable=False)
    source_url = Column(Text, nullable=True)  # URL گوگل شیت
    sheet_type = Column(SQLEnum(SheetType), nullable=False)
    platform = Column(String(50), nullable=True)  # برای sale: roblox, apple, etc.
    total_rows = Column(Integer, default=0)
    processed_rows = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    
    # روابط
    raw_data = relationship("RawData", back_populates="sheet_import", cascade="all, delete-orphan")
    field_mappings = relationship("FieldMapping", back_populates="sheet_import", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SheetImport(name='{self.sheet_name}', type='{self.sheet_type.value}', rows={self.total_rows})>"


class RawData(FinancialBase):
    """
    داده‌های خام Import شده (بدون پردازش)
    """
    __tablename__ = 'raw_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sheet_import_id = Column(Integer, ForeignKey('sheet_imports.id', ondelete='CASCADE'), nullable=False)
    row_number = Column(Integer, nullable=False)
    data = Column(JSON, nullable=False)  # {"Label": "A1054", "Gold": 535, ...}
    processed = Column(Boolean, default=False)
    processing_errors = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # روابط
    sheet_import = relationship("SheetImport", back_populates="raw_data")
    
    def __repr__(self):
        return f"<RawData(id={self.id}, row={self.row_number}, processed={self.processed})>"


class FieldMapping(FinancialBase):
    """
    نقشه‌برداری فیلدها - کاربر تعریف می‌کند هر ستون چه نقشی دارد
    """
    __tablename__ = 'field_mappings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sheet_import_id = Column(Integer, ForeignKey('sheet_imports.id', ondelete='CASCADE'), nullable=False)
    source_column = Column(String(200), nullable=False)  # نام ستون در شیت
    target_field = Column(SQLEnum(TargetField), nullable=False)  # نقش در سیستم
    data_type = Column(SQLEnum(DataType), nullable=False)
    is_required = Column(Boolean, default=False)
    default_value = Column(String(100), nullable=True)
    transformation_rule = Column(Text, nullable=True)  # مثلاً: برای تبدیل فرمت
    
    # روابط
    sheet_import = relationship("SheetImport", back_populates="field_mappings")
    
    def __repr__(self):
        return f"<FieldMapping({self.source_column} → {self.target_field.value})>"


class Platform(FinancialBase):
    """
    پلتفرم‌های فروش (Roblox, Apple, Nintendo, ...)
    """
    __tablename__ = 'platforms'
    
    code = Column(String(50), primary_key=True)  # roblox, apple, nintendo
    name = Column(String(100), nullable=False)   # Roblox, Apple Gift Card
    is_active = Column(Boolean, default=True)
    default_commission = Column(String(10), nullable=True)  # اختیاری
    notes = Column(Text, nullable=True)
    
    # توجه: relationship به Sale حذف شد چون platform فعلاً String است نه FK
    
    def __repr__(self):
        return f"<Platform(code='{self.code}', name='{self.name}')>"


class DiscrepancyReport(FinancialBase):
    """
    گزارش مغایرت‌ها - مقایسه سود محاسبه شده با سود پرسنل
    """
    __tablename__ = 'discrepancy_reports'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    label = Column(String(50), ForeignKey('accounts.label', ondelete='CASCADE'), nullable=False)
    calculated_profit = Column(String(20), nullable=False)  # سود محاسبه شده توسط سیستم
    staff_profit = Column(String(20), nullable=True)        # سود گزارش شده توسط پرسنل
    discrepancy = Column(String(20), nullable=True)         # اختلاف
    discrepancy_percent = Column(String(10), nullable=True) # درصد اختلاف
    checked_date = Column(DateTime, default=datetime.now)
    notes = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<DiscrepancyReport(label='{self.label}', diff={self.discrepancy})>"


class CustomReport(FinancialBase):
    """
    گزارش‌های سفارشی کاربر
    """
    __tablename__ = 'custom_reports'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_name = Column(String(200), nullable=False)
    report_type = Column(String(50), nullable=False)  # label, platform, customer, custom
    filters = Column(JSON, nullable=True)  # {"platform": "roblox", "date_from": "2024-01-01"}
    columns = Column(JSON, nullable=True)  # ["label", "gold_sold", "profit"]
    aggregations = Column(JSON, nullable=True)  # {"profit": "sum", "quantity": "avg"}
    sort_by = Column(String(100), nullable=True)
    created_date = Column(DateTime, default=datetime.now)
    is_favorite = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<CustomReport(name='{self.report_name}', type='{self.report_type}')>"
