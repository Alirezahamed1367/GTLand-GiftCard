"""
مدل داده‌های فروش
"""
from sqlalchemy import Column, Integer, String, Boolean, Text, TIMESTAMP, JSON, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class SalesData(Base):
    """
    جدول داده‌های استخراج شده از Google Sheets
    """
    __tablename__ = 'sales_data'
    
    # ستون‌های اصلی
    id = Column(Integer, primary_key=True, index=True)
    sheet_config_id = Column(
        Integer, 
        ForeignKey('sheet_configs.id', ondelete='CASCADE'),
        nullable=False,
        comment='شناسه تنظیمات شیت'
    )
    
    # اطلاعات ردیف
    row_number = Column(Integer, nullable=False, comment='شماره ردیف در شیت')
    unique_key = Column(String(500), unique=True, nullable=False, index=True, comment='کلید یکتا')
    
    # داده‌های اصلی
    data = Column(JSON, nullable=False, comment='داده‌های خام به صورت JSON')
    
    # وضعیت خروجی
    is_exported = Column(Boolean, default=False, index=True, comment='آیا خروجی گرفته شده؟')
    export_type = Column(String(50), nullable=True, comment='نوع خروجی (type1, type2, type3)')
    exported_at = Column(TIMESTAMP, nullable=True, comment='تاریخ خروجی')
    
    # وضعیت داده
    is_updated = Column(Boolean, default=False, comment='آیا بروزرسانی شده؟')
    update_count = Column(Integer, default=0, comment='تعداد دفعات بروزرسانی')
    
    # تاریخ‌ها
    extracted_at = Column(TIMESTAMP, server_default=func.now(), comment='تاریخ استخراج')
    updated_at = Column(
        TIMESTAMP, 
        server_default=func.now(), 
        onupdate=func.now(), 
        comment='تاریخ آخرین بروزرسانی'
    )
    
    # یادداشت‌ها
    notes = Column(Text, nullable=True, comment='یادداشت‌ها')
    
    # روابط
    sheet_config = relationship("SheetConfig", back_populates="sales_data")
    
    # ایندکس‌ها و محدودیت‌ها
    __table_args__ = (
        Index('idx_sales_data_sheet_config', 'sheet_config_id'),
        Index('idx_sales_data_exported', 'is_exported'),
        Index('idx_sales_data_export_type', 'export_type'),
        Index('idx_sales_data_extracted_at', 'extracted_at'),
        UniqueConstraint('sheet_config_id', 'row_number', name='uq_sheet_row'),
    )
    
    def __repr__(self):
        return f"<SalesData(id={self.id}, key='{self.unique_key[:20]}...', exported={self.is_exported})>"
    
    def to_dict(self, include_data=True):
        """تبدیل به دیکشنری"""
        result = {
            'id': self.id,
            'sheet_config_id': self.sheet_config_id,
            'row_number': self.row_number,
            'unique_key': self.unique_key,
            'is_exported': self.is_exported,
            'export_type': self.export_type,
            'exported_at': self.exported_at.isoformat() if self.exported_at else None,
            'is_updated': self.is_updated,
            'update_count': self.update_count,
            'extracted_at': self.extracted_at.isoformat() if self.extracted_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'notes': self.notes,
        }
        
        if include_data:
            result['data'] = self.data
        
        return result
