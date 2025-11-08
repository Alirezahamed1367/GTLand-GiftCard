"""
تست Template Manager پیشرفته
"""
import sys
from pathlib import Path

# اضافه کردن مسیر پروژه
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from app.gui.dialogs.template_manager_dialog_advanced import TemplateManagerDialog
from app.core.database import db_manager

def main():
    print("="*60)
    print("🧪 Testing Template Manager Dialog")
    print("="*60)
    
    # 1. Test database connection
    print("\n1️⃣ Testing database connection...")
    templates = db_manager.get_all_templates()
    print(f"✅ Found {len(templates)} templates in database")
    
    # 2. Test Qt Application
    print("\n2️⃣ Creating Qt Application...")
    app = QApplication(sys.argv)
    print("✅ Qt App created")
    
    # 3. Test Dialog Creation
    print("\n3️⃣ Creating Template Manager Dialog...")
    dialog = TemplateManagerDialog()
    print("✅ Dialog created successfully")
    
    # 4. Show Dialog
    print("\n4️⃣ Showing Dialog...")
    print("💡 Click 'Add Template' button to test wizard")
    print("="*60)
    
    dialog.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
