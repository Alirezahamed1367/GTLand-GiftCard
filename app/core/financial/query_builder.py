"""
QueryBuilder: ساخت SQL بهینه برای EAV
=====================================

این کلاس فیلترهای پیچیده رو به SQL بهینه تبدیل می‌کنه
"""

from sqlalchemy import and_, or_, func, text
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, date

from app.models.financial import get_financial_session
from app.models.financial.dynamic_eav import (
    DataSource, FieldDefinition, DataEntity, FieldValue
)


class QueryBuilder:
    """
    ساخت query های بهینه برای EAV
    
    مثال:
        qb = QueryBuilder()
        results = qb.build_query(
            source_ids=[1],
            filters=[
                {"field_id": 3, "operator": ">", "value": 1000}
            ]
        )
    """
    
    def __init__(self, session: Optional[Session] = None):
        """
        Args:
            session: SQLAlchemy session
        """
        self.session = session or get_financial_session()
        self._auto_close = session is None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._auto_close:
            self.session.close()
    
    def build_query(
        self,
        source_ids: List[int],
        field_ids: Optional[List[int]] = None,
        filters: Optional[List[Dict[str, Any]]] = None,
        order_by: Optional[List[Dict[str, str]]] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        ساخت و اجرای query
        
        Args:
            source_ids: لیست source IDs
            field_ids: لیست field IDs (None = همه)
            filters: فیلترها [{"field_id": 3, "operator": ">", "value": 1000}]
            order_by: مرتب‌سازی [{"field_id": 3, "direction": "desc"}]
            limit: محدودیت تعداد
            offset: شروع از رکورد چندم
        
        Returns:
            لیست رکوردها
        """
        # دریافت تمام entities
        entities_query = self.session.query(DataEntity).filter(
            DataEntity.source_id.in_(source_ids)
        )
        
        # اعمال فیلترها
        if filters:
            entities_query = self._apply_filters(entities_query, filters)
        
        # Pagination
        if limit:
            entities_query = entities_query.limit(limit).offset(offset)
        else:
            entities_query = entities_query.limit(1000).offset(offset)  # Default limit
        
        entities = entities_query.all()
        
        if not entities:
            return []
        
        # دریافت entity IDs
        entity_ids = [e.id for e in entities]
        
        # دریافت تمام field values برای این entities
        values_query = self.session.query(FieldValue).filter(
            FieldValue.entity_id.in_(entity_ids)
        )
        
        if field_ids:
            values_query = values_query.filter(FieldValue.field_id.in_(field_ids))
        
        field_values = values_query.all()
        
        # دریافت field definitions
        field_defs_query = self.session.query(FieldDefinition).filter(
            FieldDefinition.source_id.in_(source_ids)
        )
        if field_ids:
            field_defs_query = field_defs_query.filter(FieldDefinition.id.in_(field_ids))
        
        field_defs = {f.id: f for f in field_defs_query.all()}
        
        # ساخت دیکشنری values به تفکیک entity
        entity_values = {}
        for fv in field_values:
            if fv.entity_id not in entity_values:
                entity_values[fv.entity_id] = {}
            
            field = field_defs.get(fv.field_id)
            if field:
                value = self._extract_value(fv, field.data_type)
                entity_values[fv.entity_id][field.field_name] = value
        
        # ساخت نتیجه نهایی
        results = []
        for entity in entities:
            row = {
                "_entity_id": entity.id,
                "_source_id": entity.source_id,
                "_created_at": entity.created_at,
            }
            row.update(entity_values.get(entity.id, {}))
            results.append(row)
        
        # مرتب‌سازی
        if order_by:
            results = self._sort_results(results, order_by, field_defs)
        
        return results
    
    def _apply_filters(
        self,
        query,
        filters: List[Dict[str, Any]]
    ):
        """
        اعمال فیلترها روی query
        
        این بخش پیچیده‌ترین قسمت است چون باید JOIN های متعدد
        روی FieldValue بزنیم
        """
        for i, filter_def in enumerate(filters):
            field_id = filter_def.get("field_id")
            operator = filter_def.get("operator", "=")
            value = filter_def.get("value")
            
            if not field_id:
                continue
            
            # دریافت field definition
            field = self.session.query(FieldDefinition).filter_by(id=field_id).first()
            if not field:
                continue
            
            # ایجاد alias برای این فیلتر
            fv_alias = f"fv_{i}"
            
            # JOIN با FieldValue
            subquery = self.session.query(FieldValue.entity_id).filter(
                FieldValue.field_id == field_id
            )
            
            # اعمال شرط بر اساس نوع داده
            if field.data_type == "text":
                subquery = self._apply_text_filter(subquery, operator, value)
            elif field.data_type in ("number", "decimal"):
                subquery = self._apply_numeric_filter(subquery, operator, value, field.data_type)
            elif field.data_type == "date":
                subquery = self._apply_date_filter(subquery, operator, value)
            elif field.data_type == "boolean":
                subquery = self._apply_boolean_filter(subquery, value)
            
            # اعمال به query اصلی
            query = query.filter(DataEntity.id.in_(subquery))
        
        return query
    
    def _apply_text_filter(self, subquery, operator: str, value: str):
        """فیلتر متنی"""
        if operator == "=":
            return subquery.filter(FieldValue.value_text == value)
        elif operator == "!=":
            return subquery.filter(FieldValue.value_text != value)
        elif operator == "CONTAINS":
            return subquery.filter(FieldValue.value_text.contains(value))
        elif operator == "STARTS_WITH":
            return subquery.filter(FieldValue.value_text.startswith(value))
        elif operator == "ENDS_WITH":
            return subquery.filter(FieldValue.value_text.endswith(value))
        elif operator == "IS_EMPTY":
            return subquery.filter(
                or_(FieldValue.value_text == None, FieldValue.value_text == "")
            )
        elif operator == "IS_NOT_EMPTY":
            return subquery.filter(
                and_(FieldValue.value_text != None, FieldValue.value_text != "")
            )
        return subquery
    
    def _apply_numeric_filter(self, subquery, operator: str, value: Any, data_type: str):
        """فیلتر عددی"""
        column = FieldValue.value_number if data_type == "number" else FieldValue.value_decimal
        
        try:
            value = float(value)
        except:
            return subquery
        
        if operator == "=":
            return subquery.filter(column == value)
        elif operator == "!=":
            return subquery.filter(column != value)
        elif operator == ">":
            return subquery.filter(column > value)
        elif operator == ">=":
            return subquery.filter(column >= value)
        elif operator == "<":
            return subquery.filter(column < value)
        elif operator == "<=":
            return subquery.filter(column <= value)
        elif operator == "BETWEEN":
            # value باید tuple باشه: (min, max)
            if isinstance(value, (list, tuple)) and len(value) == 2:
                return subquery.filter(and_(column >= value[0], column <= value[1]))
        
        return subquery
    
    def _apply_date_filter(self, subquery, operator: str, value: Any):
        """فیلتر تاریخی"""
        if operator in ("LAST_7_DAYS", "LAST_30_DAYS", "THIS_MONTH", "THIS_YEAR"):
            # محاسبه بازه تاریخی
            today = date.today()
            
            if operator == "LAST_7_DAYS":
                start_date = today - timedelta(days=7)
                return subquery.filter(FieldValue.value_date >= start_date)
            elif operator == "LAST_30_DAYS":
                start_date = today - timedelta(days=30)
                return subquery.filter(FieldValue.value_date >= start_date)
            elif operator == "THIS_MONTH":
                start_date = date(today.year, today.month, 1)
                return subquery.filter(FieldValue.value_date >= start_date)
            elif operator == "THIS_YEAR":
                start_date = date(today.year, 1, 1)
                return subquery.filter(FieldValue.value_date >= start_date)
        else:
            # عملگرهای معمولی
            if isinstance(value, str):
                try:
                    value = datetime.strptime(value, "%Y-%m-%d").date()
                except:
                    return subquery
            
            if operator == "=":
                return subquery.filter(FieldValue.value_date == value)
            elif operator == ">":
                return subquery.filter(FieldValue.value_date > value)
            elif operator == "<":
                return subquery.filter(FieldValue.value_date < value)
            elif operator == ">=":
                return subquery.filter(FieldValue.value_date >= value)
            elif operator == "<=":
                return subquery.filter(FieldValue.value_date <= value)
            elif operator == "BETWEEN":
                if isinstance(value, (list, tuple)) and len(value) == 2:
                    return subquery.filter(
                        and_(FieldValue.value_date >= value[0], FieldValue.value_date <= value[1])
                    )
        
        return subquery
    
    def _apply_boolean_filter(self, subquery, value: Any):
        """فیلتر بولین"""
        bool_value = bool(value) if not isinstance(value, bool) else value
        return subquery.filter(FieldValue.value_boolean == bool_value)
    
    def _extract_value(self, fv: FieldValue, data_type: str) -> Any:
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
    
    def _sort_results(
        self,
        results: List[Dict[str, Any]],
        order_by: List[Dict[str, str]],
        field_defs: Dict[int, FieldDefinition]
    ) -> List[Dict[str, Any]]:
        """مرتب‌سازی نتایج"""
        for order in reversed(order_by):
            field_id = order.get("field_id")
            direction = order.get("direction", "asc")
            
            field = field_defs.get(field_id)
            if not field:
                continue
            
            field_name = field.field_name
            
            # مرتب‌سازی
            results.sort(
                key=lambda x: x.get(field_name, ""),
                reverse=(direction.lower() == "desc")
            )
        
        return results
    
    def count_results(
        self,
        source_ids: List[int],
        filters: Optional[List[Dict[str, Any]]] = None
    ) -> int:
        """
        شمارش تعداد نتایج بدون دریافت داده
        
        Returns:
            تعداد رکوردها
        """
        query = self.session.query(func.count(DataEntity.id)).filter(
            DataEntity.source_id.in_(source_ids)
        )
        
        if filters:
            query = self._apply_filters(query, filters)
        
        return query.scalar()


# Import برای date filter
from datetime import timedelta


if __name__ == "__main__":
    # تست
    qb = QueryBuilder()
    
    # تست ساده
    results = qb.build_query(
        source_ids=[1],
        limit=5
    )
    
    print(f"Found {len(results)} results")
    for row in results:
        print(row)
