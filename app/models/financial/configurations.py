"""
Configuration Models - تمام تنظیمات سیستم مالی
این ماژول شامل تمام تعاریف پایه است که کاربر مدیریت می‌کند
"""
from sqlalchemy import (
    Column, Integer, String, Text, TIMESTAMP, DECIMAL, 
    Boolean, Date, ForeignKey, Index, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base_financial import FinancialBase


# ═══════════════════════════════════════════════════════════
#                   1. UNIT TYPES (واحدهای اندازه‌گیری)
# ═══════════════════════════════════════════════════════════

class UnitType(FinancialBase):
    """
    تعریف واحدهای اندازه‌گیری
    مثال: CP (سی پی کالاف), GOLD (گلد), SILVER (سیلور)
    """
    __tablename__ = 'unit_types'
    
    unit_id = Column(Integer, primary_key=True, autoincrement=True)
    unit_code = Column(String(20), unique=True, nullable=False, index=True, comment='کد یکتا')
    unit_name_fa = Column(String(100), nullable=False, comment='نام فارسی')
    unit_name_en = Column(String(100), comment='نام انگلیسی')
    unit_symbol = Column(String(10), comment='نماد (CP, $, 🪙)')
    unit_category = Column(String(50), comment='currency, game_item, bonus')
    is_active = Column(Boolean, default=True, index=True)
    display_order = Column(Integer, default=0, comment='ترتیب نمایش')
    notes = Column(Text, comment='یادداشت')
    
    # تاریخ‌ها
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # روابط
    accounts = relationship("AccountInventory", back_populates="unit_type")
    
    __table_args__ = (
        Index('idx_unit_active', 'is_active'),
        Index('idx_unit_category', 'unit_category'),
    )
    
    def __repr__(self):
        return f"<UnitType({self.unit_code}: {self.unit_name_fa})>"


# ═══════════════════════════════════════════════════════════
#                   2. DEPARTMENTS (دپارتمان‌ها)
# ═══════════════════════════════════════════════════════════

class Department(FinancialBase):
    """
    تعریف دپارتمان‌ها
    مثال: Gift-Card, Top-up
    """
    __tablename__ = 'departments'
    
    department_id = Column(Integer, primary_key=True, autoincrement=True)
    department_code = Column(String(20), unique=True, nullable=False, index=True, comment='کد یکتا')
    department_name_fa = Column(String(100), nullable=False, comment='نام فارسی')
    department_name_en = Column(String(100), comment='نام انگلیسی')
    parent_department_id = Column(Integer, ForeignKey('departments.department_id'), comment='دپارتمان پدر')
    is_active = Column(Boolean, default=True, index=True)
    notes = Column(Text)
    
    # تاریخ‌ها
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # روابط
    parent = relationship("Department", remote_side=[department_id], backref="children")
    accounts = relationship("AccountInventory", back_populates="department")
    sku_patterns = relationship("SKUPattern", back_populates="department")
    
    def __repr__(self):
        return f"<Department({self.department_code}: {self.department_name_fa})>"


# ═══════════════════════════════════════════════════════════
#                   3. PLATFORMS (پلتفرم‌ها)
# ═══════════════════════════════════════════════════════════

class Platform(FinancialBase):
    """
    تعریف پلتفرم‌ها
    مثال: COD Mobile, PUBG, PlayStation, Xbox
    """
    __tablename__ = 'platforms'
    
    platform_id = Column(Integer, primary_key=True, autoincrement=True)
    platform_code = Column(String(50), unique=True, nullable=False, index=True)
    platform_name_fa = Column(String(100), nullable=False)
    platform_name_en = Column(String(100))
    platform_category = Column(String(50), comment='mobile_game, console, pc, service')
    is_active = Column(Boolean, default=True, index=True)
    notes = Column(Text)
    
    # تاریخ‌ها
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # روابط
    accounts = relationship("AccountInventory", back_populates="platform")
    sales = relationship("Sale", back_populates="platform")
    silver_bonuses = relationship("SilverBonus", back_populates="platform")
    
    __table_args__ = (
        Index('idx_platform_category', 'platform_category'),
    )
    
    def __repr__(self):
        return f"<Platform({self.platform_code}: {self.platform_name_fa})>"


# ═══════════════════════════════════════════════════════════
#                   4. REGIONS (ریجن‌ها)
# ═══════════════════════════════════════════════════════════

class Region(FinancialBase):
    """
    تعریف ریجن‌ها
    مثال: USA, EU, Sweden, Turkey
    """
    __tablename__ = 'regions'
    
    region_id = Column(Integer, primary_key=True, autoincrement=True)
    region_code = Column(String(20), nullable=False, index=True)
    region_name_fa = Column(String(100), nullable=False)
    region_name_en = Column(String(100))
    is_active = Column(Boolean, default=True, index=True)
    notes = Column(Text)
    
    # تاریخ‌ها
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # روابط
    accounts = relationship("AccountInventory", back_populates="region")
    
    def __repr__(self):
        return f"<Region({self.region_code}: {self.region_name_fa})>"


# ═══════════════════════════════════════════════════════════
#                   5. TRANSACTION TYPES (نوع معاملات)
# ═══════════════════════════════════════════════════════════

class TransactionType(FinancialBase):
    """
    تعریف نوع معاملات
    مثال: خرید، فروش، بونوس سیلور، تعدیل
    """
    __tablename__ = 'transaction_types'
    
    type_id = Column(Integer, primary_key=True, autoincrement=True)
    type_code = Column(String(50), unique=True, nullable=False, index=True)
    type_name_fa = Column(String(100), nullable=False)
    type_name_en = Column(String(100))
    type_category = Column(String(50), comment='inbound, outbound, adjustment')
    affects_inventory = Column(String(20), comment='increase, decrease, none')
    is_active = Column(Boolean, default=True, index=True)
    notes = Column(Text)
    
    # تاریخ‌ها
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # روابط
    sheet_type_definitions = relationship("SheetTypeDefinition", back_populates="transaction_type")
    
    def __repr__(self):
        return f"<TransactionType({self.type_code}: {self.type_name_fa})>"


# ═══════════════════════════════════════════════════════════
#                   6. SKU PATTERNS (الگوی کد کالا)
# ═══════════════════════════════════════════════════════════

class SKUPattern(FinancialBase):
    """
    تعریف الگوی کد کالا
    مثال: GC-{YEAR}-{SEQ:5} → GC-2025-00001
    """
    __tablename__ = 'sku_patterns'
    
    pattern_id = Column(Integer, primary_key=True, autoincrement=True)
    pattern_name = Column(String(100), nullable=False, comment='نام الگو')
    pattern_format = Column(String(255), nullable=False, comment='فرمت: GC-{YEAR}-{SEQ:5}')
    pattern_example = Column(String(100), comment='مثال: GC-2025-00001')
    department_id = Column(Integer, ForeignKey('departments.department_id'), comment='دپارتمان')
    current_sequence = Column(Integer, default=0, comment='شماره فعلی')
    is_active = Column(Boolean, default=True, index=True)
    notes = Column(Text, comment='''
    متغیرهای قابل استفاده:
    {YEAR} - سال جاری
    {MONTH} - ماه (01-12)
    {DAY} - روز (01-31)
    {SEQ:n} - شماره ترتیبی با n رقم
    {DEPT} - کد دپارتمان
    {RANDOM:n} - عدد تصادفی n رقمی
    ''')
    
    # تاریخ‌ها
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # روابط
    department = relationship("Department", back_populates="sku_patterns")
    
    def generate_code(self):
        """تولید کد جدید بر اساس الگو"""
        import re
        from datetime import datetime
        import random
        
        code = self.pattern_format
        
        # جایگذاری متغیرها
        code = code.replace('{YEAR}', str(datetime.now().year))
        code = code.replace('{MONTH}', f"{datetime.now().month:02d}")
        code = code.replace('{DAY}', f"{datetime.now().day:02d}")
        
        if self.department:
            code = code.replace('{DEPT}', self.department.department_code)
        
        # SEQ با تعداد رقم مشخص
        seq_pattern = re.findall(r'\{SEQ:(\d+)\}', code)
        if seq_pattern:
            digits = int(seq_pattern[0])
            self.current_sequence += 1
            seq_value = str(self.current_sequence).zfill(digits)
            code = re.sub(r'\{SEQ:\d+\}', seq_value, code)
        
        # RANDOM با تعداد رقم مشخص
        random_pattern = re.findall(r'\{RANDOM:(\d+)\}', code)
        if random_pattern:
            digits = int(random_pattern[0])
            random_value = ''.join([str(random.randint(0, 9)) for _ in range(digits)])
            code = re.sub(r'\{RANDOM:\d+\}', random_value, code)
        
        return code
    
    def __repr__(self):
        return f"<SKUPattern({self.pattern_name}: {self.pattern_format})>"


# ═══════════════════════════════════════════════════════════
#                   7. CUSTOMER CODE PATTERNS (الگوی کد مشتری)
# ═══════════════════════════════════════════════════════════

class CustomerCodePattern(FinancialBase):
    """
    تعریف الگوی کد مشتری
    مثال: C-{SEQ:4} → C-0001
    """
    __tablename__ = 'customer_code_patterns'
    
    pattern_id = Column(Integer, primary_key=True, autoincrement=True)
    pattern_name = Column(String(100), nullable=False)
    pattern_format = Column(String(255), nullable=False)
    pattern_example = Column(String(100))
    current_sequence = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, index=True)
    notes = Column(Text)
    
    # تاریخ‌ها
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    def generate_code(self):
        """تولید کد مشتری جدید"""
        import re
        from datetime import datetime
        
        code = self.pattern_format
        
        code = code.replace('{YEAR}', str(datetime.now().year))
        code = code.replace('{MONTH}', f"{datetime.now().month:02d}")
        
        seq_pattern = re.findall(r'\{SEQ:(\d+)\}', code)
        if seq_pattern:
            digits = int(seq_pattern[0])
            self.current_sequence += 1
            seq_value = str(self.current_sequence).zfill(digits)
            code = re.sub(r'\{SEQ:\d+\}', seq_value, code)
        
        return code
    
    def __repr__(self):
        return f"<CustomerCodePattern({self.pattern_name}: {self.pattern_format})>"


# ═══════════════════════════════════════════════════════════
#                   8. SHEET TYPE DEFINITIONS (تعریف نوع شیت‌ها)
# ═══════════════════════════════════════════════════════════

class SheetTypeDefinition(FinancialBase):
    """
    تعریف نوع شیت‌ها و فیلدهای مورد نیاز
    """
    __tablename__ = 'sheet_type_definitions'
    
    type_def_id = Column(Integer, primary_key=True, autoincrement=True)
    type_code = Column(String(50), unique=True, nullable=False, index=True)
    type_name_fa = Column(String(100), nullable=False)
    type_name_en = Column(String(100))
    transaction_type_id = Column(Integer, ForeignKey('transaction_types.type_id'))
    
    # تعریف فیلدها
    required_fields = Column(JSON, comment='فیلدهای الزامی')
    optional_fields = Column(JSON, comment='فیلدهای اختیاری')
    default_mappings = Column(JSON, comment='نقشه پیش‌فرض فیلدها')
    
    is_active = Column(Boolean, default=True, index=True)
    notes = Column(Text)
    
    # تاریخ‌ها
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # روابط
    transaction_type = relationship("TransactionType", back_populates="sheet_type_definitions")
    column_mappings = relationship("SheetColumnMapping", back_populates="sheet_type_definition")
    
    def __repr__(self):
        return f"<SheetTypeDefinition({self.type_code}: {self.type_name_fa})>"


# ═══════════════════════════════════════════════════════════
#                   9. SHEET COLUMN MAPPINGS (نقشه ستون‌های شیت)
# ═══════════════════════════════════════════════════════════

class SheetColumnMapping(FinancialBase):
    """
    نقشه‌برداری ستون‌های شیت به فیلدهای دیتابیس
    کاربر مشخص می‌کند کدام ستون در شیت به کدام فیلد در سیستم متصل شود
    """
    __tablename__ = 'sheet_column_mappings'
    
    mapping_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # لینک به شیت از Phase 1
    sheet_config_id = Column(Integer, nullable=False, index=True, comment='از sheet_configs')
    
    # نوع شیت
    sheet_type_def_id = Column(Integer, ForeignKey('sheet_type_definitions.type_def_id'), nullable=False)
    
    # Mapping
    source_column_name = Column(String(255), nullable=False, comment='نام ستون در شیت')
    target_field_name = Column(String(100), nullable=False, comment='نام فیلد در دیتابیس')
    field_role = Column(String(50), comment='identifier, amount, customer, rate, date, ...')
    
    # اعتبارسنجی
    data_type = Column(String(50), comment='text, number, decimal, date, boolean')
    is_required = Column(Boolean, default=False)
    validation_rules = Column(JSON, comment='قوانین اعتبارسنجی')
    
    # ترتیب
    display_order = Column(Integer, default=0)
    
    # تاریخ‌ها
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # روابط
    sheet_type_definition = relationship("SheetTypeDefinition", back_populates="column_mappings")
    
    __table_args__ = (
        Index('idx_mapping_sheet', 'sheet_config_id'),
        Index('idx_mapping_type', 'sheet_type_def_id'),
        UniqueConstraint('sheet_config_id', 'source_column_name', name='uq_sheet_column'),
    )
    
    def __repr__(self):
        return f"<SheetColumnMapping({self.source_column_name} → {self.target_field_name})>"


# ═══════════════════════════════════════════════════════════
#                   10. CURRENCY RATES (نرخ ارز)
# ═══════════════════════════════════════════════════════════

class CurrencyRate(FinancialBase):
    """
    نرخ تبدیل ارزها
    مثال: USDT → IRT (تتر به تومان)
    """
    __tablename__ = 'currency_rates'
    
    rate_id = Column(Integer, primary_key=True, autoincrement=True)
    from_currency = Column(String(10), nullable=False, index=True, comment='USDT, USD, EUR')
    to_currency = Column(String(10), nullable=False, index=True, comment='IRT, IRR')
    rate = Column(DECIMAL(20, 2), nullable=False, comment='نرخ تبدیل')
    effective_date = Column(Date, nullable=False, index=True, comment='تاریخ اعمال')
    is_active = Column(Boolean, default=True, index=True)
    notes = Column(Text)
    
    # تاریخ‌ها
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_currency_pair', 'from_currency', 'to_currency'),
        Index('idx_currency_date', 'effective_date'),
    )
    
    def __repr__(self):
        return f"<CurrencyRate({self.from_currency}/{self.to_currency}: {self.rate})>"


# ═══════════════════════════════════════════════════════════
#                   11. CALCULATION FORMULAS (فرمول‌های محاسباتی)
# ═══════════════════════════════════════════════════════════

class CalculationFormula(FinancialBase):
    """
    فرمول‌های محاسباتی قابل تنظیم توسط کاربر
    مثال: سود فروش گلد = sale_price - (amount_consumed * purchase_rate / 100)
    """
    __tablename__ = 'calculation_formulas'
    
    formula_id = Column(Integer, primary_key=True, autoincrement=True)
    formula_name = Column(String(100), nullable=False, comment='نام فرمول')
    formula_code = Column(String(50), unique=True, nullable=False, index=True, comment='کد یکتا')
    formula_type = Column(String(50), comment='profit_gold, profit_silver, inventory, ...')
    formula_expression = Column(Text, nullable=False, comment='عبارت ریاضی')
    variables = Column(JSON, comment='متغیرهای مورد نیاز')
    result_field = Column(String(100), comment='فیلد ذخیره نتیجه')
    is_active = Column(Boolean, default=True, index=True)
    description = Column(Text, comment='توضیحات فارسی')
    
    # تاریخ‌ها
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<CalculationFormula({self.formula_code}: {self.formula_name})>"


# ═══════════════════════════════════════════════════════════
#                   HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════

def init_default_configurations(session):
    """
    ایجاد تنظیمات پیش‌فرض
    این تابع یکبار در راه‌اندازی اولیه اجرا می‌شود
    """
    
    # 1. واحدهای پیش‌فرض
    default_units = [
        UnitType(unit_code="GOLD", unit_name_fa="گلد (دلار)", unit_name_en="Gold (USD)", 
                 unit_symbol="$", unit_category="currency"),
        UnitType(unit_code="SILVER", unit_name_fa="سیلور (بونوس)", unit_name_en="Silver (Bonus)", 
                 unit_symbol="🪙", unit_category="bonus"),
        UnitType(unit_code="CP", unit_name_fa="سی پی کالاف", unit_name_en="COD Points", 
                 unit_symbol="CP", unit_category="game_item"),
    ]
    
    # 2. دپارتمان‌های پیش‌فرض
    default_departments = [
        Department(department_code="GC", department_name_fa="گیفت کارت", department_name_en="Gift Card"),
        Department(department_code="TU", department_name_fa="تاپ آپ", department_name_en="Top-up"),
    ]
    
    # 3. نوع معاملات پیش‌فرض
    default_transaction_types = [
        TransactionType(type_code="PURCHASE", type_name_fa="خرید آکانت", type_name_en="Purchase", 
                       type_category="inbound", affects_inventory="increase"),
        TransactionType(type_code="SALE", type_name_fa="فروش", type_name_en="Sale", 
                       type_category="outbound", affects_inventory="decrease"),
        TransactionType(type_code="SILVER_BONUS", type_name_fa="دریافت بونوس سیلور", type_name_en="Silver Bonus", 
                       type_category="inbound", affects_inventory="increase"),
        TransactionType(type_code="ADJUSTMENT", type_name_fa="تعدیل", type_name_en="Adjustment", 
                       type_category="adjustment", affects_inventory="none"),
    ]
    
    # اضافه کردن به دیتابیس
    try:
        for item in default_units + default_departments + default_transaction_types:
            session.merge(item)  # merge به جای add برای جلوگیری از تکراری
        session.commit()
        print("✅ تنظیمات پیش‌فرض ایجاد شد")
    except Exception as e:
        session.rollback()
        print(f"❌ خطا در ایجاد تنظیمات: {e}")
