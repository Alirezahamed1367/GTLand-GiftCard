"""
Custom Field Models - سیستم فیلدهای قابل تنظیم توسط کاربر
==================================================================
این مدل‌ها به کاربر اجازه می‌دهند فیلدهای سفارشی تعریف کند
نقش‌ها (Roles) نیز توسط کاربر قابل تعریف هستند
"""
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from .base_financial import FinancialBase


class CustomField(FinancialBase):
    """
    فیلدهای سفارشی کاربر
    کاربر می‌تواند برای هر نوع تراکنش فیلدهای دلخواه خود را تعریف کند
    """
    __tablename__ = 'custom_fields'
    
    id = Column(Integer, primary_key=True)
    
    # مشخصات فیلد
    name = Column(String(100), nullable=False, unique=True, comment="نام فیلد (انگلیسی)")
    label_fa = Column(String(200), nullable=False, comment="برچسب فارسی")
    
    # نوع داده
    data_type = Column(String(50), nullable=False, default='text', comment="""
        نوع داده: text, number, decimal, date, datetime, boolean, email, phone, url
    """)
    
    # نقش در سیستم (ارجاع به FieldRole)
    role_id = Column(Integer, ForeignKey('field_roles.id'), nullable=True, comment="نقش این فیلد (از جدول field_roles)")
    role = relationship("FieldRole", foreign_keys=[role_id])
    
    # دسته‌بندی
    category = Column(String(50), nullable=False, default='common', comment="""
        دسته: common (مشترک), purchase (خرید), sale (فروش), 
        silver (سیلور), financial (مالی), inventory (موجودی)
    """)
    
    # ویژگی‌های اعتبارسنجی
    is_required = Column(Boolean, default=False, comment="آیا الزامی است؟")
    is_unique = Column(Boolean, default=False, comment="آیا باید یکتا باشد؟")
    min_value = Column(String(50), nullable=True, comment="حداقل مقدار (برای اعداد)")
    max_value = Column(String(50), nullable=True, comment="حداکثر مقدار (برای اعداد)")
    pattern = Column(String(200), nullable=True, comment="الگوی Regex برای اعتبارسنجی")
    
    # مقدار پیش‌فرض
    default_value = Column(Text, nullable=True, comment="مقدار پیش‌فرض")
    
    # فرمول (برای فیلدهای محاسبه شده)
    formula = Column(Text, nullable=True, comment="""
        فرمول محاسبه (مثال: {unit_price} * {quantity})
        از {} برای ارجاع به فیلدهای دیگر استفاده کنید
    """)
    
    # ترتیب نمایش
    display_order = Column(Integer, default=100, comment="ترتیب نمایش در فرم‌ها")
    
    # توضیحات
    description = Column(Text, nullable=True, comment="توضیحات تکمیلی")
    
    # متادیتا
    metadata_json = Column(JSON, nullable=True, comment="""
        اطلاعات اضافی (لیست انتخاب، فیلترها، قالب نمایش و...)
    """)
    
    # وضعیت
    is_active = Column(Boolean, default=True, comment="فعال/غیرفعال")
    
    # زمان‌ها
    created_at = Column(DateTime, default=datetime.now, comment="تاریخ ایجاد")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="تاریخ بروزرسانی")
    
    # روابط
    mappings = relationship("FieldMapping", back_populates="custom_field", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CustomField(name='{self.name}', label='{self.label_fa}', category='{self.category}')>"
    
    def to_dict(self):
        """تبدیل به دیکشنری"""
        return {
            "id": self.id,
            "name": self.name,
            "label_fa": self.label_fa,
            "data_type": self.data_type,
            "role_id": self.role_id,
            "role_name": self.role.name if self.role else None,
            "role_label": self.role.label_fa if self.role else None,
            "category": self.category,
            "is_required": self.is_required,
            "is_unique": self.is_unique,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "pattern": self.pattern,
            "default_value": self.default_value,
            "formula": self.formula,
            "display_order": self.display_order,
            "description": self.description,
            "metadata_json": self.metadata_json,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class FieldMapping(FinancialBase):
    """
    نگاشت فیلدهای سفارشی به ستون‌های شیت
    """
    __tablename__ = 'field_mappings'
    
    id = Column(Integer, primary_key=True)
    
    # فیلد سفارشی
    field_id = Column(Integer, ForeignKey('custom_fields.id'), nullable=False)
    custom_field = relationship("CustomField", back_populates="mappings")
    
    # مشخصات شیت
    sheet_name = Column(String(200), nullable=False, comment="نام شیت گوگل")
    sheet_id = Column(String(100), nullable=True, comment="شناسه شیت (اختیاری)")
    
    # نگاشت ستون
    column_name = Column(String(100), nullable=False, comment="نام ستون در شیت")
    column_index = Column(Integer, nullable=True, comment="شماره ستون (0-based)")
    column_letter = Column(String(5), nullable=True, comment="حرف ستون (A, B, C, ...)")
    
    # تبدیل داده
    transformation = Column(Text, nullable=True, comment="""
        کد Python برای تبدیل داده (اختیاری)
        مثال: lambda x: float(x.replace(',', ''))
    """)
    
    # اعتبارسنجی
    validation_rule = Column(Text, nullable=True, comment="قانون اعتبارسنجی (Python expression)")
    
    # وضعیت
    is_active = Column(Boolean, default=True)
    
    # زمان‌ها
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<FieldMapping(field='{self.custom_field.name if self.custom_field else 'N/A'}', column='{self.column_name}')>"


class TransactionSchema(FinancialBase):
    """
    طرح‌واره (Schema) هر نوع تراکنش
    برای خرید، فروش، سیلور و ... فیلدهای مختلف تعریف می‌شود
    """
    __tablename__ = 'transaction_schemas'
    
    id = Column(Integer, primary_key=True)
    
    # نوع تراکنش
    transaction_type = Column(String(50), nullable=False, unique=True, comment="""
        نوع: purchase (خرید), sale (فروش), silver (سیلور), 
        inventory (موجودی), payment (پرداخت)
    """)
    
    # عنوان
    title_fa = Column(String(200), nullable=False, comment="عنوان فارسی")
    
    # فیلدهای مربوطه (JSON array of field names)
    field_names = Column(JSON, nullable=False, default=list, comment="""
        لیست نام فیلدها که به این تراکنش تعلق دارند
        مثال: ["account_number", "initial_balance", "purchase_price"]
    """)
    
    # تنظیمات نمایش
    display_config = Column(JSON, nullable=True, comment="""
        تنظیمات نمایش فرم (layout, grouping, tabs)
    """)
    
    # قوانین کسب‌وکار
    business_rules = Column(JSON, nullable=True, comment="""
        قوانین کسب‌وکار (محاسبات، اعتبارسنجی‌های پیچیده)
    """)
    
    # وضعیت
    is_active = Column(Boolean, default=True)
    
    # زمان‌ها
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<TransactionSchema(type='{self.transaction_type}', title='{self.title_fa}')>"
    
    def get_fields(self, db_session):
        """دریافت فیلدهای مربوطه"""
        from sqlalchemy import and_
        
        if not self.field_names:
            return []
        
        return db_session.query(CustomField).filter(
            and_(
                CustomField.name.in_(self.field_names),
                CustomField.is_active == True
            )
        ).order_by(CustomField.display_order).all()
