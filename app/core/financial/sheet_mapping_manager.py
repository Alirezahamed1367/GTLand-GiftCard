"""
مدیریت Field Mapping به تفکیک هر SheetConfig
Sheet-Specific Field Mapping Manager
"""
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from app.models.financial import FieldMapping, TargetField, DataType, get_financial_session
from app.models.sheet_config import SheetConfig
from app.core.database import db_manager


class SheetFieldMappingManager:
    """
    مدیریت Field Mapping های مخصوص هر SheetConfig
    
    هر SheetConfig (Buy, Sale1, Sale2) می‌تواند:
    - نقش‌های مخصوص خودش را داشته باشد
    - ستون‌های متفاوتی را Map کند
    - تنظیمات مستقل داشته باشد
    """
    
    def __init__(self):
        self.main_db: Session = db_manager.get_session()
        self.financial_db: Session = get_financial_session()
    
    def get_sheet_configs(self) -> List[SheetConfig]:
        """لیست تمام SheetConfig های فعال"""
        return self.main_db.query(SheetConfig).filter_by(is_active=True).all()
    
    def get_sheet_config_by_id(self, config_id: int) -> Optional[SheetConfig]:
        """دریافت یک SheetConfig خاص"""
        return self.main_db.query(SheetConfig).filter_by(id=config_id).first()
    
    def get_mappings_for_sheet(self, config_id: int) -> List[FieldMapping]:
        """
        دریافت تمام Field Mapping های یک SheetConfig
        """
        return self.financial_db.query(FieldMapping).filter_by(
            sheet_config_id=config_id
        ).all()
    
    def set_mapping_for_sheet(
        self,
        config_id: int,
        config_name: str,
        source_column: str,
        target_field: TargetField,
        data_type: DataType,
        is_required: bool = False,
        default_value: str = None
    ) -> FieldMapping:
        """
        تعیین یا بروزرسانی یک Field Mapping برای یک SheetConfig
        
        Args:
            config_id: ID SheetConfig
            config_name: نام SheetConfig (برای راحتی)
            source_column: نام ستون در شیت
            target_field: نقش (ACCOUNT_ID, GOLD_QUANTITY, ...)
            data_type: نوع داده (TEXT, DECIMAL, ...)
            is_required: آیا الزامی است؟
            default_value: مقدار پیش‌فرض
        """
        # بررسی: آیا این Mapping قبلاً برای این SheetConfig وجود دارد؟
        existing = self.financial_db.query(FieldMapping).filter_by(
            sheet_config_id=config_id,
            source_column=source_column
        ).first()
        
        if existing:
            # بروزرسانی
            existing.target_field = target_field
            existing.data_type = data_type
            existing.is_required = is_required
            existing.default_value = default_value
            existing.sheet_config_name = config_name
            self.financial_db.commit()
            return existing
        else:
            # ایجاد جدید
            mapping = FieldMapping(
                sheet_config_id=config_id,
                sheet_config_name=config_name,
                source_column=source_column,
                target_field=target_field,
                data_type=data_type,
                is_required=is_required,
                default_value=default_value
            )
            self.financial_db.add(mapping)
            self.financial_db.commit()
            return mapping
    
    def delete_mapping_for_sheet(self, config_id: int, source_column: str) -> bool:
        """حذف یک Field Mapping"""
        mapping = self.financial_db.query(FieldMapping).filter_by(
            sheet_config_id=config_id,
            source_column=source_column
        ).first()
        
        if mapping:
            self.financial_db.delete(mapping)
            self.financial_db.commit()
            return True
        return False
    
    def get_mapping_dict_for_sheet(self, config_id: int) -> Dict[str, TargetField]:
        """
        دریافت دیکشنری Mapping های یک SheetConfig
        
        Returns:
            {"Label": TargetField.ACCOUNT_ID, "GOLD": TargetField.GOLD_QUANTITY, ...}
        """
        mappings = self.get_mappings_for_sheet(config_id)
        return {m.source_column: m.target_field for m in mappings}
    
    def apply_preset_for_sheet(self, config_id: int, preset_name: str):
        """
        اعمال یک Preset از پیش تعریف شده برای یک SheetConfig
        
        Presets:
        - "Purchase": برای شیت‌های خرید
        - "Sale": برای شیت‌های فروش
        - "Bonus": برای شیت‌های بونوس
        """
        sheet_config = self.get_sheet_config_by_id(config_id)
        if not sheet_config:
            raise ValueError(f"SheetConfig با ID {config_id} یافت نشد")
        
        # حذف Mapping های قبلی
        self.financial_db.query(FieldMapping).filter_by(
            sheet_config_id=config_id
        ).delete()
        
        if preset_name == "Purchase":
            # نقش‌های پیش‌فرض برای شیت خرید
            presets = [
                ("Label", TargetField.ACCOUNT_ID, DataType.TEXT, True),
                ("EMAIL", TargetField.EMAIL, DataType.TEXT, False),
                ("Owner", TargetField.SUPPLIER, DataType.TEXT, False),
                ("GOLD", TargetField.GOLD_QUANTITY, DataType.DECIMAL, True),
                ("Gold Paid for", TargetField.PURCHASE_RATE, DataType.DECIMAL, True),
                ("COST", TargetField.PURCHASE_COST, DataType.DECIMAL, True),
                ("Date", TargetField.PURCHASE_DATE, DataType.DATE, False),
                ("SILVER", TargetField.SILVER_BONUS, DataType.DECIMAL, False),
            ]
        elif preset_name == "Sale":
            # نقش‌های پیش‌فرض برای شیت فروش
            presets = [
                ("Label", TargetField.ACCOUNT_ID, DataType.TEXT, True),
                ("RZGold", TargetField.SALE_QUANTITY, DataType.DECIMAL, True),
                ("Rate For Sale", TargetField.SALE_RATE, DataType.DECIMAL, True),
                ("Type", TargetField.SALE_TYPE, DataType.TEXT, False),
                ("Customer", TargetField.CUSTOMER_CODE, DataType.TEXT, False),
                ("Sold Date", TargetField.SALE_DATE, DataType.DATE, False),
                ("INTEREST($)", TargetField.STAFF_PROFIT, DataType.DECIMAL, False),
            ]
        elif preset_name == "Bonus":
            # نقش‌های پیش‌فرض برای شیت بونوس
            presets = [
                ("Label", TargetField.ACCOUNT_ID, DataType.TEXT, True),
                ("Silver Bonus", TargetField.SILVER_BONUS, DataType.DECIMAL, True),
            ]
        else:
            raise ValueError(f"Preset نامشخص: {preset_name}")
        
        # ایجاد Mapping ها
        for source_col, target, dtype, required in presets:
            self.set_mapping_for_sheet(
                config_id=config_id,
                config_name=sheet_config.name,
                source_column=source_col,
                target_field=target,
                data_type=dtype,
                is_required=required
            )
        
        self.financial_db.commit()
    
    def get_available_columns_for_sheet(self, config_id: int) -> List[str]:
        """
        دریافت لیست ستون‌های موجود در یک SheetConfig
        (از column_mappings در SheetConfig)
        """
        sheet_config = self.get_sheet_config_by_id(config_id)
        if not sheet_config or not sheet_config.column_mappings:
            return []
        
        # column_mappings یک dict است
        return list(sheet_config.column_mappings.keys())
    
    def validate_mappings_for_sheet(self, config_id: int) -> Dict[str, any]:
        """
        اعتبارسنجی Mapping های یک SheetConfig
        
        Returns:
            {
                "valid": True/False,
                "errors": [...],
                "warnings": [...],
                "required_missing": [...]
            }
        """
        sheet_config = self.get_sheet_config_by_id(config_id)
        mappings = self.get_mappings_for_sheet(config_id)
        
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "required_missing": []
        }
        
        # بررسی: آیا حداقل ACCOUNT_ID Map شده؟
        has_account_id = any(m.target_field == TargetField.ACCOUNT_ID for m in mappings)
        if not has_account_id:
            result["valid"] = False
            result["errors"].append("فیلد ACCOUNT_ID (Label) الزامی است")
        
        # بررسی نوع شیت
        if sheet_config and sheet_config.sheet_type == "Purchase":
            # برای خرید: باید GOLD_QUANTITY و PURCHASE_RATE داشته باشیم
            has_gold = any(m.target_field == TargetField.GOLD_QUANTITY for m in mappings)
            has_rate = any(m.target_field == TargetField.PURCHASE_RATE for m in mappings)
            
            if not has_gold:
                result["warnings"].append("فیلد GOLD_QUANTITY توصیه می‌شود")
            if not has_rate:
                result["warnings"].append("فیلد PURCHASE_RATE توصیه می‌شود")
        
        elif sheet_config and sheet_config.sheet_type == "Sale":
            # برای فروش: باید SALE_QUANTITY و SALE_RATE داشته باشیم
            has_qty = any(m.target_field == TargetField.SALE_QUANTITY for m in mappings)
            has_rate = any(m.target_field == TargetField.SALE_RATE for m in mappings)
            
            if not has_qty:
                result["warnings"].append("فیلد SALE_QUANTITY توصیه می‌شود")
            if not has_rate:
                result["warnings"].append("فیلد SALE_RATE توصیه می‌شود")
        
        return result
    
    def close(self):
        """بستن session ها"""
        if self.main_db:
            self.main_db.close()
        if self.financial_db:
            self.financial_db.close()
