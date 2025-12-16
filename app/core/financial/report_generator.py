"""
Report Generator - گزارش‌ساز جامع
=================================
تولید گزارش‌های مختلف با فرمت‌های متنوع
"""
from typing import Dict, List, Optional
from datetime import datetime, date
from decimal import Decimal

from app.core.financial.calculation_engine import CalculationEngine


class ReportGenerator:
    """
    گزارش‌ساز
    
    انواع گزارش:
    - جزئیات Label
    - خلاصه Email
    - تحلیل Customer
    - گزارش بازه زمانی
    - گزارش سود/زیان
    """
    
    def __init__(self, calculation_engine: CalculationEngine):
        self.engine = calculation_engine
    
    # ═══════════════════════════════════════════════════════════════
    # گزارش Label
    # ═══════════════════════════════════════════════════════════════
    
    def generate_label_report(self, label: str) -> str:
        """
        گزارش کامل یک Label
        """
        summary = self.engine.calculate_label_summary(label)
        if not summary:
            return f"⚠️ Label '{label}' یافت نشد."
        
        report = []
        report.append("═" * 60)
        report.append("گزارش جامع آکانت")
        report.append("═" * 60)
        report.append("")
        
        # اطلاعات اصلی
        report.append(f"Label: {summary['label']}")
        report.append(f"Email: {summary['email']}")
        report.append(f"تامین‌کننده: {summary['supplier']}")
        report.append(f"وضعیت: {summary['status']}")
        report.append("")
        
        # گلد
        report.append("─" * 60)
        report.append("خرید گلد:")
        report.append("─" * 60)
        report.append(f"مقدار: {summary['gold']['purchased']:.2f} Gold")
        report.append(f"نرخ: {summary['gold']['purchase_rate']:.4f}")
        report.append(f"هزینه کل: ${summary['gold']['cost']:.2f}")
        report.append("")
        
        # سیلور
        report.append("─" * 60)
        report.append("بونوس سیلور:")
        report.append("─" * 60)
        report.append(f"مقدار: {summary['silver']['bonus']:.2f} Silver (رایگان)")
        report.append("")
        
        # فروش‌های گلد
        report.append("─" * 60)
        report.append("فروش‌های گلد:")
        report.append("─" * 60)
        report.append(f"کل فروش: {summary['gold']['sold']:.2f} Gold")
        report.append(f"درآمد: ${summary['gold']['revenue']:.2f}")
        report.append(f"سود: ${summary['gold']['profit']:.2f}")
        report.append(f"نرخ سود: {summary['gold']['profit_pct']:.2f}%")
        report.append(f"مانده: {summary['gold']['remaining']:.2f} Gold")
        report.append("")
        
        # فروش‌های سیلور
        report.append("─" * 60)
        report.append("فروش‌های سیلور:")
        report.append("─" * 60)
        report.append(f"کل فروش: {summary['silver']['sold']:.2f} Silver")
        report.append(f"درآمد: ${summary['silver']['revenue']:.2f}")
        report.append(f"سود: ${summary['silver']['profit']:.2f} (100%)")
        report.append(f"مانده: {summary['silver']['remaining']:.2f} Silver")
        report.append("")
        
        # خلاصه نهایی
        report.append("═" * 60)
        report.append("خلاصه نهایی:")
        report.append("═" * 60)
        report.append(f"کل هزینه: ${summary['total']['cost']:.2f}")
        report.append(f"کل درآمد: ${summary['total']['revenue']:.2f}")
        report.append(f"کل سود: ${summary['total']['profit']:.2f}")
        report.append("")
        report.append(f"تعداد فروش: {summary['stats']['sale_count']}")
        report.append(f"تعداد مشتریان: {summary['stats']['unique_customers']}")
        
        if summary['stats']['last_sale_date']:
            report.append(f"آخرین فروش: {summary['stats']['last_sale_date'].strftime('%Y-%m-%d')}")
        
        report.append("═" * 60)
        
        return "\n".join(report)
    
    # ═══════════════════════════════════════════════════════════════
    # گزارش Email
    # ═══════════════════════════════════════════════════════════════
    
    def generate_email_report(self, email: str) -> str:
        """
        گزارش جامع یک Email (جمع همه Labels)
        """
        summary = self.engine.calculate_email_summary(email)
        if not summary:
            return f"⚠️ Email '{email}' یافت نشد."
        
        report = []
        report.append("═" * 60)
        report.append("گزارش جامع ایمیل")
        report.append("═" * 60)
        report.append("")
        
        # اطلاعات کلی
        report.append(f"Email: {summary['email']}")
        report.append(f"تعداد Labels: {summary['label_count']}")
        report.append(f"Labels: {', '.join(summary['labels'])}")
        report.append("")
        
        # خلاصه گلد
        report.append("─" * 60)
        report.append("خلاصه گلد:")
        report.append("─" * 60)
        report.append(f"کل خرید: {summary['gold']['total_purchased']:.2f} Gold")
        report.append(f"کل فروش: {summary['gold']['total_sold']:.2f} Gold")
        report.append(f"مانده: {summary['gold']['total_remaining']:.2f} Gold")
        report.append(f"هزینه: ${summary['gold']['total_cost']:.2f}")
        report.append(f"درآمد: ${summary['gold']['total_revenue']:.2f}")
        report.append(f"سود: ${summary['gold']['total_profit']:.2f}")
        report.append("")
        
        # خلاصه سیلور
        report.append("─" * 60)
        report.append("خلاصه سیلور:")
        report.append("─" * 60)
        report.append(f"کل بونوس: {summary['silver']['total_bonus']:.2f} Silver")
        report.append(f"کل فروش: {summary['silver']['total_sold']:.2f} Silver")
        report.append(f"مانده: {summary['silver']['total_remaining']:.2f} Silver")
        report.append(f"درآمد: ${summary['silver']['total_revenue']:.2f}")
        report.append(f"سود: ${summary['silver']['total_profit']:.2f} (100%)")
        report.append("")
        
        # جمع کل
        report.append("═" * 60)
        report.append("جمع کل:")
        report.append("═" * 60)
        report.append(f"کل هزینه: ${summary['total']['cost']:.2f}")
        report.append(f"کل درآمد: ${summary['total']['revenue']:.2f}")
        report.append(f"کل سود: ${summary['total']['profit']:.2f}")
        report.append("")
        
        # جدول Labels
        report.append("─" * 60)
        report.append("جزئیات Labels:")
        report.append("─" * 60)
        report.append(f"{'Label':<10} {'گلد خرید':<12} {'گلد فروش':<12} {'سیلور':<10} {'سود':<12}")
        report.append("─" * 60)
        
        for detail in summary['details']:
            label = detail['label']
            gold_purchased = detail['gold']['purchased']
            gold_sold = detail['gold']['sold']
            silver = f"{detail['silver']['bonus']:.0f}→{detail['silver']['sold']:.0f}"
            profit = detail['total']['profit']
            
            report.append(f"{label:<10} {gold_purchased:<12.2f} {gold_sold:<12.2f} {silver:<10} ${profit:<11.2f}")
        
        report.append("═" * 60)
        
        return "\n".join(report)
    
    # ═══════════════════════════════════════════════════════════════
    # گزارش Customer
    # ═══════════════════════════════════════════════════════════════
    
    def generate_customer_report(self, customer_code: str) -> str:
        """
        گزارش خریدهای یک مشتری
        """
        summary = self.engine.calculate_customer_summary(customer_code)
        if not summary:
            return f"⚠️ مشتری '{customer_code}' یافت نشد."
        
        report = []
        report.append("═" * 60)
        report.append(f"گزارش خریدهای مشتری: {summary['customer']}")
        report.append("═" * 60)
        report.append("")
        
        # آمار کلی
        report.append(f"تعداد خریدها: {summary['total_purchases']}")
        report.append(f"کل مبلغ پرداختی: ${summary['total_spent']:.2f}")
        report.append(f"متوسط هر خرید: ${summary['total_spent'] / summary['total_purchases']:.2f}")
        report.append("")
        
        # گلد و سیلور
        report.append("─" * 60)
        report.append("جزئیات خرید:")
        report.append("─" * 60)
        report.append(f"گلد خریداری: {summary['gold']['quantity']:.2f} Gold (${summary['gold']['amount']:.2f})")
        report.append(f"سیلور خریداری: {summary['silver']['quantity']:.2f} Silver (${summary['silver']['amount']:.2f})")
        report.append("")
        
        # Labels
        report.append("─" * 60)
        report.append(f"Labels خریداری شده: {', '.join(summary['labels'])}")
        report.append("")
        
        # تاریخ‌ها
        if summary['first_purchase']:
            report.append(f"اولین خرید: {summary['first_purchase'].strftime('%Y-%m-%d')}")
        if summary['last_purchase']:
            report.append(f"آخرین خرید: {summary['last_purchase'].strftime('%Y-%m-%d')}")
        
        report.append("═" * 60)
        
        return "\n".join(report)
    
    # ═══════════════════════════════════════════════════════════════
    # گزارش خلاصه کل سیستم
    # ═══════════════════════════════════════════════════════════════
    
    def generate_system_summary_report(self) -> str:
        """
        گزارش خلاصه کل سیستم
        """
        summary = self.engine.get_total_system_summary()
        
        report = []
        report.append("═" * 60)
        report.append("گزارش خلاصه کل سیستم")
        report.append("═" * 60)
        report.append("")
        
        # آمار کلی
        report.append(f"تعداد کل آکانت‌ها: {summary['total_accounts']}")
        report.append("")
        
        # گلد
        report.append("─" * 60)
        report.append("گلد:")
        report.append("─" * 60)
        report.append(f"کل خرید: {summary['gold']['total_purchased']:.2f} Gold")
        report.append(f"کل فروش: {summary['gold']['total_sold']:.2f} Gold")
        report.append(f"مانده: {summary['gold']['total_remaining']:.2f} Gold")
        report.append(f"هزینه: ${summary['gold']['total_cost']:.2f}")
        report.append(f"درآمد: ${summary['gold']['total_revenue']:.2f}")
        report.append(f"سود: ${summary['gold']['total_profit']:.2f}")
        report.append("")
        
        # سیلور
        report.append("─" * 60)
        report.append("سیلور:")
        report.append("─" * 60)
        report.append(f"کل بونوس: {summary['silver']['total_bonus']:.2f} Silver")
        report.append(f"کل فروش: {summary['silver']['total_sold']:.2f} Silver")
        report.append(f"مانده: {summary['silver']['total_remaining']:.2f} Silver")
        report.append(f"درآمد: ${summary['silver']['total_revenue']:.2f}")
        report.append(f"سود: ${summary['silver']['total_profit']:.2f} (100%)")
        report.append("")
        
        # جمع کل
        report.append("═" * 60)
        report.append("جمع کل:")
        report.append("═" * 60)
        report.append(f"کل هزینه: ${summary['total']['cost']:.2f}")
        report.append(f"کل درآمد: ${summary['total']['revenue']:.2f}")
        report.append(f"کل سود: ${summary['total']['profit']:.2f}")
        
        if summary['total']['cost'] > 0:
            profit_pct = (summary['total']['profit'] / summary['total']['cost']) * 100
            report.append(f"نرخ سود: {profit_pct:.2f}%")
        
        report.append("═" * 60)
        
        return "\n".join(report)
    
    # ═══════════════════════════════════════════════════════════════
    # گزارش جدولی (برای Excel)
    # ═══════════════════════════════════════════════════════════════
    
    def generate_table_report(self) -> List[Dict]:
        """
        گزارش به صورت لیست (برای Export به Excel)
        
        Returns:
            [
                {
                    'Label': 'g450',
                    'Email': 'test@example.com',
                    'Gold_Purchased': 100,
                    'Gold_Sold': 30,
                    'Gold_Remaining': 70,
                    'Silver_Bonus': 20,
                    'Silver_Sold': 10,
                    'Silver_Remaining': 10,
                    'Total_Cost': 300.00,
                    'Total_Revenue': 179.00,
                    'Total_Profit': 89.00
                },
                ...
            ]
        """
        summaries = self.engine.get_all_labels_summary()
        
        table = []
        for s in summaries:
            row = {
                'Label': s['label'],
                'Email': s['email'],
                'Supplier': s['supplier'],
                'Status': s['status'],
                
                # گلد
                'Gold_Purchased': float(s['gold']['purchased']),
                'Gold_Sold': float(s['gold']['sold']),
                'Gold_Remaining': float(s['gold']['remaining']),
                'Gold_Cost': float(s['gold']['cost']),
                'Gold_Revenue': float(s['gold']['revenue']),
                'Gold_Profit': float(s['gold']['profit']),
                'Gold_Profit_Pct': float(s['gold']['profit_pct']),
                
                # سیلور
                'Silver_Bonus': float(s['silver']['bonus']),
                'Silver_Sold': float(s['silver']['sold']),
                'Silver_Remaining': float(s['silver']['remaining']),
                'Silver_Revenue': float(s['silver']['revenue']),
                'Silver_Profit': float(s['silver']['profit']),
                
                # جمع
                'Total_Cost': float(s['total']['cost']),
                'Total_Revenue': float(s['total']['revenue']),
                'Total_Profit': float(s['total']['profit']),
                
                # آمار
                'Sale_Count': s['stats']['sale_count'],
                'Unique_Customers': s['stats']['unique_customers']
            }
            
            if s['stats']['last_sale_date']:
                row['Last_Sale_Date'] = s['stats']['last_sale_date'].strftime('%Y-%m-%d')
            
            table.append(row)
        
        return table
    
    # ═══════════════════════════════════════════════════════════════
    # Export به Excel
    # ═══════════════════════════════════════════════════════════════
    
    def export_to_excel(self, filepath: str):
        """
        Export به Excel
        (نیاز به pandas)
        """
        try:
            import pandas as pd
            
            table = self.generate_table_report()
            df = pd.DataFrame(table)
            
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # شیت اصلی
                df.to_excel(writer, sheet_name='Summary', index=False)
                
                # فرمت‌بندی ستون‌ها
                worksheet = writer.sheets['Summary']
                
                # عرض ستون‌ها
                for column in worksheet.columns:
                    max_length = max(len(str(cell.value)) for cell in column)
                    worksheet.column_dimensions[column[0].column_letter].width = min(max_length + 2, 50)
            
            return True, f"✅ فایل Excel ذخیره شد: {filepath}"
            
        except ImportError:
            return False, "❌ pandas نصب نیست. برای Export به Excel، pandas را نصب کنید."
        except Exception as e:
            return False, f"❌ خطا در ذخیره Excel: {str(e)}"
