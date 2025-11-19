"""
Data Analyzer - تحلیلگر هوشمند داده‌ها
تشخیص نوع sheet (خرید/فروش/تسویه) و شناسایی فیلدها
"""
from typing import Dict, List, Optional, Literal
from dataclasses import dataclass
from app.models.sheet_config import SheetConfig
from app.models.sales_data import SalesData
from app.core.database import SessionLocal
from app.core.logger import app_logger


SheetType = Literal['purchase', 'sale', 'payment', 'unknown']


@dataclass
class FieldMapping:
    """نقشه فیلدهای شناسایی شده"""
    # فیلدهای مشترک
    label: Optional[str] = None  # Label/شناسه آکانت
    date: Optional[str] = None  # تاریخ
    
    # فیلدهای فروش
    customer: Optional[str] = None  # نام مشتری
    rate: Optional[str] = None  # نرخ فروش
    price: Optional[str] = None  # قیمت نهایی
    gold_amount: Optional[str] = None  # مقدار Gold فروخته شده
    silver_amount: Optional[str] = None  # مقدار Silver فروخته شده
    
    # فیلدهای خرید
    supplier: Optional[str] = None  # نام supplier/منبع
    purchase_price: Optional[str] = None  # قیمت خرید
    initial_gold: Optional[str] = None  # موجودی اولیه Gold
    initial_silver: Optional[str] = None  # موجودی اولیه Silver
    
    # فیلدهای تسویه
    payment_amount: Optional[str] = None  # مبلغ پرداختی
    payment_method: Optional[str] = None  # روش پرداخت
    currency: Optional[str] = None  # واحد پول


@dataclass
class SheetAnalysis:
    """نتیجه تحلیل یک sheet"""
    sheet_id: int
    sheet_name: str
    sheet_type: SheetType
    confidence: float  # درصد اطمینان (0-1)
    field_mapping: FieldMapping
    sample_count: int
    total_records: int
    reason: str  # دلیل تشخیص


class DataAnalyzer:
    """
    تحلیلگر هوشمند داده‌ها
    """
    
    # کلمات کلیدی برای تشخیص نوع sheet
    SALE_KEYWORDS = ['customer', 'buyer', 'مشتری', 'خریدار', 'sold', 'sale', 'فروش', 'rate', 'نرخ']
    PURCHASE_KEYWORDS = ['supplier', 'vendor', 'تامین', 'خرید', 'purchase', 'buy', 'منبع', 'source']
    PAYMENT_KEYWORDS = ['payment', 'پرداخت', 'تسویه', 'settle', 'واریز', 'deposit']
    
    # کلمات کلیدی برای شناسایی فیلدها
    LABEL_KEYWORDS = ['label', 'لیبل', 'شناسه', 'id', 'code', 'کد']
    CUSTOMER_KEYWORDS = ['customer', 'مشتری', 'buyer', 'خریدار', 'client']
    RATE_KEYWORDS = ['rate', 'نرخ', 'price per unit', 'قیمت واحد']
    PRICE_KEYWORDS = ['price', 'قیمت', 'amount', 'مبلغ', 'final', 'نهایی', 'total']
    DATE_KEYWORDS = ['date', 'تاریخ', 'time', 'زمان']
    
    def __init__(self):
        self.logger = app_logger
    
    def analyze_all_sheets(self) -> List[SheetAnalysis]:
        """تحلیل تمام sheets"""
        db = SessionLocal()
        try:
            sheets = db.query(SheetConfig).filter(SheetConfig.is_active == True).all()
            results = []
            
            for sheet in sheets:
                analysis = self.analyze_sheet(sheet, db)
                results.append(analysis)
                self.logger.info(f"Sheet '{sheet.name}': Type={analysis.sheet_type}, Confidence={analysis.confidence:.2%}")
            
            return results
        finally:
            db.close()
    
    def analyze_sheet(self, sheet: SheetConfig, db) -> SheetAnalysis:
        """تحلیل یک sheet"""
        # گرفتن نمونه داده‌ها
        samples = db.query(SalesData).filter(
            SalesData.sheet_config_id == sheet.id
        ).limit(10).all()
        
        total_records = db.query(SalesData).filter(
            SalesData.sheet_config_id == sheet.id
        ).count()
        
        if not samples or total_records == 0:
            return SheetAnalysis(
                sheet_id=sheet.id,
                sheet_name=sheet.name,
                sheet_type='unknown',
                confidence=0.0,
                field_mapping=FieldMapping(),
                sample_count=0,
                total_records=0,
                reason="No data found"
            )
        
        # استخراج فیلدهای موجود
        all_fields = set()
        for sample in samples:
            if sample.data:
                all_fields.update(sample.data.keys())
        
        # تشخیص نوع sheet
        sheet_type, confidence, reason = self._detect_sheet_type(
            sheet.name, 
            sheet.worksheet_name or "", 
            all_fields
        )
        
        # شناسایی فیلدها
        field_mapping = self._map_fields(all_fields, sheet_type)
        
        return SheetAnalysis(
            sheet_id=sheet.id,
            sheet_name=sheet.name,
            sheet_type=sheet_type,
            confidence=confidence,
            field_mapping=field_mapping,
            sample_count=len(samples),
            total_records=total_records,
            reason=reason
        )
    
    def _detect_sheet_type(self, sheet_name: str, worksheet_name: str, fields: set) -> tuple:
        """تشخیص نوع sheet"""
        text = f"{sheet_name} {worksheet_name} {' '.join(fields)}".lower()
        
        scores = {
            'sale': 0,
            'purchase': 0,
            'payment': 0
        }
        
        # امتیازدهی بر اساس کلمات کلیدی
        for keyword in self.SALE_KEYWORDS:
            if keyword in text:
                scores['sale'] += 1
        
        for keyword in self.PURCHASE_KEYWORDS:
            if keyword in text:
                scores['purchase'] += 1
        
        for keyword in self.PAYMENT_KEYWORDS:
            if keyword in text:
                scores['payment'] += 1
        
        # بررسی ترکیب فیلدها
        has_customer = any(k in text for k in self.CUSTOMER_KEYWORDS)
        has_rate = any(k in text for k in self.RATE_KEYWORDS)
        has_label = any(k in text for k in self.LABEL_KEYWORDS)
        
        if has_customer and has_rate and has_label:
            scores['sale'] += 3
        
        # تشخیص نهایی
        max_score = max(scores.values())
        if max_score == 0:
            return 'unknown', 0.0, "No matching keywords found"
        
        sheet_type = max(scores, key=scores.get)
        confidence = max_score / (sum(scores.values()) + 1)
        
        reasons = []
        if scores['sale'] > 0:
            reasons.append(f"Sale indicators: {scores['sale']}")
        if scores['purchase'] > 0:
            reasons.append(f"Purchase indicators: {scores['purchase']}")
        if scores['payment'] > 0:
            reasons.append(f"Payment indicators: {scores['payment']}")
        
        return sheet_type, confidence, "; ".join(reasons)
    
    def _map_fields(self, fields: set, sheet_type: SheetType) -> FieldMapping:
        """شناسایی و نقشه‌برداری فیلدها"""
        mapping = FieldMapping()
        fields_lower = {f.lower(): f for f in fields}
        
        # شناسایی Label
        for keyword in self.LABEL_KEYWORDS:
            for field_lower, field_original in fields_lower.items():
                if keyword in field_lower:
                    mapping.label = field_original
                    break
            if mapping.label:
                break
        
        # شناسایی تاریخ
        for keyword in self.DATE_KEYWORDS:
            for field_lower, field_original in fields_lower.items():
                if keyword in field_lower:
                    mapping.date = field_original
                    break
            if mapping.date:
                break
        
        if sheet_type == 'sale':
            # شناسایی مشتری
            for keyword in self.CUSTOMER_KEYWORDS:
                for field_lower, field_original in fields_lower.items():
                    if keyword in field_lower:
                        mapping.customer = field_original
                        break
                if mapping.customer:
                    break
            
            # شناسایی نرخ
            for keyword in self.RATE_KEYWORDS:
                for field_lower, field_original in fields_lower.items():
                    if keyword in field_lower and 'sale' in field_lower:
                        mapping.rate = field_original
                        break
                if mapping.rate:
                    break
            
            # شناسایی قیمت
            for keyword in self.PRICE_KEYWORDS:
                for field_lower, field_original in fields_lower.items():
                    if keyword in field_lower and ('final' in field_lower or 'sale' in field_lower):
                        mapping.price = field_original
                        break
                if mapping.price:
                    break
        
        return mapping
    
    def get_sheet_config_by_type(self, sheet_type: SheetType) -> List[int]:
        """دریافت ID های sheets بر اساس نوع"""
        analyses = self.analyze_all_sheets()
        return [a.sheet_id for a in analyses if a.sheet_type == sheet_type and a.confidence > 0.5]
    
    def print_analysis_report(self):
        """چاپ گزارش کامل تحلیل"""
        analyses = self.analyze_all_sheets()
        
        print("\n" + "="*80)
        print("DATA ANALYSIS REPORT")
        print("="*80)
        
        for analysis in analyses:
            print(f"\nSheet: {analysis.sheet_name}")
            print(f"  Type: {analysis.sheet_type.upper()} (Confidence: {analysis.confidence:.1%})")
            print(f"  Records: {analysis.total_records:,}")
            print(f"  Reason: {analysis.reason}")
            
            if analysis.field_mapping.label:
                print(f"  Field Mappings:")
                for field, value in vars(analysis.field_mapping).items():
                    if value:
                        print(f"    - {field}: '{value}'")
            
            print("  " + "-"*76)
        
        # خلاصه
        print(f"\nSUMMARY:")
        print(f"  Total Sheets: {len(analyses)}")
        print(f"  Sale Sheets: {sum(1 for a in analyses if a.sheet_type == 'sale')}")
        print(f"  Purchase Sheets: {sum(1 for a in analyses if a.sheet_type == 'purchase')}")
        print(f"  Payment Sheets: {sum(1 for a in analyses if a.sheet_type == 'payment')}")
        print(f"  Unknown Sheets: {sum(1 for a in analyses if a.sheet_type == 'unknown')}")
        print("="*80 + "\n")


if __name__ == "__main__":
    analyzer = DataAnalyzer()
    analyzer.print_analysis_report()
