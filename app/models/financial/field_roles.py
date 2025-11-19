"""
Field Roles - سیستم نقش‌های کاملاً داینامیک
=============================================
کاربر نقش‌ها را خودش تعریف می‌کند - هیچ نقش از پیش تعریف شده‌ای نداریم
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from .base_financial import FinancialBase


class FieldRole(FinancialBase):
    """
    نقش‌های فیلدها (کاملاً قابل تعریف توسط کاربر)
    
    مثال‌های نقش:
    - شناسه اکانت (identifier)
    - مقدار موجودی (value)
    - شماره تراکنش (transaction_id)
    - تاریخ فروش (sale_date)
    - نام مشتری (customer_name)
    - نرخ فروش (sale_rate)
    - سریال محصول (serial_number)
    - ایمیل اکانت (email)
    - پسورد (password)
    """
    __tablename__ = 'field_roles'
    
    id = Column(Integer, primary_key=True)
    
    # مشخصات نقش
    name = Column(String(100), nullable=False, unique=True, comment="نام نقش (انگلیسی، بدون فاصله)")
    label_fa = Column(String(200), nullable=False, comment="برچسب فارسی")
    label_en = Column(String(200), nullable=True, comment="برچسب انگلیسی (اختیاری)")
    
    # توضیحات
    description = Column(Text, nullable=True, comment="توضیح کامل این نقش")
    
    # دسته‌بندی
    category = Column(String(50), nullable=True, comment="""
        دسته‌بندی: core (اصلی), business (کسب‌وکار), 
        technical (فنی), custom (سفارشی)
    """)
    
    # ویژگی‌های خاص
    properties = Column(JSON, nullable=True, comment="ویژگی‌های خاص: is_identifier, is_searchable, is_filterable, is_groupable, is_aggregatable, data_type_hint, format_pattern")
    
    # استفاده در unique key
    used_in_unique_key = Column(Boolean, default=False, comment="""
        آیا این نقش در تولید Unique Key استفاده می‌شود؟
        مثلاً: CODE, TR_ID, Date, Customer, Rate
    """)
    
    # اولویت در unique key
    unique_key_priority = Column(Integer, nullable=True, comment="""
        اولویت در ترکیب unique key (1=بالاترین)
    """)
    
    # استفاده در گروه‌بندی
    used_in_grouping = Column(Boolean, default=False, comment="""
        آیا این نقش در گروه‌بندی فروش‌ها استفاده می‌شود؟
        مثلاً: Date, CODE, Customer, Rate
    """)
    
    # آیکون (اختیاری)
    icon = Column(String(50), nullable=True, comment="نام آیکون برای UI")
    
    # رنگ (اختیاری)
    color = Column(String(20), nullable=True, comment="رنگ برای UI (hex: #FF5733)")
    
    # ترتیب نمایش
    display_order = Column(Integer, default=100)
    
    # وضعیت
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False, comment="""
        آیا نقش سیستمی است؟ (نمی‌توان حذف کرد)
        فقط برای نقش‌های پیش‌فرض اولیه
    """)
    
    # زمان‌ها
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = Column(String(100), nullable=True, comment="کاربر ایجادکننده")
    
    def __repr__(self):
        return f"<FieldRole(name='{self.name}', label='{self.label_fa}')>"
    
    def to_dict(self):
        """تبدیل به دیکشنری"""
        return {
            "id": self.id,
            "name": self.name,
            "label_fa": self.label_fa,
            "label_en": self.label_en,
            "description": self.description,
            "category": self.category,
            "properties": self.properties,
            "used_in_unique_key": self.used_in_unique_key,
            "unique_key_priority": self.unique_key_priority,
            "used_in_grouping": self.used_in_grouping,
            "icon": self.icon,
            "color": self.color,
            "display_order": self.display_order,
            "is_active": self.is_active,
            "is_system": self.is_system,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class RolePreset(FinancialBase):
    """
    پیش‌فرض‌های نقش (Presets) برای شروع سریع
    کاربر می‌تواند از پیش‌فرض‌ها استفاده کند یا نقش‌های جدید بسازد
    """
    __tablename__ = 'role_presets'
    
    id = Column(Integer, primary_key=True)
    
    # مشخصات پیش‌فرض
    name = Column(String(100), nullable=False, unique=True, comment="نام پیش‌فرض")
    title_fa = Column(String(200), nullable=False, comment="عنوان فارسی")
    description = Column(Text, nullable=True)
    
    # نقش‌های پیشنهادی
    suggested_roles = Column(JSON, nullable=False, comment="لیست نقش‌های پیشنهادی شامل name, label_fa, properties")
    
    # دسته‌بندی
    category = Column(String(50), nullable=True, comment="""
        gift_cards, gaming, digital_products, ...
    """)
    
    # وضعیت
    is_active = Column(Boolean, default=True)
    
    # زمان‌ها
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<RolePreset(name='{self.name}', title='{self.title_fa}')>"


def init_default_roles(db_session):
    """
    ایجاد نقش‌های پیش‌فرض اولیه (فقط برای راهنمایی)
    کاربر می‌تواند آن‌ها را ویرایش/حذف/اضافه کند
    """
    default_roles = [
        # نقش‌های اصلی (Core)
        {
            "name": "identifier",
            "label_fa": "شناسه",
            "label_en": "Identifier",
            "description": "شناسه منحصر به فرد (مثل CODE، Serial، Email)",
            "category": "core",
            "properties": {
                "is_identifier": True,
                "is_searchable": True,
                "is_filterable": True,
                "data_type_hint": "text"
            },
            "used_in_unique_key": True,
            "unique_key_priority": 1,
            "icon": "🔑",
            "is_system": True
        },
        {
            "name": "value",
            "label_fa": "مقدار/موجودی",
            "label_en": "Value/Balance",
            "description": "مقدار یا موجودی (UC، Gold، Dollar، CP)",
            "category": "core",
            "properties": {
                "is_aggregatable": True,
                "data_type_hint": "decimal",
                "format_pattern": "###,###.##"
            },
            "used_in_unique_key": True,
            "unique_key_priority": 4,
            "icon": "💰",
            "is_system": True
        },
        {
            "name": "transaction_id",
            "label_fa": "شماره تراکنش",
            "label_en": "Transaction ID",
            "description": "شماره منحصر به فرد تراکنش (TR_ID)",
            "category": "core",
            "properties": {
                "is_identifier": True,
                "is_searchable": True,
                "data_type_hint": "text"
            },
            "used_in_unique_key": True,
            "unique_key_priority": 2,
            "icon": "🔖",
            "is_system": True
        },
        {
            "name": "date",
            "label_fa": "تاریخ",
            "label_en": "Date",
            "description": "تاریخ رویداد (فروش، خرید، ...)",
            "category": "core",
            "properties": {
                "is_filterable": True,
                "is_groupable": True,
                "data_type_hint": "date"
            },
            "used_in_unique_key": True,
            "unique_key_priority": 3,
            "used_in_grouping": True,
            "icon": "📅",
            "is_system": True
        },
        {
            "name": "customer",
            "label_fa": "مشتری",
            "label_en": "Customer",
            "description": "نام یا کد مشتری",
            "category": "business",
            "properties": {
                "is_searchable": True,
                "is_filterable": True,
                "is_groupable": True,
                "data_type_hint": "text"
            },
            "used_in_unique_key": True,
            "unique_key_priority": 5,
            "used_in_grouping": True,
            "icon": "👤",
            "is_system": True
        },
        {
            "name": "rate",
            "label_fa": "نرخ",
            "label_en": "Rate",
            "description": "نرخ فروش یا خرید",
            "category": "business",
            "properties": {
                "is_aggregatable": True,
                "data_type_hint": "decimal",
                "format_pattern": "###,###.####"
            },
            "used_in_unique_key": True,
            "unique_key_priority": 6,
            "used_in_grouping": True,
            "icon": "💱",
            "is_system": True
        },
        
        # نقش‌های اضافی (Custom)
        {
            "name": "serial",
            "label_fa": "سریال",
            "label_en": "Serial Number",
            "description": "سریال محصول یا کارت هدیه",
            "category": "custom",
            "properties": {
                "is_searchable": True,
                "data_type_hint": "text"
            },
            "icon": "#️⃣",
            "is_system": False
        },
        {
            "name": "email",
            "label_fa": "ایمیل",
            "label_en": "Email",
            "description": "آدرس ایمیل اکانت",
            "category": "custom",
            "properties": {
                "is_searchable": True,
                "data_type_hint": "email"
            },
            "icon": "📧",
            "is_system": False
        },
        {
            "name": "password",
            "label_fa": "پسورد",
            "label_en": "Password",
            "description": "رمز عبور اکانت",
            "category": "custom",
            "properties": {
                "data_type_hint": "text"
            },
            "icon": "🔐",
            "is_system": False
        },
        {
            "name": "platform",
            "label_fa": "پلتفرم",
            "label_en": "Platform",
            "description": "نام پلتفرم (PUBG، Razer، PSN، ...)",
            "category": "business",
            "properties": {
                "is_filterable": True,
                "is_groupable": True,
                "data_type_hint": "text"
            },
            "icon": "🎮",
            "is_system": False
        },
        {
            "name": "amount",
            "label_fa": "مبلغ",
            "label_en": "Amount",
            "description": "مبلغ نهایی (تومان، تتر، ...)",
            "category": "business",
            "properties": {
                "is_aggregatable": True,
                "data_type_hint": "decimal",
                "format_pattern": "###,###.##"
            },
            "icon": "💵",
            "is_system": False
        },
        {
            "name": "description",
            "label_fa": "توضیحات",
            "label_en": "Description",
            "description": "توضیحات تکمیلی",
            "category": "custom",
            "properties": {
                "is_searchable": True,
                "data_type_hint": "text"
            },
            "icon": "📝",
            "is_system": False
        },
        {
            "name": "extracted",
            "label_fa": "استخراج شده",
            "label_en": "Extracted",
            "description": "وضعیت استخراج (تیک سبز)",
            "category": "technical",
            "properties": {
                "is_filterable": True,
                "data_type_hint": "boolean"
            },
            "icon": "✅",
            "is_system": True
        },
    ]
    
    for role_data in default_roles:
        existing = db_session.query(FieldRole).filter_by(name=role_data["name"]).first()
        if not existing:
            role = FieldRole(**role_data)
            db_session.add(role)
    
    db_session.commit()
    print(f"✅ {len(default_roles)} نقش پیش‌فرض ایجاد شد")


def init_default_presets(db_session):
    """
    ایجاد پیش‌فرض‌های نقش برای شروع سریع
    """
    presets = [
        {
            "name": "gift_card_basic",
            "title_fa": "کارت هدیه ساده",
            "description": "نقش‌های پایه برای کارت‌های هدیه",
            "category": "gift_cards",
            "suggested_roles": [
                {"name": "code", "label_fa": "کد کارت", "role": "identifier"},
                {"name": "value", "label_fa": "مقدار", "role": "value"},
                {"name": "serial", "label_fa": "سریال", "role": "serial"},
                {"name": "date", "label_fa": "تاریخ", "role": "date"},
            ]
        },
        {
            "name": "gaming_account",
            "title_fa": "اکانت بازی",
            "description": "نقش‌های مربوط به اکانت‌های بازی (PUBG، Free Fire، ...)",
            "category": "gaming",
            "suggested_roles": [
                {"name": "account_code", "label_fa": "کد اکانت", "role": "identifier"},
                {"name": "email", "label_fa": "ایمیل", "role": "email"},
                {"name": "password", "label_fa": "پسورد", "role": "password"},
                {"name": "uc_balance", "label_fa": "موجودی UC", "role": "value"},
                {"name": "platform", "label_fa": "پلتفرم", "role": "platform"},
            ]
        },
        {
            "name": "sales_transaction",
            "title_fa": "تراکنش فروش",
            "description": "نقش‌های مربوط به فروش",
            "category": "business",
            "suggested_roles": [
                {"name": "tr_id", "label_fa": "شماره تراکنش", "role": "transaction_id"},
                {"name": "customer", "label_fa": "مشتری", "role": "customer"},
                {"name": "quantity", "label_fa": "مقدار", "role": "value"},
                {"name": "rate", "label_fa": "نرخ", "role": "rate"},
                {"name": "amount", "label_fa": "مبلغ", "role": "amount"},
                {"name": "date", "label_fa": "تاریخ", "role": "date"},
            ]
        },
    ]
    
    for preset_data in presets:
        existing = db_session.query(RolePreset).filter_by(name=preset_data["name"]).first()
        if not existing:
            preset = RolePreset(**preset_data)
            db_session.add(preset)
    
    db_session.commit()
    print(f"✅ {len(presets)} پیش‌فرض نقش ایجاد شد")
