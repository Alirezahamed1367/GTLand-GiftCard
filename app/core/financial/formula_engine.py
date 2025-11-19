"""
FormulaEngine: موتور محاسبه فرمول‌ها
====================================

این کلاس فرمول‌های ساخته شده در Formula Builder رو اجرا می‌کنه
"""

import re
import ast
import operator
from typing import Dict, Any, List, Union, Optional
from decimal import Decimal
from datetime import datetime, date


class FormulaEngine:
    """
    موتور محاسبه فرمول‌های Excel-like
    
    مثال:
        fe = FormulaEngine()
        result = fe.evaluate(
            formula="([amount] * [rate]) / 100",
            context={"amount": 1500, "rate": 84.5}
        )
        # result = 1267.5
    """
    
    # عملگرها
    OPERATORS = {
        '+': operator.add,
        '-': operator.sub,
        '*': operator.mul,
        '/': operator.truediv,
        '//': operator.floordiv,
        '%': operator.mod,
        '**': operator.pow,
        '==': operator.eq,
        '!=': operator.ne,
        '>': operator.gt,
        '>=': operator.ge,
        '<': operator.lt,
        '<=': operator.le,
        'AND': operator.and_,
        'OR': operator.or_,
    }
    
    def __init__(self):
        """Initialize formula engine"""
        pass
    
    def evaluate(
        self,
        formula: str,
        context: Dict[str, Any],
        safe_mode: bool = True
    ) -> Any:
        """
        محاسبه یک فرمول
        
        Args:
            formula: متن فرمول (مثلاً "([amount] * [rate]) / 100")
            context: مقادیر فیلدها (مثلاً {"amount": 1500, "rate": 84.5})
            safe_mode: اگر True باشه از eval استفاده نمی‌کنه (امن‌تر اما محدودتر)
        
        Returns:
            نتیجه محاسبه
        
        Raises:
            ValueError: اگر فرمول نامعتبر باشه
        """
        if not formula or not formula.strip():
            return None
        
        # جایگزینی فیلدها با مقادیر
        formula_eval = formula
        for field_name, value in context.items():
            # [field_name] رو با مقدار جایگزین می‌کنیم
            pattern = r'\[' + re.escape(field_name) + r'\]'
            
            # تبدیل مقدار به رشته مناسب
            if value is None:
                value_str = "None"
            elif isinstance(value, str):
                value_str = f'"{value}"'
            elif isinstance(value, (date, datetime)):
                value_str = f'"{value.isoformat()}"'
            elif isinstance(value, Decimal):
                value_str = str(float(value))
            else:
                value_str = str(value)
            
            formula_eval = re.sub(pattern, value_str, formula_eval)
        
        if safe_mode:
            # استفاده از SafeEvaluator
            return self._safe_evaluate(formula_eval)
        else:
            # استفاده از eval (ناامن اما قدرتمند)
            try:
                result = eval(formula_eval, {"__builtins__": {}}, self._get_functions())
                return result
            except Exception as e:
                raise ValueError(f"Formula evaluation error: {e}")
    
    def _safe_evaluate(self, formula: str) -> Any:
        """
        محاسبه امن (بدون eval)
        
        NOTE: این فقط عملیات‌های ساده رو پشتیبانی می‌کنه
        برای عملیات پیچیده‌تر باید یک AST parser کامل بسازیم
        """
        try:
            # Parse formula to AST
            tree = ast.parse(formula, mode='eval')
            return self._eval_node(tree.body)
        except Exception as e:
            raise ValueError(f"Safe evaluation error: {e}")
    
    def _eval_node(self, node: ast.AST) -> Any:
        """ارزیابی یک node از AST"""
        if isinstance(node, ast.Num):  # عدد
            return node.n
        
        elif isinstance(node, ast.Str):  # رشته
            return node.s
        
        elif isinstance(node, ast.NameConstant):  # True, False, None
            return node.value
        
        elif isinstance(node, ast.UnaryOp):  # -x, +x
            operand = self._eval_node(node.operand)
            if isinstance(node.op, ast.UAdd):
                return +operand
            elif isinstance(node.op, ast.USub):
                return -operand
            elif isinstance(node.op, ast.Not):
                return not operand
        
        elif isinstance(node, ast.BinOp):  # x + y
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            
            if isinstance(node.op, ast.Add):
                return left + right
            elif isinstance(node.op, ast.Sub):
                return left - right
            elif isinstance(node.op, ast.Mult):
                return left * right
            elif isinstance(node.op, ast.Div):
                return left / right
            elif isinstance(node.op, ast.FloorDiv):
                return left // right
            elif isinstance(node.op, ast.Mod):
                return left % right
            elif isinstance(node.op, ast.Pow):
                return left ** right
        
        elif isinstance(node, ast.Compare):  # x > y
            left = self._eval_node(node.left)
            
            for op, comparator in zip(node.ops, node.comparators):
                right = self._eval_node(comparator)
                
                if isinstance(op, ast.Eq):
                    result = left == right
                elif isinstance(op, ast.NotEq):
                    result = left != right
                elif isinstance(op, ast.Lt):
                    result = left < right
                elif isinstance(op, ast.LtE):
                    result = left <= right
                elif isinstance(op, ast.Gt):
                    result = left > right
                elif isinstance(op, ast.GtE):
                    result = left >= right
                else:
                    raise ValueError(f"Unsupported comparison: {op}")
                
                if not result:
                    return False
                left = right
            
            return True
        
        elif isinstance(node, ast.Call):  # function(args)
            func_name = node.func.id if isinstance(node.func, ast.Name) else None
            args = [self._eval_node(arg) for arg in node.args]
            
            if func_name:
                func = self._get_function(func_name)
                if func:
                    return func(*args)
            
            raise ValueError(f"Unknown function: {func_name}")
        
        else:
            raise ValueError(f"Unsupported AST node: {type(node)}")
    
    def _get_functions(self) -> Dict[str, callable]:
        """توابع قابل استفاده در فرمول"""
        return {
            'SUM': lambda *args: sum(args),
            'AVG': lambda *args: sum(args) / len(args) if args else 0,
            'COUNT': lambda *args: len(args),
            'MIN': lambda *args: min(args) if args else None,
            'MAX': lambda *args: max(args) if args else None,
            'IF': lambda condition, true_val, false_val: true_val if condition else false_val,
            'ROUND': lambda value, digits=0: round(value, int(digits)),
            'ABS': abs,
            'FLOOR': lambda x: int(x),
            'CEIL': lambda x: int(x) + (1 if x > int(x) else 0),
            'POW': pow,
            'SQRT': lambda x: x ** 0.5,
        }
    
    def _get_function(self, name: str) -> Optional[callable]:
        """دریافت یک تابع"""
        return self._get_functions().get(name.upper())
    
    def validate(self, formula: str, available_fields: List[str]) -> Dict[str, Any]:
        """
        اعتبارسنجی یک فرمول
        
        Args:
            formula: متن فرمول
            available_fields: لیست فیلدهای موجود
        
        Returns:
            {
                "valid": True/False,
                "errors": [...],
                "warnings": [...],
                "fields_used": [...],
                "functions_used": [...]
            }
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "fields_used": [],
            "functions_used": []
        }
        
        if not formula or not formula.strip():
            result["valid"] = False
            result["errors"].append("Formula is empty")
            return result
        
        # استخراج فیلدها
        fields_in_formula = re.findall(r'\[([^\]]+)\]', formula)
        result["fields_used"] = fields_in_formula
        
        # بررسی فیلدهای ناموجود
        for field in fields_in_formula:
            if field not in available_fields:
                result["errors"].append(f"Field not found: {field}")
                result["valid"] = False
        
        # استخراج توابع
        functions_in_formula = re.findall(r'([A-Z]+)\(', formula)
        result["functions_used"] = functions_in_formula
        
        # بررسی توابع ناشناخته
        known_functions = self._get_functions().keys()
        for func in functions_in_formula:
            if func.upper() not in known_functions:
                result["errors"].append(f"Unknown function: {func}")
                result["valid"] = False
        
        # بررسی syntax
        try:
            # جایگزینی فیلدها با صفر برای تست
            test_formula = formula
            for field in fields_in_formula:
                pattern = r'\[' + re.escape(field) + r'\]'
                test_formula = re.sub(pattern, '0', test_formula)
            
            # تست با eval
            ast.parse(test_formula, mode='eval')
        except SyntaxError as e:
            result["errors"].append(f"Syntax error: {e}")
            result["valid"] = False
        
        return result
    
    def get_dependencies(self, formula: str) -> List[str]:
        """
        دریافت لیست فیلدهای استفاده شده در فرمول
        
        Args:
            formula: متن فرمول
        
        Returns:
            لیست نام فیلدها
        """
        return re.findall(r'\[([^\]]+)\]', formula)
    
    def build_ast(self, formula: str) -> Dict[str, Any]:
        """
        ساخت AST از فرمول
        
        Returns:
            {
                "type": "expression",
                "formula": "...",
                "fields": [...],
                "functions": [...],
                "operators": [...]
            }
        """
        fields = self.get_dependencies(formula)
        functions = re.findall(r'([A-Z]+)\(', formula)
        
        # استخراج عملگرها
        operators = []
        for op in ['+', '-', '*', '/', '>', '<', '==', '!=']:
            if op in formula:
                operators.append(op)
        
        return {
            "type": "expression",
            "formula": formula,
            "fields": fields,
            "functions": functions,
            "operators": operators
        }


class AggregationEngine:
    """
    موتور Aggregation برای گزارش‌ها
    
    مثال:
        ae = AggregationEngine()
        result = ae.aggregate(
            data=[
                {"customer": "Ali", "amount": 1000},
                {"customer": "Ali", "amount": 2000},
                {"customer": "Sara", "amount": 1500},
            ],
            group_by=["customer"],
            aggregations=[
                {"field": "amount", "function": "sum", "alias": "total"}
            ]
        )
        # result = [
        #     {"customer": "Ali", "total": 3000},
        #     {"customer": "Sara", "total": 1500}
        # ]
    """
    
    def aggregate(
        self,
        data: List[Dict[str, Any]],
        group_by: List[str],
        aggregations: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        انجام aggregation روی داده‌ها
        
        Args:
            data: لیست رکوردها
            group_by: لیست فیلدها برای گروه‌بندی
            aggregations: لیست aggregation ها [{"field": "amount", "function": "sum", "alias": "total"}]
        
        Returns:
            لیست رکوردهای aggregate شده
        """
        if not data:
            return []
        
        if not group_by:
            # اگر group by نداریم، روی کل داده aggregate می‌کنیم
            return [self._aggregate_group(data, aggregations)]
        
        # گروه‌بندی
        groups = {}
        for row in data:
            # ساخت key برای group
            group_key = tuple(row.get(field) for field in group_by)
            
            if group_key not in groups:
                groups[group_key] = []
            
            groups[group_key].append(row)
        
        # Aggregation روی هر group
        results = []
        for group_key, group_rows in groups.items():
            result_row = {}
            
            # اضافه کردن فیلدهای group by
            for i, field in enumerate(group_by):
                result_row[field] = group_key[i]
            
            # Aggregation
            agg_results = self._aggregate_group(group_rows, aggregations)
            result_row.update(agg_results)
            
            results.append(result_row)
        
        return results
    
    def _aggregate_group(
        self,
        rows: List[Dict[str, Any]],
        aggregations: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Aggregation روی یک group"""
        result = {}
        
        for agg in aggregations:
            field = agg["field"]
            function = agg["function"].lower()
            alias = agg.get("alias", f"{function}_{field}")
            
            # استخراج مقادیر
            values = [row.get(field) for row in rows if row.get(field) is not None]
            
            # محاسبه
            if function == "sum":
                result[alias] = sum(values)
            elif function == "avg":
                result[alias] = sum(values) / len(values) if values else 0
            elif function == "count":
                result[alias] = len(rows)
            elif function == "min":
                result[alias] = min(values) if values else None
            elif function == "max":
                result[alias] = max(values) if values else None
            elif function == "first":
                result[alias] = values[0] if values else None
            elif function == "last":
                result[alias] = values[-1] if values else None
            elif function == "distinct_count":
                result[alias] = len(set(values))
            else:
                result[alias] = None
        
        return result


if __name__ == "__main__":
    # تست FormulaEngine
    fe = FormulaEngine()
    
    # تست 1: فرمول ساده
    formula1 = "([amount] * [rate]) / 100"
    context1 = {"amount": 1500, "rate": 84.5}
    result1 = fe.evaluate(formula1, context1)
    print(f"Formula: {formula1}")
    print(f"Context: {context1}")
    print(f"Result: {result1}")  # 1267.5
    print()
    
    # تست 2: با تابع
    formula2 = "ROUND(([amount] * [rate]) / 100, 2)"
    result2 = fe.evaluate(formula2, context1)
    print(f"Formula: {formula2}")
    print(f"Result: {result2}")  # 1267.5
    print()
    
    # تست 3: شرط
    formula3 = "IF([amount] > 1000, [amount] * 0.9, [amount])"
    result3 = fe.evaluate(formula3, context1)
    print(f"Formula: {formula3}")
    print(f"Result: {result3}")  # 1350.0
    print()
    
    # تست 4: Validation
    available_fields = ["amount", "rate", "quantity"]
    formula4 = "([amount] * [rate]) / [unknown_field]"
    validation = fe.validate(formula4, available_fields)
    print(f"Formula: {formula4}")
    print(f"Validation: {validation}")
    print()
    
    # تست AggregationEngine
    ae = AggregationEngine()
    
    data = [
        {"customer": "Ali", "amount": 1000, "quantity": 2},
        {"customer": "Ali", "amount": 2000, "quantity": 3},
        {"customer": "Sara", "amount": 1500, "quantity": 1},
        {"customer": "Sara", "amount": 500, "quantity": 1},
    ]
    
    result = ae.aggregate(
        data=data,
        group_by=["customer"],
        aggregations=[
            {"field": "amount", "function": "sum", "alias": "total_amount"},
            {"field": "amount", "function": "count", "alias": "transaction_count"},
            {"field": "quantity", "function": "sum", "alias": "total_quantity"},
        ]
    )
    
    print("Aggregation result:")
    for row in result:
        print(row)
