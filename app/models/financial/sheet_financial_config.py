"""
Sheet Financial Config - تنظیمات مالی هر شیت
کاربر مشخص می‌کند هر sheet چه نوع داده‌ای دارد و ستون‌ها به چه فیلدهایی map می‌شوند
"""
from sqlalchemy import Column, Integer, String, Boolean, Text, TIMESTAMP, JSON, ForeignKey
from sqlalchemy.sql import func
from .base_financial import FinancialBase


class SheetFinancialConfig(FinancialBase):
    """
    تنظیمات مالی برای هر Google Sheet
    کاربر تعیین می‌کند این sheet چه نوع داده‌ای دارد
    """
    __tablename__ = 'sheet_financial_configs'
    
    id = Column(Integer, primary_key=True, index=True)
    
    # ارتباط با sheet_config در دیتابیس اصلی
    sheet_config_id = Column(Integer, nullable=False, unique=True, index=True, 
                            comment='شناسه sheet_config از gt_land.db')
    sheet_name = Column(String(255), nullable=False, comment='نام sheet (برای نمایش)')
    
    # نوع داده
    data_type = Column(String(50), nullable=False, 
                      comment='نوع داده: purchase (خرید), sale (فروش), payment (تسویه), mixed (ترکیبی), other (سایر)')
    
    # وضعیت
    is_active = Column(Boolean, default=True, comment='فعال برای تبدیل به سیستم مالی')
    
    # Mapping فیلدها
    field_mappings = Column(JSON, nullable=False, comment='''
    نقشه فیلدها - کاربر مشخص می‌کند هر ستون sheet به چه فیلد مالی map میشه:
    {
        "sale": {
            "label": "Label",              # ستونی که شناسه آکانت داره
            "customer": "Customer",         # ستون نام مشتری
            "rate": "Rate For Sale",        # ستون نرخ فروش
            "price": "Final Price Sale",    # ستون قیمت نهایی
            "amount": "Amount",             # ستون مقدار فروخته شده
            "date": "Sold Date",            # ستون تاریخ
            "seller": "Seller Name"         # ستون فروشنده
        },
        "purchase": {
            "label": "Account ID",
            "supplier": "Supplier",
            "purchase_price": "Buy Price",
            "initial_balance": "Initial Amount",
            "date": "Purchase Date"
        },
        "payment": {
            "customer": "Customer Name",
            "amount": "Payment Amount",
            "currency": "Currency",
            "date": "Payment Date",
            "method": "Payment Method"
        }
    }
    ''')
    
    # تنظیمات پیشرفته
    department_code = Column(String(20), nullable=True, 
                            comment='کد دپارتمان (TOPUP, GIFTCARD) - null = تشخیص خودکار')
    
    product_type = Column(String(100), nullable=True,
                         comment='نوع محصول (PUBG, COD, RG, ...) - null = تشخیص خودکار')
    
    auto_create_accounts = Column(Boolean, default=True, 
                                 comment='ساخت خودکار آکانت‌های جدید')
    
    auto_create_customers = Column(Boolean, default=True,
                                  comment='ساخت خودکار مشتریان جدید')
    
    # فیلترها
    row_filters = Column(JSON, nullable=True, comment='''
    فیلترهای اعمالی برای انتخاب رکوردهای قابل تبدیل:
    {
        "status_column": "Status",
        "status_values": ["Completed", "Paid"],
        "exclude_test": true
    }
    ''')
    
    # آمار
    total_records_converted = Column(Integer, default=0, comment='تعداد کل رکوردهای تبدیل شده')
    last_conversion_at = Column(TIMESTAMP, nullable=True, comment='آخرین زمان تبدیل')
    
    # تاریخ‌ها
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    notes = Column(Text, nullable=True, comment='یادداشت‌های کاربر')
    
    def __repr__(self):
        return f"<SheetFinancialConfig(sheet='{self.sheet_name}', type='{self.data_type}')>"
    
    def to_dict(self):
        """تبدیل به دیکشنری"""
        return {
            'id': self.id,
            'sheet_config_id': self.sheet_config_id,
            'sheet_name': self.sheet_name,
            'data_type': self.data_type,
            'is_active': self.is_active,
            'field_mappings': self.field_mappings,
            'department_code': self.department_code,
            'product_type': self.product_type,
            'auto_create_accounts': self.auto_create_accounts,
            'auto_create_customers': self.auto_create_customers,
            'row_filters': self.row_filters,
            'total_records_converted': self.total_records_converted,
            'last_conversion_at': str(self.last_conversion_at) if self.last_conversion_at else None,
            'notes': self.notes
        }
    
    def get_field_mapping_for_type(self, data_type: str = None) -> dict:
        """دریافت mapping فیلدها برای نوع مشخص"""
        dt = data_type or self.data_type
        if self.field_mappings and dt in self.field_mappings:
            return self.field_mappings[dt]
        return {}
    
    def validate_mapping(self) -> tuple[bool, list]:
        """اعتبارسنجی mapping - برمی‌گرداند (is_valid, errors)"""
        errors = []
        
        if not self.field_mappings:
            errors.append("هیچ mapping تعریف نشده")
            return False, errors
        
        # بررسی فیلدهای ضروری بر اساس نوع
        required_fields = {
            'sale': ['label', 'customer', 'rate', 'price'],
            'purchase': ['label', 'supplier', 'purchase_price'],
            'payment': ['customer', 'amount']
        }
        
        if self.data_type in required_fields:
            mapping = self.get_field_mapping_for_type()
            for field in required_fields[self.data_type]:
                if not mapping.get(field):
                    errors.append(f"فیلد ضروری '{field}' برای نوع '{self.data_type}' تعریف نشده")
        
        return len(errors) == 0, errors
