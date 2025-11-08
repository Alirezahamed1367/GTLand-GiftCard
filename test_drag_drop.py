"""
تست ساده Drag & Drop Widget
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from app.gui.widgets.column_mapping_widget import ColumnMappingWidget

def main():
    print("="*60)
    print("🧪 Testing Drag & Drop Column Mapping Widget")
    print("="*60)
    
    app = QApplication(sys.argv)
    
    # داده‌های تست
    excel_columns = ['A', 'B', 'C', 'D', 'E', 'F']
    
    available_sheets = {
        1: {
            'name': 'Google Sheet Test 1',
            'worksheet': 'Sheet1',
            'columns': ['نام', 'کد', 'قیمت', 'تعداد', 'توضیحات']
        },
        2: {
            'name': 'Google Sheet Test 2',
            'worksheet': 'Sheet2',
            'columns': ['تاریخ', 'مبلغ', 'نوع', 'وضعیت']
        }
    }
    
    # ساخت پنجره
    window = QMainWindow()
    window.setWindowTitle("Test Drag & Drop")
    window.resize(1000, 700)
    
    # ویجت مرکزی
    central_widget = QWidget()
    layout = QVBoxLayout(central_widget)
    
    # ویجت Mapping
    try:
        mapping_widget = ColumnMappingWidget(
            parent=window,
            excel_columns=excel_columns,
            available_sheets=available_sheets
        )
        layout.addWidget(mapping_widget)
        print("✅ Widget created successfully")
    except Exception as e:
        print(f"❌ Error creating widget: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    window.setCentralWidget(central_widget)
    window.show()
    
    print("\n" + "="*60)
    print("💡 Instructions:")
    print("1. Select a Google Sheet from dropdown")
    print("2. Drag a column from RIGHT side")
    print("3. Drop it on an Excel column on LEFT side")
    print("4. Watch for errors in terminal")
    print("="*60 + "\n")
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
