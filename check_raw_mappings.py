from app.core.database import db_manager
from app.models import ExportTemplate
import json

db = db_manager.get_session()
template = db.query(ExportTemplate).filter_by(name='کالا').first()

if template:
    print(f"Template: {template.name}")
    print(f"\nColumn Mappings (RAW):")
    print(json.dumps(template.column_mappings, indent=2, ensure_ascii=False))
    
    print(f"\nنوع: {type(template.column_mappings)}")
    print(f"تعداد: {len(template.column_mappings) if template.column_mappings else 0}")
    
    if template.column_mappings:
        print(f"\nاولین مورد:")
        print(json.dumps(template.column_mappings[0], indent=2, ensure_ascii=False))

db.close()
