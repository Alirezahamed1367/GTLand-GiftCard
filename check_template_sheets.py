from app.core.database import db_manager
from app.models import ExportTemplate
import json

db = db_manager.get_session()
template = db.query(ExportTemplate).filter_by(name='کالا').first()

if template:
    print(f"Template: {template.name}")
    print(f"\nColumn Mappings:")
    
    mappings = template.column_mappings
    sheets = set()
    
    for mapping in mappings:
        if isinstance(mapping, dict) and 'source_sheet' in mapping:
            sheets.add(mapping['source_sheet'])
            print(f"  - {mapping.get('target_column', '???')} ← {mapping['source_sheet']}.{mapping.get('source_column', '???')}")
    
    print(f"\n📋 شیت‌های منبع یافت شده: {list(sheets)}")
    print(f"✅ تعداد: {len(sheets)}")
else:
    print("Template 'کالا' پیدا نشد")

db.close()
