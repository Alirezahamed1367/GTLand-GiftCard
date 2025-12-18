# 📋 الزامات نهایی سیستم - GT-Land Manager

## ✅ پاسخ سوالات کلیدی

### 1️⃣ ریت فروش
- **هر فروش ریت مجزا دارد** ✅
- ریت در شیت فروش ثبت می‌شود
- مثال: 
  - فروش 1: 500 Gold @ 1:10,000 Robux
  - فروش 2: 500 Gold @ 1:12,000 Robux

### 2️⃣ نرخ تمام شده
- **هر آکانت = یک خرید یکباره با یک نرخ ثابت** ✅
- Account Label تغییر نمی‌کند (مگر شارژ مجدد)
- نرخ خرید ثابت برای تمام فروش‌های آن آکانت استفاده می‌شود
- **فرمول سود:**
  ```
  سود = قیمت فروش - (مقدار فروخته شده × نرخ خرید آکانت)
  ```

### 3️⃣ شارژ مجدد آکانت
- **Email ثابت می‌ماند** ✅
- **Label تغییر می‌کند** (مثلاً A1055 → A1055-R2)
- **مقدار و نرخ جدید** ثبت می‌شود
- در واقع یک آکانت جدید با Email قبلی است

### 4️⃣ سیستم پرداخت مشتری
- **تمام فروش‌ها نسیه است** ✅
- پرداخت به صورت **Tether** یا **Toman**
- هر مشتری یک **گردش تفصیلی** دارد:
  ```
  تاریخ    | شرح              | بدهکار  | بستانکار | مانده
  --------------------------------------------------------
  2025-12-01| فروش Roblox     | $100    | -        | $100
  2025-12-05| واریز Tether    | -       | $50      | $50
  2025-12-10| فروش Apple      | $80     | -        | $130
  2025-12-15| واریز Toman     | -       | $100     | $30
  ```

### 5️⃣ ویرایش داده
- **ویرایش فقط از Google Sheets** ✅
- سپس Re-Import به سیستم
- یکپارچگی داده حفظ می‌شود
- در نرم‌افزار: **فقط مشاهده و گزارش**

### 6️⃣ Export/Output
- **فرمت فعلی کاربردی نیست** ✅
- نیاز به **سیستم Template سفارشی**
- کاربر بتواند:
  - ستون‌ها را انتخاب کند
  - ترتیب را تعیین کند
  - فرمت‌های مختلف داشته باشد
  - Template ذخیره و بارگذاری کند

---

## 🏗️ معماری سیستم (نهایی)

### 📊 Database Schema

#### جدول `accounts`
```sql
id              INT PRIMARY KEY
label           VARCHAR UNIQUE  -- A1055, A1055-R2
email           VARCHAR         -- ثابت می‌ماند
supplier        VARCHAR
created_at      DATETIME
is_active       BOOLEAN
notes           TEXT
```

#### جدول `account_gold`
```sql
id              INT PRIMARY KEY
account_id      INT FOREIGN KEY → accounts.id
quantity        DECIMAL         -- مقدار خرید
price_per_unit  DECIMAL         -- نرخ خرید (ثابت برای این آکانت)
total_cost      DECIMAL         -- quantity × price_per_unit
purchase_date   DATETIME
supplier        VARCHAR
```

#### جدول `account_silver` (مشابه)
```sql
-- ساختار مشابه account_gold
```

#### جدول `sales`
```sql
id              INT PRIMARY KEY
label           VARCHAR         -- کدام آکانت؟
sale_type       VARCHAR         -- 'gold' یا 'silver'
quantity        DECIMAL         -- چه مقدار فروخته شد؟
platform        VARCHAR         -- Roblox, Apple, ...
sale_rate       DECIMAL         -- ریت فروش (مثلاً 10000 = 1:10k)
sale_amount     DECIMAL         -- مبلغ دریافتی
cost_basis      DECIMAL         -- بهای تمام شده (quantity × نرخ خرید آکانت)
profit          DECIMAL         -- sale_amount - cost_basis
customer_code   VARCHAR         -- کد مشتری
sale_date       DATETIME
notes           TEXT
```

#### جدول `customers`
```sql
id                  INT PRIMARY KEY
code                VARCHAR UNIQUE  -- C001, C002, ...
name                VARCHAR
phone               VARCHAR
email               VARCHAR
total_purchases     INT             -- تعداد کل خریدها
total_spent         DECIMAL         -- مجموع خرج کرده (بدهکار)
total_paid          DECIMAL         -- مجموع پرداخت (بستانکار)
balance             DECIMAL         -- total_spent - total_paid
first_purchase_at   DATETIME
last_purchase_at    DATETIME
created_at          DATETIME
```

#### جدول `payments` (جدید!)
```sql
id              INT PRIMARY KEY
customer_code   VARCHAR FOREIGN KEY
amount          DECIMAL
currency        VARCHAR         -- 'TETHER' یا 'TOMAN'
exchange_rate   DECIMAL         -- نرخ تبدیل (اگر TOMAN)
amount_usd      DECIMAL         -- معادل دلار
payment_date    DATETIME
receipt_number  VARCHAR         -- شماره فیش
notes           TEXT
created_at      DATETIME
```

---

## 🔄 جریان کار سیستم

### مرحله 1: Import از Google Sheets

```python
# شیت خرید
columns: Label, Email, Supplier, Gold_Qty, Gold_Price, Silver_Qty, Silver_Price, Date

# شیت فروش
columns: Label, Platform, Type, Quantity, Rate, Amount, Customer, Date

# شیت پرداخت
columns: Customer, Amount, Currency, ExchangeRate, ReceiptNo, Date
```

### مرحله 2: Field Mapping
کاربر نقش هر ستون را مشخص می‌کند

### مرحله 3: پردازش خودکار

```python
def process_purchase():
    # 1. بررسی: آیا Label وجود دارد?
    existing = session.query(Account).filter_by(label=label).first()
    
    if existing and existing.email == new_email:
        # همان آکانت است - Update نکن!
        pass
    elif existing and existing.email != new_email:
        # شارژ مجدد! Label جدید بساز
        new_label = f"{base_label}-R{recharge_count}"
        create_new_account(new_label, new_email)
    else:
        # آکانت جدید
        create_new_account(label, email)
    
    # 2. ثبت خرید Gold/Silver با نرخ ثابت
    add_purchase(account_id, gold_qty, gold_price)
    add_purchase(account_id, silver_qty, silver_price)
```

```python
def process_sale():
    # 1. پیدا کردن آکانت و نرخ خرید
    account = get_account(label)
    purchases = get_purchases(account.id, sale_type)
    
    # 2. محاسبه بهای تمام شده
    avg_price = sum(p.price_per_unit * p.quantity) / sum(p.quantity)
    cost_basis = quantity * avg_price
    
    # 3. محاسبه سود
    profit = sale_amount - cost_basis
    
    # 4. ثبت فروش
    create_sale(
        label=label,
        quantity=quantity,
        platform=platform,
        sale_rate=rate,
        sale_amount=sale_amount,
        cost_basis=cost_basis,
        profit=profit,
        customer=customer
    )
    
    # 5. به‌روزرسانی بدهی مشتری
    update_customer_balance(customer, sale_amount)
```

```python
def process_payment():
    # 1. تبدیل به دلار (اگر تومان)
    if currency == 'TOMAN':
        amount_usd = amount / exchange_rate
    else:
        amount_usd = amount
    
    # 2. ثبت پرداخت
    create_payment(
        customer=customer,
        amount=amount_usd,
        currency=currency,
        receipt=receipt_no
    )
    
    # 3. کاهش بدهی مشتری
    reduce_customer_balance(customer, amount_usd)
```

---

## 📊 UI Components (اولویت‌بندی)

### ✅ Phase 1: Core System (در حال حاضر)
- [x] Import از Google Sheets
- [x] Field Mapping
- [x] Auto-detect آکانت‌ها
- [x] محاسبه سود پایه
- [x] گزارشات ساده

### 🚧 Phase 2: جدول مدیریت کامل
```
Priority: HIGH

Features:
1. DataGrid با ستون‌های پویا:
   - Label, Email, Supplier
   - Gold: Qty/Cost [📊 Details]
   - Silver: Qty/Cost [📊 Details]
   - Roblox: [N sales 🔵]
   - Apple: [N sales 🔵]
   - ... (هر پلتفرم یک ستون)

2. Click Handlers:
   [📊] → Dialog: لیست خریدها
   [🔵] → Dialog: لیست فروش‌ها با جزئیات
   
3. Summary Row:
   - کل سرمایه‌گذاری
   - کل فروش
   - کل سود
   - Profit Margin
```

### 🚧 Phase 3: سیستم مشتری و پرداخت
```
Priority: HIGH

Features:
1. جدول مشتریان:
   - Code, Name, Phone, Email
   - Total Purchases
   - Total Spent (بدهکار)
   - Total Paid (بستانکار)
   - Balance (مانده)

2. گردش تفصیلی مشتری:
   - تاریخ | شرح | بدهکار | بستانکار | مانده
   - فیلتر به تاریخ
   - Export

3. ثبت پرداخت:
   - مبلغ (Tether/Toman)
   - نرخ تبدیل
   - شماره فیش
   - تاریخ
```

### 🚧 Phase 4: Template System برای Export
```
Priority: MEDIUM

Features:
1. Template Builder:
   - انتخاب ستون‌ها (Drag & Drop)
   - ترتیب ستون‌ها
   - Format کردن (عدد، تاریخ، ارز)
   - Filter و Sort

2. Template Manager:
   - ذخیره Template
   - بارگذاری Template
   - Share Template

3. Export Formats:
   - Excel (با چند Sheet)
   - CSV
   - PDF (با Chart)
```

### 🚧 Phase 5: Dashboard تعاملی
```
Priority: LOW

Features:
1. Charts:
   - فروش به تفکیک پلتفرم (Pie Chart)
   - روند فروش (Line Chart)
   - سود به تفکیک ماه (Bar Chart)

2. KPIs:
   - فروش امروز/هفته/ماه
   - سود امروز/هفته/ماه
   - تعداد مشتریان فعال
   - میانگین فروش

3. Quick Filters:
   - بازه تاریخ
   - پلتفرم
   - مشتری
```

---

## 🎯 اولویت پیاده‌سازی فوری

### 1. بهینه‌سازی محاسبات (الان) ⚡
```python
# در DynamicDataProcessor
def process_sales_with_cost_basis():
    """
    محاسبه دقیق بهای تمام شده:
    - پیدا کردن نرخ خرید آکانت
    - محاسبه cost_basis = quantity × نرخ خرید
    - محاسبه profit = sale_amount - cost_basis
    """
```

### 2. جدول مدیریت کامل (هفته آینده) 📊
```python
# ویجت جدید: InventoryManagementWidget
class InventoryManagementWidget(QWidget):
    def __init__(self):
        # DataGrid با ستون‌های پویا
        # Click handlers برای [📊] و [🔵]
        # Dialogs برای جزئیات
```

### 3. سیستم مشتری (دو هفته آینده) 👥
```python
# جدول payments
# محاسبه balance
# گردش تفصیلی
```

---

## 📝 نکات مهم

### ⚠️ نکته 1: شارژ مجدد آکانت
```python
# الگوریتم تشخیص:
if email_exists and label_new:
    # این شارژ مجدد است!
    # Label جدید بساز: A1055-R2
    new_label = f"{base_label}-R{recharge_count + 1}"
```

### ⚠️ نکته 2: نرخ تبدیل Toman
```python
# هر پرداخت باید نرخ تبدیل خودش را داشته باشد
payment = Payment(
    amount=500000,  # تومان
    currency='TOMAN',
    exchange_rate=65000,  # نرخ روز
    amount_usd=500000 / 65000  # 7.69 دلار
)
```

### ⚠️ نکته 3: یکپارچگی داده
```python
# Source of Truth = Google Sheets
# نرم‌افزار = Read-Only View + Reports
# ویرایش فقط در Sheets → Re-Import
```

---

## ✅ Checklist پیاده‌سازی

### امروز:
- [x] Database بازسازی شد
- [x] خطاهای گزارشات برطرف شد
- [x] الزامات نهایی مستند شد
- [ ] بهینه‌سازی محاسبه سود
- [ ] اضافه کردن جدول `payments`

### این هفته:
- [ ] جدول مدیریت کامل
- [ ] Dialog جزئیات خرید
- [ ] Dialog جزئیات فروش
- [ ] تست کامل با داده واقعی

### هفته بعد:
- [ ] سیستم مشتری
- [ ] ثبت پرداخت
- [ ] گردش تفصیلی
- [ ] گزارش بدهی/طلب

---

## 🚀 شروع پیاده‌سازی

الان شروع می‌کنیم:
1. ✅ اضافه کردن Model برای `Payment`
2. ✅ بهینه‌سازی محاسبه سود در `DynamicDataProcessor`
3. ✅ ساخت `InventoryManagementWidget` پایه

آماده‌ایم؟ 🎯
