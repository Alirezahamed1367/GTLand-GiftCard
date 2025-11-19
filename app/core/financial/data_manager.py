"""
DataManager: API برای مدیریت EAV Database
============================================

این کلاس رابط کامل برای کار با سیستم EAV فراهم می‌کنه:
- مدیریت DataSources
- مدیریت FieldDefinitions
- ورود و خروج داده
- Query و فیلتر
"""

from sqlalchemy import and_, or_, func, text
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict, Optional, Any, Union
from datetime import datetime, date
from decimal import Decimal
import json

from app.models.financial import get_financial_session
from app.models.financial.dynamic_eav import (
    DataSource, FieldDefinition, DataEntity, FieldValue,
    Formula, ReportDefinition, MaterializedView
)


class DataManager:
    """
    مدیریت کامل داده‌های EAV
    
    مثال:
        dm = DataManager()
        source_id = dm.add_source("PUBG Sales", "google_sheet", {...})
        field_id = dm.add_field(source_id, "amount", "decimal", role="amount")
        entities = dm.import_data(source_id, data_rows)
        results = dm.query(source_ids=[source_id], filters=[...])
    """
    
    def __init__(self, session: Optional[Session] = None):
        """
        Args:
            session: SQLAlchemy session (اگر None باشه خودش می‌سازه)
        """
        self.session = session or get_financial_session()
        self._auto_close = session is None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._auto_close:
            self.session.close()
    
    # ================== DATA SOURCES ==================
    
    def add_source(
        self,
        name: str,
        source_type: str,
        connection_info: Dict[str, Any],
        **kwargs
    ) -> int:
        """
        اضافه کردن یک Data Source جدید
        
        Args:
            name: نام منبع (مثلاً "PUBG Sales October")
            source_type: نوع (google_sheet, excel, csv, api, database)
            connection_info: اطلاعات اتصال (URL, credentials, ...)
            **kwargs: سایر تنظیمات (auto_sync, sync_frequency, ...)
        
        Returns:
            ID منبع ساخته شده
        """
        source = DataSource(
            name=name,
            source_type=source_type,
            connection_info=connection_info,
            **kwargs
        )
        self.session.add(source)
        self.session.commit()
        return source.id
    
    def get_source(self, source_id: int) -> Optional[DataSource]:
        """دریافت یک source"""
        return self.session.query(DataSource).filter_by(id=source_id).first()
    
    def list_sources(self, source_type: Optional[str] = None) -> List[DataSource]:
        """لیست تمام sources"""
        query = self.session.query(DataSource)
        if source_type:
            query = query.filter_by(source_type=source_type)
        return query.all()
    
    def update_source(self, source_id: int, **updates):
        """به‌روزرسانی یک source"""
        source = self.get_source(source_id)
        if source:
            for key, value in updates.items():
                setattr(source, key, value)
            source.updated_at = datetime.utcnow()
            self.session.commit()
    
    def delete_source(self, source_id: int):
        """حذف یک source (و تمام داده‌هاش)"""
        source = self.get_source(source_id)
        if source:
            # حذف cascade می‌شه (entities → field_values)
            self.session.delete(source)
            self.session.commit()
    
    # ================== FIELD DEFINITIONS ==================
    
    def add_field(
        self,
        source_id: int,
        field_name: str,
        data_type: str,
        field_display_name: Optional[str] = None,
        field_role: Optional[str] = None,
        **kwargs
    ) -> int:
        """
        اضافه کردن یک فیلد جدید
        
        Args:
            source_id: ID منبع
            field_name: نام فیلد (technical)
            data_type: نوع داده (text, number, decimal, date, ...)
            field_display_name: نام نمایشی (فارسی)
            field_role: نقش فیلد (label, customer, amount, ...)
            **kwargs: is_required, is_unique, validation_rules, ...
        
        Returns:
            ID فیلد ساخته شده
        """
        field = FieldDefinition(
            source_id=source_id,
            field_name=field_name,
            field_display_name=field_display_name or field_name,
            data_type=data_type,
            field_role=field_role,
            **kwargs
        )
        self.session.add(field)
        self.session.commit()
        return field.id
    
    def get_field(self, field_id: int) -> Optional[FieldDefinition]:
        """دریافت یک field"""
        return self.session.query(FieldDefinition).filter_by(id=field_id).first()
    
    def list_fields(
        self,
        source_id: Optional[int] = None,
        field_role: Optional[str] = None,
        data_type: Optional[str] = None
    ) -> List[FieldDefinition]:
        """لیست فیلدها"""
        query = self.session.query(FieldDefinition)
        if source_id:
            query = query.filter_by(source_id=source_id)
        if field_role:
            query = query.filter_by(field_role=field_role)
        if data_type:
            query = query.filter_by(data_type=data_type)
        return query.order_by(FieldDefinition.display_order).all()
    
    def update_field(self, field_id: int, **updates):
        """به‌روزرسانی یک field"""
        field = self.get_field(field_id)
        if field:
            for key, value in updates.items():
                setattr(field, key, value)
            field.updated_at = datetime.utcnow()
            self.session.commit()
    
    def delete_field(self, field_id: int):
        """حذف یک field (و تمام values)"""
        field = self.get_field(field_id)
        if field:
            self.session.delete(field)
            self.session.commit()
    
    # ================== DATA IMPORT ==================
    
    def import_data(
        self,
        source_id: int,
        data_rows: List[Dict[str, Any]],
        field_mapping: Optional[Dict[str, int]] = None
    ) -> List[int]:
        """
        ورود داده‌های bulk
        
        Args:
            source_id: ID منبع
            data_rows: لیست رکوردها (هر رکورد یک dict)
            field_mapping: نگاشت column_name → field_id
        
        Returns:
            لیست entity_ids ساخته شده
        
        مثال:
            data_rows = [
                {"Label": "A123", "Customer": "Ali", "Amount": 1500},
                {"Label": "B456", "Customer": "Sara", "Amount": 2000},
            ]
            field_mapping = {"Label": 1, "Customer": 2, "Amount": 3}
            entity_ids = dm.import_data(source_id, data_rows, field_mapping)
        """
        if not field_mapping:
            # اگر mapping نداریم، از ترتیب fields استفاده می‌کنیم
            fields = self.list_fields(source_id)
            field_mapping = {f.field_name: f.id for f in fields}
        
        entity_ids = []
        
        for row in data_rows:
            # ساخت entity
            entity = DataEntity(
                source_id=source_id,
                source_entity_id=row.get("id"),  # اگر ID داشته باشه
                entity_type="data"  # یا از row بخونیم
            )
            self.session.add(entity)
            self.session.flush()  # تا entity.id بگیریم
            
            # ساخت field values
            for column_name, value in row.items():
                if column_name == "id":
                    continue  # این رو source_entity_id کردیم
                
                field_id = field_mapping.get(column_name)
                if not field_id:
                    continue  # فیلد تعریف نشده
                
                field = self.get_field(field_id)
                if not field:
                    continue
                
                # ساخت FieldValue بر اساس نوع
                field_value = self._create_field_value(
                    entity_id=entity.id,
                    field_id=field_id,
                    value=value,
                    data_type=field.data_type
                )
                self.session.add(field_value)
            
            entity_ids.append(entity.id)
        
        self.session.commit()
        
        # به‌روزرسانی تعداد رکوردها
        self.update_source(source_id, total_records=len(entity_ids))
        
        return entity_ids
    
    def _create_field_value(
        self,
        entity_id: int,
        field_id: int,
        value: Any,
        data_type: str
    ) -> FieldValue:
        """
        ساخت FieldValue بر اساس نوع داده
        """
        fv = FieldValue(entity_id=entity_id, field_id=field_id)
        
        if value is None:
            return fv
        
        if data_type == "text":
            fv.value_text = str(value)
        elif data_type == "number":
            fv.value_number = int(value)
        elif data_type == "decimal":
            fv.value_decimal = Decimal(str(value))
        elif data_type == "date":
            if isinstance(value, str):
                fv.value_date = datetime.strptime(value, "%Y-%m-%d").date()
            elif isinstance(value, datetime):
                fv.value_date = value.date()
            elif isinstance(value, date):
                fv.value_date = value
        elif data_type == "datetime":
            if isinstance(value, str):
                fv.value_datetime = datetime.fromisoformat(value)
            elif isinstance(value, datetime):
                fv.value_datetime = value
        elif data_type == "boolean":
            fv.value_boolean = bool(value)
        elif data_type in ("json", "choice"):
            fv.value_json = value if isinstance(value, dict) else {"value": value}
        elif data_type == "lookup":
            fv.value_entity_id = int(value)
        else:
            # Unknown type → store as text
            fv.value_text = str(value)
        
        return fv
    
    # ================== DATA QUERY ==================
    
    def query(
        self,
        source_ids: Optional[List[int]] = None,
        fields: Optional[List[Union[int, str]]] = None,
        filters: Optional[List[Dict[str, Any]]] = None,
        group_by: Optional[List[Union[int, str]]] = None,
        order_by: Optional[List[Dict[str, str]]] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Query کامل روی EAV
        
        Args:
            source_ids: لیست source IDs
            fields: لیست field IDs یا names (None = همه)
            filters: لیست فیلترها [{"field": ..., "operator": ..., "value": ...}]
            group_by: گروه‌بندی بر اساس فیلدها
            order_by: مرتب‌سازی [{"field": ..., "direction": "asc|desc"}]
            limit: محدودیت تعداد
            offset: شروع از رکورد چندم
        
        Returns:
            لیست رکوردها (هر رکورد یک dict)
        
        مثال:
            results = dm.query(
                source_ids=[1],
                fields=["customer", "amount"],
                filters=[
                    {"field": "amount", "operator": ">", "value": 1000}
                ],
                order_by=[{"field": "amount", "direction": "desc"}],
                limit=10
            )
        """
        # TODO: این بخش پیچیده‌ترین بخش است
        # باید SQL پیچیده‌ای برای JOIN بین entities و values بسازیم
        
        # فعلاً یک implementation ساده:
        query_base = self.session.query(DataEntity)
        
        if source_ids:
            # اگر یک integer است، تبدیل به لیست کن
            if isinstance(source_ids, int):
                source_ids = [source_ids]
            query_base = query_base.filter(DataEntity.source_id.in_(source_ids))
        
        entities = query_base.limit(limit or 1000).offset(offset).all()
        
        results = []
        for entity in entities:
            row = {"_entity_id": entity.id}
            
            # دریافت تمام field values این entity
            values = self.session.query(FieldValue).filter_by(entity_id=entity.id).all()
            
            for fv in values:
                field = self.get_field(fv.field_id)
                if not field:
                    continue
                
                # استخراج مقدار بر اساس نوع
                value = self._extract_field_value(fv, field.data_type)
                row[field.field_name] = value
            
            results.append(row)
        
        return results
    
    def _extract_field_value(self, fv: FieldValue, data_type: str) -> Any:
        """استخراج مقدار از FieldValue"""
        if data_type == "text":
            return fv.value_text
        elif data_type == "number":
            return fv.value_number
        elif data_type == "decimal":
            return float(fv.value_decimal) if fv.value_decimal else None
        elif data_type == "date":
            return fv.value_date
        elif data_type == "datetime":
            return fv.value_datetime
        elif data_type == "boolean":
            return fv.value_boolean
        elif data_type in ("json", "choice"):
            return fv.value_json
        elif data_type == "lookup":
            return fv.value_entity_id
        else:
            return fv.value_text
    
    def get_entity(self, entity_id: int) -> Optional[Dict[str, Any]]:
        """دریافت یک entity کامل"""
        results = self.query(filters=[{"field": "_entity_id", "operator": "=", "value": entity_id}])
        return results[0] if results else None
    
    def update_entity(
        self,
        entity_id: int,
        updates: Dict[Union[int, str], Any]
    ):
        """
        به‌روزرسانی یک entity
        
        Args:
            entity_id: ID رکورد
            updates: dict از field_id/name → value جدید
        """
        for field_identifier, new_value in updates.items():
            # پیدا کردن field
            if isinstance(field_identifier, int):
                field = self.get_field(field_identifier)
            else:
                field = self.session.query(FieldDefinition).filter_by(
                    field_name=field_identifier
                ).first()
            
            if not field:
                continue
            
            # پیدا یا ساخت FieldValue
            fv = self.session.query(FieldValue).filter_by(
                entity_id=entity_id,
                field_id=field.id
            ).first()
            
            if not fv:
                fv = FieldValue(entity_id=entity_id, field_id=field.id)
                self.session.add(fv)
            
            # به‌روزرسانی مقدار
            self._update_field_value(fv, new_value, field.data_type)
        
        self.session.commit()
    
    def _update_field_value(self, fv: FieldValue, value: Any, data_type: str):
        """به‌روزرسانی مقدار در FieldValue"""
        # ابتدا همه رو None می‌کنیم
        fv.value_text = None
        fv.value_number = None
        fv.value_decimal = None
        fv.value_date = None
        fv.value_datetime = None
        fv.value_boolean = None
        fv.value_json = None
        fv.value_entity_id = None
        
        # حالا مقدار جدید رو set می‌کنیم
        if value is None:
            return
        
        if data_type == "text":
            fv.value_text = str(value)
        elif data_type == "number":
            fv.value_number = int(value)
        elif data_type == "decimal":
            fv.value_decimal = Decimal(str(value))
        elif data_type == "date":
            if isinstance(value, str):
                fv.value_date = datetime.strptime(value, "%Y-%m-%d").date()
            else:
                fv.value_date = value
        elif data_type == "datetime":
            if isinstance(value, str):
                fv.value_datetime = datetime.fromisoformat(value)
            else:
                fv.value_datetime = value
        elif data_type == "boolean":
            fv.value_boolean = bool(value)
        elif data_type in ("json", "choice"):
            fv.value_json = value
        elif data_type == "lookup":
            fv.value_entity_id = int(value)
    
    def delete_entity(self, entity_id: int):
        """حذف یک entity (و تمام field values)"""
        entity = self.session.query(DataEntity).filter_by(id=entity_id).first()
        if entity:
            self.session.delete(entity)
            self.session.commit()
    
    # ================== STATISTICS ==================
    
    def get_source_stats(self, source_id: int) -> Dict[str, Any]:
        """آمار یک source"""
        source = self.get_source(source_id)
        if not source:
            return {}
        
        entity_count = self.session.query(DataEntity).filter_by(source_id=source_id).count()
        field_count = self.session.query(FieldDefinition).filter_by(source_id=source_id).count()
        
        return {
            "source_name": source.name,
            "source_type": source.source_type,
            "entity_count": entity_count,
            "field_count": field_count,
            "total_records": source.total_records,
            "last_sync": source.last_sync_at,
        }
    
    def get_field_stats(self, field_id: int) -> Dict[str, Any]:
        """آمار یک field"""
        field = self.get_field(field_id)
        if not field:
            return {}
        
        value_count = self.session.query(FieldValue).filter_by(field_id=field_id).count()
        
        stats = {
            "field_name": field.field_display_name,
            "data_type": field.data_type,
            "field_role": field.field_role,
            "value_count": value_count,
        }
        
        # آمار بر اساس نوع داده
        if field.data_type == "number":
            result = self.session.query(
                func.min(FieldValue.value_number),
                func.max(FieldValue.value_number),
                func.avg(FieldValue.value_number)
            ).filter_by(field_id=field_id).first()
            stats["min"] = result[0]
            stats["max"] = result[1]
            stats["avg"] = float(result[2]) if result[2] else None
        
        elif field.data_type == "decimal":
            result = self.session.query(
                func.min(FieldValue.value_decimal),
                func.max(FieldValue.value_decimal),
                func.avg(FieldValue.value_decimal)
            ).filter_by(field_id=field_id).first()
            stats["min"] = float(result[0]) if result[0] else None
            stats["max"] = float(result[1]) if result[1] else None
            stats["avg"] = float(result[2]) if result[2] else None
        
        return stats


# ================== HELPER FUNCTIONS ==================

def create_default_fields_for_financial() -> List[Dict[str, Any]]:
    """
    فیلدهای پیش‌فرض برای یک سیستم مالی
    
    Returns:
        لیست تعاریف فیلد
    """
    return [
        {
            "field_name": "label",
            "field_display_name": "شناسه",
            "data_type": "text",
            "field_role": "label",
            "is_required": True,
            "is_unique": True,
        },
        {
            "field_name": "customer",
            "field_display_name": "مشتری",
            "data_type": "text",
            "field_role": "customer",
            "is_required": True,
        },
        {
            "field_name": "amount",
            "field_display_name": "مبلغ",
            "data_type": "decimal",
            "field_role": "amount",
            "is_required": True,
            "validation_rules": {"min": 0},
        },
        {
            "field_name": "rate",
            "field_display_name": "نرخ",
            "data_type": "decimal",
            "field_role": "rate",
            "validation_rules": {"min": 0},
        },
        {
            "field_name": "date",
            "field_display_name": "تاریخ",
            "data_type": "date",
            "field_role": "date",
            "is_required": True,
        },
        {
            "field_name": "status",
            "field_display_name": "وضعیت",
            "data_type": "choice",
            "field_role": "status",
            "validation_rules": {
                "choices": ["pending", "completed", "cancelled"]
            },
        },
        {
            "field_name": "description",
            "field_display_name": "توضیحات",
            "data_type": "text",
            "field_role": "description",
        },
    ]


if __name__ == "__main__":
    # تست
    with DataManager() as dm:
        # ساخت یک source
        source_id = dm.add_source(
            name="Test Source",
            source_type="google_sheet",
            connection_info={"url": "https://..."}
        )
        print(f"Created source: {source_id}")
        
        # ساخت فیلدها
        fields = create_default_fields_for_financial()
        for field_def in fields:
            field_id = dm.add_field(source_id=source_id, **field_def)
            print(f"Created field: {field_def['field_name']} (ID: {field_id})")
        
        # Import داده
        sample_data = [
            {
                "label": "A123",
                "customer": "Ali",
                "amount": 1500.50,
                "rate": 84.5,
                "date": "2025-11-13",
                "status": "completed",
            },
            {
                "label": "B456",
                "customer": "Sara",
                "amount": 2000.00,
                "rate": 85.0,
                "date": "2025-11-13",
                "status": "pending",
            },
        ]
        
        entity_ids = dm.import_data(source_id, sample_data)
        print(f"Imported {len(entity_ids)} entities")
        
        # Query
        results = dm.query(source_ids=[source_id])
        print(f"\nQuery results: {len(results)} rows")
        for row in results:
            print(row)
        
        # Stats
        stats = dm.get_source_stats(source_id)
        print(f"\nSource stats: {stats}")
