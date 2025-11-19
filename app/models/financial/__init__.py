"""
مدل‌های دیتابیس سیستم مالی GT-Land - نسخه جدید
Financial Database Models - Configuration-Driven System

این پکیج شامل تمام مدل‌های مربوط به سیستم مالی است
"""

from .base_financial import (
    FinancialBase,
    financial_engine,
    FinancialSessionLocal,
    get_financial_db,
    get_financial_session,
    init_financial_db
)

# Configuration Models (NEW)
from .configurations import (
    UnitType,
    Department,
    Platform,
    Region,
    TransactionType,
    SKUPattern,
    CustomerCodePattern,
    SheetTypeDefinition,
    SheetColumnMapping,
    CurrencyRate,
    CalculationFormula,
    init_default_configurations
)

# Core Financial Models (NEW)
from .core_models import (
    AccountInventory,
    Purchase,
    Customer,
    Sale,
    SilverBonus,
    CustomerLedger,
    CustomerPayment,
    AccountProfitLoss
)

# EAV Models (OLD - Still Active)
from .dynamic_eav import (
    DataSource,
    FieldDefinition,
    DataEntity,
    FieldValue,
    Formula,
    ReportDefinition,
    MaterializedView
)

# Custom Fields (NEW - User-Defined Fields System)
from .custom_fields import (
    CustomField,
    FieldMapping,
    TransactionSchema
)

# Field Roles (NEW - User-Defined Roles System)
from .field_roles import (
    FieldRole,
    RolePreset,
    init_default_roles,
    init_default_presets
)

# Raw Data (Stage 1)
from .raw_data import (
    RawData,
    ImportBatch
)

# Processed Data (Stage 2)
from .processed_data import (
    ProductV2,
    PurchaseV2,
    CustomerV2,
    SaleV2,
    BonusV2
)

__all__ = [
    # Base
    'FinancialBase',
    'financial_engine',
    'FinancialSessionLocal',
    'get_financial_db',
    'get_financial_session',
    'init_financial_db',
    
    # Configuration Models
    'UnitType',
    'Department',
    'Platform',
    'Region',
    'TransactionType',
    'SKUPattern',
    'CustomerCodePattern',
    'SheetTypeDefinition',
    'SheetColumnMapping',
    'CurrencyRate',
    'CalculationFormula',
    'init_default_configurations',
    
    # Core Financial Models
    'AccountInventory',
    'Purchase',
    'Customer',
    'Sale',
    'SilverBonus',
    'CustomerLedger',
    'CustomerPayment',
    'AccountProfitLoss',
    
    # EAV Models (Dynamic BI Platform)
    'DataSource',
    'FieldDefinition',
    'DataEntity',
    'FieldValue',
    'Formula',
    'ReportDefinition',
    'MaterializedView',
    
    # Custom Fields (User-Defined)
    'CustomField',
    'FieldMapping',
    'TransactionSchema',
    
    # Field Roles (User-Defined)
    'FieldRole',
    'RolePreset',
    'init_default_roles',
    'init_default_presets',
    
    # Raw Data (Stage 1)
    'RawData',
    'ImportBatch',
    
    # Processed Data (Stage 2)
    'ProductV2',
    'PurchaseV2',
    'CustomerV2',
    'SaleV2',
    'BonusV2',
]
