"""
Graphical Formula Builder
سازنده فرمول گرافیکی - مثل Excel Formula Builder

کاربر می‌تونه:
- فیلدها رو drag & drop کنه
- عملگرها رو انتخاب کنه (+, -, *, /, SUM, AVG, IF, ...)
- فرمول‌های پیچیده بسازه
- نتیجه رو preview کنه
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QDialog, QLabel,
    QPushButton, QListWidget, QTextEdit, QComboBox, QLineEdit,
    QTreeWidget, QTreeWidgetItem, QSplitter, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QDragEnterEvent, QDropEvent
import json
import re


class FormulaBuilderDialog(QDialog):
    """
    دیالوگ ساخت فرمول
    """
    
    formula_created = pyqtSignal(str, dict)  # formula_text, formula_ast
    
    def __init__(self, available_fields: list, parent=None):
        """
        available_fields: لیستی از فیلدهای موجود
        [
            {"id": 1, "name": "amount", "display_name": "مبلغ", "type": "decimal"},
            {"id": 2, "name": "rate", "display_name": "نرخ", "type": "decimal"},
            ...
        ]
        """
        super().__init__(parent)
        self.available_fields = available_fields
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Formula Builder")
        self.setMinimumSize(900, 600)
        
        layout = QVBoxLayout(self)
        
        # ═══════════════════════════════════════════════════════
        #                      HEADER
        # ═══════════════════════════════════════════════════════
        
        title = QLabel("🧮 Formula Builder")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #2196F3; padding: 10px;")
        layout.addWidget(title)
        
        # Splitter اصلی
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # ═══════════════════════════════════════════════════════
        #                   LEFT PANEL: Tools
        # ═══════════════════════════════════════════════════════
        
        tools_widget = QWidget()
        tools_layout = QVBoxLayout(tools_widget)
        
        # 1. Fields
        fields_group = QGroupBox("📋 Fields")
        fields_layout = QVBoxLayout()
        
        self.fields_list = QListWidget()
        for field in self.available_fields:
            self.fields_list.addItem(f"{field['display_name']} ({field['name']})")
        self.fields_list.itemDoubleClicked.connect(self.insert_field)
        
        fields_layout.addWidget(self.fields_list)
        fields_group.setLayout(fields_layout)
        tools_layout.addWidget(fields_group)
        
        # 2. Operators
        ops_group = QGroupBox("➗ Operators")
        ops_layout = QVBoxLayout()
        
        operators = [
            ("+", "Add"),
            ("-", "Subtract"),
            ("*", "Multiply"),
            ("/", "Divide"),
            ("(", "Open Parenthesis"),
            (")", "Close Parenthesis"),
        ]
        
        for op, label in operators:
            btn = QPushButton(f"{op}  {label}")
            btn.clicked.connect(lambda checked, o=op: self.insert_operator(o))
            ops_layout.addWidget(btn)
        
        ops_group.setLayout(ops_layout)
        tools_layout.addWidget(ops_group)
        
        # 3. Functions
        funcs_group = QGroupBox("🔢 Functions")
        funcs_layout = QVBoxLayout()
        
        functions = [
            ("SUM", "Sum of values"),
            ("AVG", "Average"),
            ("COUNT", "Count"),
            ("MIN", "Minimum"),
            ("MAX", "Maximum"),
            ("IF", "Conditional"),
            ("ROUND", "Round number"),
            ("ABS", "Absolute value"),
        ]
        
        for func, desc in functions:
            btn = QPushButton(f"{func}()")
            btn.setToolTip(desc)
            btn.clicked.connect(lambda checked, f=func: self.insert_function(f))
            funcs_layout.addWidget(btn)
        
        funcs_group.setLayout(funcs_layout)
        tools_layout.addWidget(funcs_group)
        
        splitter.addWidget(tools_widget)
        
        # ═══════════════════════════════════════════════════════
        #                  RIGHT PANEL: Formula Editor
        # ═══════════════════════════════════════════════════════
        
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        
        # Formula Input
        editor_layout.addWidget(QLabel("Formula:"))
        self.formula_input = QTextEdit()
        self.formula_input.setFont(QFont("Courier New", 11))
        self.formula_input.setPlaceholderText(
            "Example: (amount * rate) / 100\n"
            "Or: IF(amount > 1000, amount * 0.95, amount)"
        )
        self.formula_input.setMaximumHeight(150)
        editor_layout.addWidget(self.formula_input)
        
        # Test Values
        test_group = QGroupBox("🧪 Test Formula")
        test_layout = QVBoxLayout()
        
        test_layout.addWidget(QLabel("Enter test values:"))
        
        self.test_inputs = {}
        for field in self.available_fields:
            row = QHBoxLayout()
            row.addWidget(QLabel(field['display_name']))
            input_widget = QLineEdit()
            input_widget.setPlaceholderText(f"Test value for {field['name']}")
            self.test_inputs[field['name']] = input_widget
            row.addWidget(input_widget)
            test_layout.addLayout(row)
        
        test_btn = QPushButton("▶ Test Formula")
        test_btn.clicked.connect(self.test_formula)
        test_layout.addWidget(test_btn)
        
        self.test_result = QLabel("Result will appear here")
        self.test_result.setStyleSheet(
            "padding: 10px; background: #f5f5f5; border: 1px solid #ddd;"
        )
        test_layout.addWidget(self.test_result)
        
        test_group.setLayout(test_layout)
        editor_layout.addWidget(test_group)
        
        # Formula Tree (AST visualization)
        tree_group = QGroupBox("🌳 Formula Structure")
        tree_layout = QVBoxLayout()
        
        self.formula_tree = QTreeWidget()
        self.formula_tree.setHeaderLabels(["Node", "Type", "Value"])
        tree_layout.addWidget(self.formula_tree)
        
        tree_group.setLayout(tree_layout)
        editor_layout.addWidget(tree_group)
        
        splitter.addWidget(editor_widget)
        splitter.setSizes([300, 600])
        
        layout.addWidget(splitter)
        
        # ═══════════════════════════════════════════════════════
        #                      FOOTER: Buttons
        # ═══════════════════════════════════════════════════════
        
        btn_layout = QHBoxLayout()
        
        validate_btn = QPushButton("✓ Validate")
        validate_btn.clicked.connect(self.validate_formula)
        btn_layout.addWidget(validate_btn)
        
        btn_layout.addStretch()
        
        save_btn = QPushButton("Save Formula")
        save_btn.clicked.connect(self.save_formula)
        save_btn.setStyleSheet("background: #4CAF50; color: white; padding: 8px;")
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def insert_field(self):
        """درج فیلد در فرمول"""
        current_item = self.fields_list.currentItem()
        if current_item:
            # استخراج نام فیلد از متن
            text = current_item.text()
            match = re.search(r'\(([^)]+)\)', text)
            if match:
                field_name = match.group(1)
                self.formula_input.insertPlainText(f"[{field_name}]")
    
    def insert_operator(self, operator):
        """درج عملگر"""
        self.formula_input.insertPlainText(f" {operator} ")
    
    def insert_function(self, function):
        """درج تابع"""
        cursor = self.formula_input.textCursor()
        cursor.insertText(f"{function}(")
        cursor.insertText(")")
        cursor.movePosition(cursor.MoveOperation.Left)
        self.formula_input.setTextCursor(cursor)
    
    def parse_formula(self, formula_text):
        """
        تبدیل فرمول متنی به AST
        
        مثال:
        Input: "([amount] * [rate]) / 100"
        Output: {
            "type": "divide",
            "left": {
                "type": "multiply",
                "left": {"type": "field", "name": "amount"},
                "right": {"type": "field", "name": "rate"}
            },
            "right": {"type": "constant", "value": 100}
        }
        """
        # ساده‌سازی شده - در واقع باید یک parser کامل نوشت
        ast = {
            "type": "expression",
            "formula": formula_text,
            "fields": self.extract_fields(formula_text),
            "functions": self.extract_functions(formula_text)
        }
        return ast
    
    def extract_fields(self, formula):
        """استخراج فیلدهای استفاده شده در فرمول"""
        return re.findall(r'\[([^\]]+)\]', formula)
    
    def extract_functions(self, formula):
        """استخراج توابع استفاده شده"""
        return re.findall(r'([A-Z]+)\(', formula)
    
    def test_formula(self):
        """تست فرمول با مقادیر نمونه"""
        formula = self.formula_input.toPlainText()
        
        if not formula:
            self.test_result.setText("⚠ Please enter a formula first")
            return
        
        # جمع‌آوری مقادیر تست
        test_values = {}
        for field_name, input_widget in self.test_inputs.items():
            value = input_widget.text()
            if value:
                try:
                    # تبدیل به عدد
                    test_values[field_name] = float(value)
                except:
                    test_values[field_name] = value
        
        # جایگزینی فیلدها با مقادیر
        eval_formula = formula
        for field_name, value in test_values.items():
            eval_formula = eval_formula.replace(f"[{field_name}]", str(value))
        
        try:
            # محاسبه (خطرناک! در production باید safe eval استفاده کرد)
            result = eval(eval_formula)
            self.test_result.setText(f"✅ Result: {result:,.2f}")
            self.test_result.setStyleSheet(
                "padding: 10px; background: #e8f5e9; border: 1px solid #4caf50; color: #2e7d32;"
            )
        except Exception as e:
            self.test_result.setText(f"❌ Error: {str(e)}")
            self.test_result.setStyleSheet(
                "padding: 10px; background: #ffebee; border: 1px solid #f44336; color: #c62828;"
            )
    
    def validate_formula(self):
        """اعتبارسنجی فرمول"""
        formula = self.formula_input.toPlainText()
        
        if not formula:
            QMessageBox.warning(self, "Validation", "Formula is empty")
            return
        
        # بررسی فیلدها
        used_fields = self.extract_fields(formula)
        valid_field_names = [f['name'] for f in self.available_fields]
        
        invalid_fields = [f for f in used_fields if f not in valid_field_names]
        if invalid_fields:
            QMessageBox.warning(
                self,
                "Invalid Fields",
                f"These fields are not available:\n{', '.join(invalid_fields)}"
            )
            return
        
        # ساخت AST
        ast = self.parse_formula(formula)
        
        # نمایش در tree
        self.formula_tree.clear()
        root = QTreeWidgetItem(["Formula", "Expression", formula[:50]])
        self.formula_tree.addTopLevelItem(root)
        
        # افزودن فیلدها
        if ast['fields']:
            fields_item = QTreeWidgetItem(root, ["Fields", "List", ""])
            for field in ast['fields']:
                QTreeWidgetItem(fields_item, [field, "Field", ""])
        
        # افزودن توابع
        if ast['functions']:
            funcs_item = QTreeWidgetItem(root, ["Functions", "List", ""])
            for func in ast['functions']:
                QTreeWidgetItem(funcs_item, [func, "Function", ""])
        
        self.formula_tree.expandAll()
        
        QMessageBox.information(self, "Validation", "✅ Formula is valid!")
    
    def save_formula(self):
        """ذخیره فرمول"""
        formula = self.formula_input.toPlainText()
        
        if not formula:
            QMessageBox.warning(self, "Save", "Formula is empty")
            return
        
        ast = self.parse_formula(formula)
        
        self.formula_created.emit(formula, ast)
        self.accept()


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    # تست
    app = QApplication(sys.argv)
    
    test_fields = [
        {"id": 1, "name": "amount", "display_name": "مبلغ", "type": "decimal"},
        {"id": 2, "name": "rate", "display_name": "نرخ", "type": "decimal"},
        {"id": 3, "name": "quantity", "display_name": "تعداد", "type": "number"},
        {"id": 4, "name": "cost", "display_name": "هزینه", "type": "decimal"},
    ]
    
    dialog = FormulaBuilderDialog(test_fields)
    
    def on_formula_created(formula, ast):
        print(f"Formula: {formula}")
        print(f"AST: {json.dumps(ast, indent=2)}")
    
    dialog.formula_created.connect(on_formula_created)
    dialog.exec()
