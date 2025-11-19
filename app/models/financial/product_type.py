"""
مدل نوع محصول - ProductType Model
"""
from sqlalchemy import Column, Integer, String, Boolean, Text, TIMESTAMP, DECIMAL, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from decimal import Decimal
from .base_financial import FinancialBase


class ProductType(FinancialBase):
    """
    جدول انواع محصولات
    """
    __tablename__ = 'product_types'
    
    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey('departments.id', ondelete='CASCADE'), nullable=False)
    
    # شناسایی
    code = Column(String(50), unique=True, nullable=False, comment='کد محصول (COD, PUBG, PS5, ...)')
    name = Column(String(255), nullable=False, comment='نام محصول')
    category = Column(String(100), nullable=True, comment='دسته‌بندی (game, console, gift_card, ...)')
    
    # واحدها
    units = Column(JSON, nullable=True, comment='لیست واحدها (["CP", "UC", "USD"])')
    default_unit = Column(String(20), nullable=True, comment='واحد پیش‌فرض')
    
    # تنظیمات قیمت‌گذاری
    default_sale_rate = Column(DECIMAL(10, 4), nullable=True, comment='ریت فروش پیش‌فرض')
    min_sale_rate = Column(DECIMAL(10, 4), nullable=True, comment='حداقل ریت')
    max_sale_rate = Column(DECIMAL(10, 4), nullable=True, comment='حداکثر ریت')
    
    # وضعیت
    is_active = Column(Boolean, default=True, comment='فعال/غیرفعال')
    
    # تاریخ
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    notes = Column(Text, nullable=True)
    
    # روابط
    department = relationship("Department", back_populates="product_types")
    
    __table_args__ = (
        Index('idx_product_type_code', 'code'),
        Index('idx_product_type_department', 'department_id'),
    )
    
    def __repr__(self):
        return f"<ProductType(id={self.id}, code='{self.code}', name='{self.name}')>"
