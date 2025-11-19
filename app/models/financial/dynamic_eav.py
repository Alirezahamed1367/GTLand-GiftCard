"""
EAV (Entity-Attribute-Value) Database Design
سیستم کاملاً داینامیک برای ذخیره هر نوع داده‌ای

این معماری اجازه می‌دهد:
- فیلدهای نامحدود برای هر entity
- نوع داده‌های متنوع (text, number, date, formula, json)
- میلیون‌ها رکورد با کارایی بالا
- تغییر ساختار بدون migration
"""
from sqlalchemy import (
    Column, Integer, String, Text, TIMESTAMP, DECIMAL, 
    Boolean, Date, ForeignKey, Index, JSON, BigInteger
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from decimal import Decimal
from .base_financial import FinancialBase


# ═══════════════════════════════════════════════════════════
#                     LAYER 1: DATA SOURCES
# ═══════════════════════════════════════════════════════════

class DataSource(FinancialBase):
    """
    منبع داده (Google Sheet, Excel, CSV, API, Database)
    هر sheet یک DataSource است
    """
    __tablename__ = 'data_sources'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    source_type = Column(String(50), nullable=False)  # google_sheet, excel, csv, api, db
    
    # ارتباط با Phase 1
    sheet_config_id = Column(Integer, nullable=True, index=True)  # از gt_land.db
    
    # تنظیمات
    connection_info = Column(JSON, comment='URL, credentials, etc.')
    is_active = Column(Boolean, default=True)
    
    # آمار
    total_records = Column(BigInteger, default=0)
    last_sync_at = Column(TIMESTAMP)
    
    # تاریخ‌ها
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # روابط
    entities = relationship("DataEntity", back_populates="source", cascade="all, delete-orphan")
    fields = relationship(
        "FieldDefinition",
        back_populates="source",
        foreign_keys="[FieldDefinition.source_id]",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index('idx_datasource_active', 'is_active'),
        Index('idx_datasource_type', 'source_type'),
    )


# ═══════════════════════════════════════════════════════════
#                  LAYER 2: FIELD DEFINITIONS
# ═══════════════════════════════════════════════════════════

class FieldDefinition(FinancialBase):
    """
    تعریف فیلد - کاربر مشخص می‌کند این فیلد چیست
    مثلاً: "نام مشتری" - نوع: متن - ضروری: بله
    """
    __tablename__ = 'field_definitions'
    
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey('data_sources.id', ondelete='CASCADE'), nullable=False)
    
    # مشخصات فیلد
    field_name = Column(String(255), nullable=False, comment='نام فیلد (کاربر تعیین می‌کند)')
    field_display_name = Column(String(255), comment='نام نمایشی فارسی')
    
    # نوع داده
    data_type = Column(String(50), nullable=False, comment='''
        text, number, decimal, date, datetime, boolean, 
        formula, lookup, choice, json, file
    ''')
    
    # نقش فیلد در سیستم مالی
    field_role = Column(String(100), comment='''
        label (شناسه آکانت)
        customer (مشتری)
        supplier (تامین‌کننده)
        amount (مبلغ)
        rate (نرخ)
        quantity (تعداد)
        date (تاریخ)
        status (وضعیت)
        description (توضیحات)
        custom (سفارشی)
    ''')
    
    # ویژگی‌ها
    is_required = Column(Boolean, default=False)
    is_unique = Column(Boolean, default=False)
    is_indexed = Column(Boolean, default=False)
    is_computed = Column(Boolean, default=False, comment='آیا محاسباتی است؟')
    
    # اعتبارسنجی
    validation_rules = Column(JSON, comment='''
    {
        "min": 0,
        "max": 1000000,
        "pattern": "^[A-Z][0-9]+$",
        "choices": ["pending", "completed", "cancelled"]
    }
    ''')
    
    # فرمول (برای فیلدهای محاسباتی)
    formula = Column(Text, comment='فرمول محاسباتی')
    formula_ast = Column(JSON, comment='درخت فرمول برای پردازش سریع')
    
    # Lookup (برای فیلدهای مرجع)
    lookup_source_id = Column(Integer, ForeignKey('data_sources.id'), nullable=True)
    lookup_field_id = Column(Integer, ForeignKey('field_definitions.id'), nullable=True)
    
    # پیش‌فرض
    default_value = Column(Text)
    
    # ترتیب نمایش
    display_order = Column(Integer, default=0)
    
    # تاریخ‌ها
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # روابط
    source = relationship("DataSource", back_populates="fields", foreign_keys=[source_id])
    lookup_source = relationship("DataSource", foreign_keys=[lookup_source_id], uselist=False)
    lookup_field = relationship("FieldDefinition", foreign_keys=[lookup_field_id], remote_side=[id], uselist=False)
    values = relationship("FieldValue", back_populates="field", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_field_source', 'source_id'),
        Index('idx_field_role', 'field_role'),
        Index('idx_field_type', 'data_type'),
    )


# ═══════════════════════════════════════════════════════════
#                   LAYER 3: DATA ENTITIES
# ═══════════════════════════════════════════════════════════

class DataEntity(FinancialBase):
    """
    یک رکورد/ردیف داده
    مثلاً: یک معامله، یک مشتری، یک آکانت
    """
    __tablename__ = 'data_entities'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey('data_sources.id', ondelete='CASCADE'), nullable=False)
    
    # شناسه یکتا در منبع اصلی
    source_entity_id = Column(String(500), comment='ID رکورد در منبع اصلی (sales_data.id)')
    
    # نوع entity (اختیاری - برای دسته‌بندی)
    entity_type = Column(String(100), comment='transaction, account, customer, ...')
    
    # تاریخ‌ها
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # روابط
    source = relationship("DataSource", back_populates="entities")
    field_values = relationship(
        "FieldValue",
        back_populates="entity",
        foreign_keys="[FieldValue.entity_id]",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index('idx_entity_source', 'source_id'),
        Index('idx_entity_type', 'entity_type'),
        Index('idx_entity_source_id', 'source_entity_id'),
        Index('idx_entity_created', 'created_at'),
    )


# ═══════════════════════════════════════════════════════════
#                  LAYER 4: FIELD VALUES (EAV)
# ═══════════════════════════════════════════════════════════

class FieldValue(FinancialBase):
    """
    مقدار یک فیلد برای یک entity
    قلب سیستم EAV - اینجا همه داده‌ها ذخیره می‌شوند
    
    مثال:
    entity_id=1001, field_id=5, value_text="Ali"
    entity_id=1001, field_id=6, value_decimal=1500.50
    entity_id=1001, field_id=7, value_date="2025-11-13"
    """
    __tablename__ = 'field_values'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_id = Column(Integer, ForeignKey('data_entities.id', ondelete='CASCADE'), nullable=False)
    field_id = Column(Integer, ForeignKey('field_definitions.id', ondelete='CASCADE'), nullable=False)
    
    # مقادیر (بر اساس نوع داده، یکی پر می‌شود)
    value_text = Column(Text)
    value_number = Column(BigInteger)
    value_decimal = Column(DECIMAL(20, 4))
    value_date = Column(Date)
    value_datetime = Column(TIMESTAMP)
    value_boolean = Column(Boolean)
    value_json = Column(JSON)
    
    # برای فیلدهای lookup
    value_entity_id = Column(Integer, ForeignKey('data_entities.id'), nullable=True)
    
    # تاریخ‌ها
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # روابط
    entity = relationship("DataEntity", back_populates="field_values", foreign_keys=[entity_id])
    field = relationship("FieldDefinition", back_populates="values")
    lookup_entity = relationship("DataEntity", foreign_keys=[value_entity_id], uselist=False)
    
    __table_args__ = (
        # ایندکس‌های کلیدی برای کارایی
        Index('idx_fieldvalue_entity', 'entity_id'),
        Index('idx_fieldvalue_field', 'field_id'),
        Index('idx_fieldvalue_entity_field', 'entity_id', 'field_id', unique=True),
        
        # ایندکس‌های جستجو
        Index('idx_fieldvalue_text', 'value_text'),  # برای LIKE queries
        Index('idx_fieldvalue_number', 'value_number'),
        Index('idx_fieldvalue_decimal', 'value_decimal'),
        Index('idx_fieldvalue_date', 'value_date'),
        Index('idx_fieldvalue_boolean', 'value_boolean'),
    )


# ═══════════════════════════════════════════════════════════
#                  LAYER 5: FORMULAS & CALCULATIONS
# ═══════════════════════════════════════════════════════════

class Formula(FinancialBase):
    """
    فرمول‌های محاسباتی - کاربر می‌سازد
    مثل Excel: =SUM(Amount) * Rate - Cost
    """
    __tablename__ = 'formulas'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # فرمول (متنی و AST)
    formula_text = Column(Text, nullable=False, comment='=SUM(field1) + field2 * 1.5')
    formula_ast = Column(JSON, comment='درخت نحوی برای پردازش')
    
    # متغیرها
    variables = Column(JSON, comment='''
    {
        "field1": "amount",
        "field2": "rate",
        "constant1": 1.5
    }
    ''')
    
    # نوع خروجی
    result_type = Column(String(50), comment='number, decimal, text, boolean')
    
    # تاریخ‌ها
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


# ═══════════════════════════════════════════════════════════
#                    LAYER 6: REPORTS & VIEWS
# ═══════════════════════════════════════════════════════════

class ReportDefinition(FinancialBase):
    """
    تعریف گزارش - کاربر می‌سازد
    """
    __tablename__ = 'report_definitions'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # نوع گزارش
    report_type = Column(String(100), comment='Table, Summary, Chart, etc.')
    
    # منبع اصلی (اگر از یک source استفاده می‌کند)
    primary_source_id = Column(Integer, comment='Main source ID')
    
    # فیلدهای انتخاب شده
    field_mappings = Column(JSON, comment='''
    {
        "selected_fields": [1, 2, 3],
        "report_config": {...}
    }
    ''')
    
    # Query
    query_config = Column(JSON, comment='''
    {
        "sources": [1, 2],
        "fields": [5, 6, 7],
        "filters": [
            {"field": 5, "operator": ">=", "value": 1000}
        ],
        "group_by": [5],
        "order_by": [{"field": 6, "direction": "desc"}],
        "aggregations": [
            {"field": 7, "function": "sum", "alias": "total"}
        ]
    }
    ''')
    
    # فیلترها و Aggregations
    filters = Column(JSON, default={})
    aggregations = Column(JSON, default={})
    
    # نمایش
    visualization = Column(JSON, comment='''
    {
        "type": "table|chart|pivot",
        "chart_type": "bar|line|pie",
        "columns": [...],
        "rows": [...]
    }
    ''')
    
    # دسترسی و وضعیت
    is_public = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # تاریخ‌ها
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


# ═══════════════════════════════════════════════════════════
#                  HELPER: MATERIALIZED VIEWS
# ═══════════════════════════════════════════════════════════

class MaterializedView(FinancialBase):
    """
    نماهای از پیش محاسبه شده برای کارایی
    برای گزارش‌های پرکاربرد
    """
    __tablename__ = 'materialized_views'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    report_id = Column(Integer, ForeignKey('report_definitions.id'), nullable=True)
    
    # داده‌های cache شده
    cached_data = Column(JSON)
    
    # تنظیمات refresh
    auto_refresh = Column(Boolean, default=True)
    refresh_interval_minutes = Column(Integer, default=60)
    last_refreshed_at = Column(TIMESTAMP)
    
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
