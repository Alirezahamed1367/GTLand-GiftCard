# راهنمای کامل رویه اجرایی سیستم Dynamic Field Mapping

## 📋 فهرست مطالب
1. [مقدمه](#مقدمه)
2. [نصب و راه‌اندازی](#نصب-و-راه‌اندازی)
3. [مراحل استفاده](#مراحل-استفاده)
4. [مثال عملی کامل](#مثال-عملی-کامل)
5. [نتایج و گزارش‌ها](#نتایج-و-گزارش‌ها)

---

## 🎯 مقدمه

سیستم **Dynamic Field Mapping** به شما اجازه می‌دهد تا داده‌های خود را از Google Sheets یا هر منبع دیگری Import کرده و **خودتان نقش هر ستون را تعیین کنید**.

### مزایا:
- ✅ **انعطاف کامل**: نیازی به تغییر کد نیست - هر ستون را خودتان تعریف می‌کنید
- ✅ **پشتیبانی از چندین نوع شیت**: خرید، فروش، بونوس
- ✅ **محاسبات خودکار**: سود/زیان، موجودی، Profit Margin
- ✅ **گزارش‌های پیشرفته**: Label، Platform، Customer، Custom
- ✅ **Discrepancy Checking**: مقایسه سود محاسبه شده با گزارش پرسنل

---

## ⚙️ نصب و راه‌اندازی

### 1. نصب وابستگی‌ها
```bash
pip install sqlalchemy pandas openpyxl
```

### 2. ایجاد جداول
```bash
python migrate_to_dynamic_system.py
```

**خروجی موفق:**
```
✅ مایگریشن با موفقیت تکمیل شد!
📊 وضعیت جداول:
  • SheetImport: ذخیره شیت‌های Import شده
  • RawData: داده‌های خام JSON
  • FieldMapping: نقش هر ستون (تعریف شده توسط کاربر)
  • Platform: پلتفرم‌های فروش
  • DiscrepancyReport: گزارش مغایرت‌های سود
  • CustomReport: گزارش‌های سفارشی کاربر
```

---

## 📝 مراحل استفاده

## مرحله 1️⃣: Import داده از Google Sheets (یا منبع دیگر)

### فرض: داده‌های خرید شما در Google Sheets به این شکل است:

| Label | Email              | GOLD | Cost   | Free Silver | Supplier   | Date       |
|-------|-------------------|------|--------|-------------|------------|------------|
| A1054 | test1@gmail.com   | 1000 | 450000 | 100         | Supplier A | 2024-01-15 |
| A1055 | test2@gmail.com   | 2000 | 900000 | 200         | Supplier B | 2024-01-16 |
| G3200 | test3@gmail.com   | 1500 | 675000 | 150         | Supplier C | 2024-01-17 |

### کد Python:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.financial import DataImporter
from app.models.financial import SheetType

# اتصال به دیتابیس
DATABASE_URL = "sqlite:///data/financial/gt_financial.db"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# ایجاد Importer
importer = DataImporter(session)

# Import از Google Sheet
success, message, sheet_import_id = importer.import_from_google_sheet(
    sheet_url="https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID",
    worksheet_name="Sheet1",
    sheet_name="Purchase January 2024",
    sheet_type=SheetType.PURCHASE,
    platform=None,  # برای شیت خرید null است
    skip_header=True  # سطر اول هدر است
)

print(message)
print(f"SheetImport ID: {sheet_import_id}")
```

### ✅ خروجی:
```
✅ Import موفق: 3 سطر از 'Sheet1' ذخیره شد!
SheetImport ID: 1
```

### 📊 چه اتفاقی افتاد؟
1. **SheetImport** ایجاد شد با ID=1
   - نام: "Purchase January 2024"
   - نوع: PURCHASE
   - تعداد سطرها: 3

2. **3 رکورد RawData** ذخیره شد:
   ```json
   {
     "Label": "A1054",
     "Email": "test1@gmail.com",
     "GOLD": "1000",
     "Cost": "450000",
     "Free Silver": "100",
     "Supplier": "Supplier A",
     "Date": "2024-01-15"
   }
   ```

---

## مرحله 2️⃣: تعریف Field Mapping

حالا باید به سیستم بگویید که هر ستون چه نقشی دارد.

### کد Python:
```python
from app.models.financial import FieldMapping, TargetField, DataType

# تعریف Mappings
mappings = [
    FieldMapping(
        sheet_import_id=1,
        source_column="Label",
        target_field=TargetField.ACCOUNT_ID,
        data_type=DataType.TEXT,
        is_required=True
    ),
    FieldMapping(
        sheet_import_id=1,
        source_column="Email",
        target_field=TargetField.EMAIL,
        data_type=DataType.TEXT,
        is_required=False
    ),
    FieldMapping(
        sheet_import_id=1,
        source_column="GOLD",
        target_field=TargetField.GOLD_QUANTITY,
        data_type=DataType.DECIMAL,
        is_required=True
    ),
    FieldMapping(
        sheet_import_id=1,
        source_column="Cost",
        target_field=TargetField.PURCHASE_COST,
        data_type=DataType.DECIMAL,
        is_required=True
    ),
    FieldMapping(
        sheet_import_id=1,
        source_column="Free Silver",
        target_field=TargetField.SILVER_BONUS,
        data_type=DataType.DECIMAL,
        is_required=False
    ),
    FieldMapping(
        sheet_import_id=1,
        source_column="Supplier",
        target_field=TargetField.SUPPLIER,
        data_type=DataType.TEXT,
        is_required=False
    ),
    FieldMapping(
        sheet_import_id=1,
        source_column="Date",
        target_field=TargetField.PURCHASE_DATE,
        data_type=DataType.DATE,
        is_required=False
    ),
]

for mapping in mappings:
    session.add(mapping)

session.commit()
print("✅ Field Mappings ذخیره شد!")
```

### ✅ خروجی:
```
✅ Field Mappings ذخیره شد!

🗺️ تعریف 7 mapping:
   ✅ 'Label' → account_id (text)
   ➖ 'Email' → email (text)
   ✅ 'GOLD' → gold_quantity (decimal)
   ✅ 'Cost' → purchase_cost (decimal)
   ➖ 'Free Silver' → silver_bonus (decimal)
   ➖ 'Supplier' → supplier (text)
   ➖ 'Date' → purchase_date (date)
```

### 📊 چه اتفاقی افتاد؟
- **7 رکورد FieldMapping** ایجاد شد که هرکدام نقش یک ستون را مشخص می‌کند
- ✅ = Required (اجباری)
- ➖ = Optional (اختیاری)

---

## مرحله 3️⃣: پردازش داده

حالا داده‌های خام را بر اساس Mapping پردازش می‌کنیم.

### کد Python:
```python
from app.core.financial import DynamicDataProcessor

processor = DynamicDataProcessor(session)

stats = processor.process_sheet(sheet_import_id=1)

print(f"✅ پردازش موفق!")
print(f"📊 آمار:")
print(f"   📦 کل سطرها: {stats['total']}")
print(f"   ✅ پردازش شده: {stats['processed']}")
print(f"   ⚠️ خطاها: {stats['errors']}")
```

### ✅ خروجی:
```
✅ پردازش موفق!

📊 آمار پردازش:
   📦 کل سطرها: 3
   ✅ پردازش شده: 3
   ⚠️ خطاها: 0

📋 Accountهای ایجاد شده:
   • A1054: Gold=1000, Silver=100, Email=test1@gmail.com
   • A1055: Gold=2000, Silver=200, Email=test2@gmail.com
   • G3200: Gold=1500, Silver=150, Email=test3@gmail.com
```

### 📊 چه اتفاقی افتاد؟

1. **3 Account ایجاد شد** در جدول `accounts`:
   ```
   label=A1054, email=test1@gmail.com, supplier=Supplier A
   label=A1055, email=test2@gmail.com, supplier=Supplier B
   label=G3200, email=test3@gmail.com, supplier=Supplier C
   ```

2. **3 AccountGold ایجاد شد** در جدول `account_gold`:
   ```
   label=A1054, gold_quantity=1000, purchase_cost=450000
   label=A1055, gold_quantity=2000, purchase_cost=900000
   label=G3200, gold_quantity=1500, purchase_cost=675000
   ```

3. **3 AccountSilver ایجاد شد** در جدول `account_silver`:
   ```
   label=A1054, silver_quantity=100
   label=A1055, silver_quantity=200
   label=G3200, silver_quantity=150
   ```

4. **RawData رکوردها** به عنوان `processed=True` علامت‌گذاری شدند

---

## مرحله 4️⃣: محاسبات مالی

حالا سود/زیان و موجودی را محاسبه می‌کنیم.

### کد Python:
```python
from app.core.financial import CalculationEngine
from app.models.financial import Account

calc_engine = CalculationEngine(session)

# محاسبه برای هر Account
accounts = session.query(Account).all()

for account in accounts:
    summary = calc_engine.calculate_label_summary(account.label)
    
    print(f"\n📊 {account.label}:")
    print(f"   💰 Gold:")
    print(f"      خرید: {summary['gold']['purchased']:,.0f}")
    print(f"      فروخته شده: {summary['gold']['sold']:,.0f}")
    print(f"      موجودی: {summary['gold']['remaining']:,.0f}")
    print(f"   🥈 Silver:")
    print(f"      بونوس: {summary['silver']['bonus']:,.0f}")
    print(f"      فروخته شده: {summary['silver']['sold']:,.0f}")
    print(f"      موجودی: {summary['silver']['remaining']:,.0f}")
    print(f"   💵 مالی:")
    print(f"      هزینه خرید: {summary['total']['cost']:,.0f} تومان")
    print(f"      درآمد: {summary['total']['revenue']:,.0f} تومان")
    print(f"      سود: {summary['total']['profit']:,.0f} تومان")
```

### ✅ خروجی:
```
📊 A1054:
   💰 Gold:
      خرید: 1,000
      فروخته شده: 0
      موجودی: 1,000
   🥈 Silver:
      بونوس: 100
      فروخته شده: 0
      موجودی: 100
   💵 مالی:
      هزینه خرید: 450,000 تومان
      درآمد: 0 تومان
      سود: 0 تومان

📊 A1055:
   💰 Gold:
      خرید: 2,000
      فروخته شده: 0
      موجودی: 2,000
   🥈 Silver:
      بونوس: 200
      فروخته شده: 0
      موجودی: 200
   💵 مالی:
      هزینه خرید: 900,000 تومان
      درآمد: 0 تومان
      سود: 0 تومان
```

---

## مرحله 5️⃣: ثبت فروش

فرض کنید چند فروش انجام می‌دهید.

### کد Python:
```python
from app.models.financial import Sale
from decimal import Decimal
from datetime import datetime

# ایجاد چند فروش
sales = [
    Sale(
        label="A1054",
        quantity=Decimal("500"),
        sale_rate=Decimal("600"),
        sale_amount=Decimal("300000"),
        sale_type="gold",
        platform="roblox",
        customer="C1001",
        sale_date=datetime.now()
    ),
    Sale(
        label="A1054",
        quantity=Decimal("50"),
        sale_rate=Decimal("700"),
        sale_amount=Decimal("35000"),
        sale_type="silver",
        platform="roblox",
        customer="C1002",
        sale_date=datetime.now()
    ),
    Sale(
        label="A1055",
        quantity=Decimal("1000"),
        sale_rate=Decimal("580"),
        sale_amount=Decimal("580000"),
        sale_type="gold",
        platform="apple",
        customer="C1003",
        sale_date=datetime.now()
    ),
]

for sale in sales:
    session.add(sale)

session.commit()
print("✅ فروش‌ها ثبت شد!")
```

### ✅ خروجی:
```
🛒 ایجاد 3 فروش تست:
   • A1054: 500 gold @ 600 = 300,000 (roblox)
   • A1054: 50 silver @ 700 = 35,000 (roblox)
   • A1055: 1000 gold @ 580 = 580,000 (apple)
✅ فروش‌ها ذخیره شد
```

---

## مرحله 6️⃣: گزارش‌گیری

### گزارش Label (تفصیلی هر Account)
```python
from app.core.financial import AdvancedReportBuilder

report_builder = AdvancedReportBuilder(session)

# گزارش Label
label_config = {
    'report_type': 'label',
    'filters': {}
}
label_df = report_builder.build_report(label_config)

print("📊 گزارش Label:")
print(label_df)
```

### ✅ خروجی:
```
📊 گزارش Label:
   label  gold_purchased  gold_sold  gold_remaining  silver_bonus  silver_sold  silver_remaining  total_profit
0  A1054          1000.0      500.0           500.0         100.0         50.0              50.0      110000.0
1  A1055          2000.0     1000.0          1000.0         200.0          0.0             200.0       80000.0
2  G3200          1500.0        0.0          1500.0         150.0          0.0             150.0           0.0
```

### گزارش Platform (فروش به تفکیک پلتفرم)
```python
platform_config = {
    'report_type': 'platform',
    'filters': {}
}
platform_df = report_builder.build_report(platform_config)

print("📊 گزارش Platform:")
print(platform_df)
```

### ✅ خروجی:
```
📊 گزارش Platform:
   platform  total_sales  total_quantity  total_revenue  avg_rate
0    roblox            2           550.0       335000.0    609.09
1     apple            1          1000.0       580000.0    580.00
```

---

## مرحله 7️⃣: بررسی Discrepancy (مغایرت‌گیری)

اگر پرسنل شما سود را گزارش می‌دهند، می‌توانید با محاسبات سیستم مقایسه کنید.

### کد Python:
```python
from app.core.financial import DiscrepancyChecker

checker = DiscrepancyChecker(session)
discrepancies = checker.check_all_accounts()

if discrepancies:
    print(f"⚠️ {len(discrepancies)} اختلاف یافت شد:")
    for disc in discrepancies:
        print(f"   • {disc['label']}: محاسبه={disc['calculated_profit']:,.0f}, Staff={disc['staff_profit']:,.0f}, اختلاف={disc['discrepancy_percent']:.2f}%")
else:
    print("✅ هیچ اختلافی یافت نشد!")
```

### ✅ خروجی:
```
✅ هیچ اختلافی یافت نشد! (همه محاسبات صحیح است)
```

---

## 📊 نتایج نهایی

پس از طی تمام مراحل، شما:

### ✅ داده‌ها:
- 3 Account با اطلاعات کامل
- 3 خرید Gold با هزینه و نرخ
- 3 بونوس Silver
- 3 فروش (2 Gold + 1 Silver)

### ✅ محاسبات:
- سود هر Account
- موجودی Gold/Silver
- Profit Margin
- درآمد کل

### ✅ گزارش‌ها:
- گزارش تفصیلی Label
- گزارش Platform
- گزارش Customer
- امکان Export به Excel

---

## 🎯 مزایای این سیستم

1. **انعطاف**: هر شیت با هر ساختاری را می‌توانید Import کنید
2. **شفافیت**: تمام داده‌های خام حفظ می‌شوند
3. **قابلیت ردیابی**: هر داده از کجا آمده قابل پیگیری است
4. **محاسبات دقیق**: با Decimal برای جلوگیری از خطای Floating Point
5. **گزارش‌های پیشرفته**: با فیلترهای مختلف و Export به Excel

---

## 🔧 عیب‌یابی

### مشکل: SheetImport یافت نشد
**راه حل**: مطمئن شوید `sheet_import_id` صحیح است.

### مشکل: Field Mapping تعریف نشده
**راه حل**: قبل از Process، حتماً Field Mapping را تعریف کنید.

### مشکل: تبدیل داده ناموفق
**راه حل**: نوع داده را صحیح تعیین کنید (TEXT/DECIMAL/DATE).

---

## 📞 پشتیبانی

در صورت بروز مشکل، لاگ‌ها را بررسی کنید:
```python
from app.core.logger import app_logger

app_logger.info("پیام من")
```

---

**🎉 تبریک! شما سیستم Dynamic Field Mapping را با موفقیت راه‌اندازی کردید!**
