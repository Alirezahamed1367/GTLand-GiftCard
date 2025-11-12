from app.core.database import db_manager
from app.models import ExportTemplate
import json

db = db_manager.get_session()
templates = db.query(ExportTemplate).all()

print(f"📋 تعداد Template ها: {len(templates)}\n")

for template in templates:
    print(f"{'='*60}")
    print(f"📄 Template: {template.name}")
    print(f"   نوع: {template.template_type}")
    
    mappings = template.column_mappings
    sheets = set()
    
    if mappings:
        for mapping in mappings:
            if isinstance(mapping, dict) and 'source_sheet' in mapping:
                sheets.add(mapping['source_sheet'])
        
        print(f"   📊 شیت‌های منبع: {list(sheets) if sheets else 'هیچ'}")
        print(f"   🔢 تعداد: {len(sheets)}")
    else:
        print(f"   ⚠️ بدون column mapping")
    
    print()

db.close()
