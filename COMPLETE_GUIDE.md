# 📖 راهنمای کامل GT-Land Manager

> سیستم جامع مدیریت و پردازش داده‌های فروش Google Sheets

**نسخه:** 2.2.0  
**تاریخ:** نوامبر 2025  
**توسعه‌دهنده:** تیم GT-Land

---

## 📋 فهرست مطالب

1. [معرفی](#معرفی)
2. [نصب و راه‌اندازی](#نصب-و-راه‌اندازی)
3. [راهنمای کاربری](#راهنمای-کاربری)
4. [راهنمای توسعه‌دهنده](#راهنمای-توسعه‌دهنده)
5. [معماری سیستم](#معماری-سیستم)
6. [مدیریت دیتابیس](#مدیریت-دیتابیس)
7. [عیب‌یابی](#عیب‌یابی)
8. [FAQ](#faq)

---

## 🎯 معرفی

### GT-Land Manager چیست؟

سیستمی جامع برای:
- 📥 **استخراج هوشمند** داده‌ها از Google Sheets
- 💾 **ذخیره‌سازی مرکزی** در دیتابیس SQLite
- 🔄 **مدیریت تکرار** و تشخیص داده‌های موجود
- 📤 **تولید خروجی Excel** با Template های قابل تنظیم
- 📊 **گزارش‌گیری** و تحلیل داده‌ها
- 🗄️ **آرشیو خودکار** و نگهداری تاریخچه

### ویژگی‌های کلیدی

✅ رابط کاربری گرافیکی (PyQt6)  
✅ پشتیبانی از چند Sheet مختلف  
✅ تشخیص خودکار ستون‌ها  
✅ مدیریت Duplicate ها  
✅ سیستم Template برای Export  
✅ گزارش‌های آماری پیشرفته  
✅ Backup و Archive خودکار  
✅ Log کامل عملیات  

---

## 🚀 نصب و راه‌اندازی

### پیش‌نیازها

- **Python**: نسخه 3.10 یا بالاتر
- **سیستم عامل**: Windows 10/11، Linux، macOS
- **Google Account**: برای دسترسی به Sheets API

### مرحله 1: دانلود و آماده‌سازی

```bash
# کلون پروژه (یا دانلود ZIP)
git clone https://github.com/your-org/GT-Land.git
cd GT-Land

# ایجاد محیط مجازی
python -m venv venv

# فعال‌سازی محیط مجازی
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# نصب پکیج‌ها
pip install -r requirements.txt
```

### مرحله 2: تنظیمات Google Sheets API

1. **ورود به Google Cloud Console:**
   - https://console.cloud.google.com/

2. **ایجاد پروژه جدید:**
   - نام: GT-Land Manager
   - شناسه یکتا انتخاب کنید

3. **فعال‌سازی Google Sheets API:**
   - APIs & Services → Library
   - جستجوی "Google Sheets API"
   - کلیک "Enable"

4. **ایجاد Service Account:**
   - APIs & Services → Credentials
   - Create Credentials → Service Account
   - نام: gt-land-service
   - نقش: Editor

5. **دانلود کلید JSON:**
   - وارد Service Account شوید
   - Keys → Add Key → Create New Key
   - نوع: JSON
   - فایل دانلود شده را به `config/credentials.json` کپی کنید

6. **اشتراک‌گذاری Google Sheet:**
   - Sheet خود را باز کنید
   - Share → ایمیل Service Account را اضافه کنید
   - دسترسی: Editor

### مرحله 3: تنظیمات محیط (.env)

فایل `.env` را از `.env.example` کپی کنید:

```bash
cp .env.example .env
```

محتوای `.env`:
```env
# دیتابیس
DATABASE_PATH=data/gt_land.db

# Google Sheets
GOOGLE_CREDENTIALS_PATH=config/credentials.json

# Log
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Export
EXPORT_PATH=data/exports
TEMPLATE_PATH=templates

# Backup
BACKUP_PATH=data/backups
ARCHIVE_PATH=data/archives
AUTO_BACKUP=true
BACKUP_RETENTION_DAYS=30
```

### مرحله 4: راه‌اندازی دیتابیس

```bash
# ایجاد ساختار دیتابیس
python setup_database.py
```

این دستور:
- دیتابیس `gt_land.db` را ایجاد می‌کند
- تمام جداول را می‌سازد
- Index های لازم را اضافه می‌کند

### مرحله 5: اجرای برنامه

**Windows:**
```bash
GT-Land.bat
```

**Linux/Mac:**
```bash
python app/main.py
```

---

## 👤 راهنمای کاربری

### 1️⃣ داشبورد اصلی

هنگام ورود به برنامه، داشبورد اصلی را می‌بینید:

#### کارت‌های آماری:
- **📝 تنظیمات شیت‌ها**: تعداد Sheet های تعریف شده
- **📦 کل رکوردها**: مجموع داده‌های ذخیره شده
- **✅ خروجی گرفته شده**: تعداد رکوردهای Export شده
- **⏳ در انتظار**: داده‌های بدون Export

#### دکمه‌های سریع:
- **📥 استخراج سریع**: انتقال فوری به تب استخراج
- **📤 تولید خروجی**: انتقال فوری به تب Export

### 2️⃣ مدیریت شیت‌ها

**مسیر:** تب "📋 مدیریت شیت‌ها"

#### افزودن Sheet جدید:

1. کلیک روی دکمه **"➕ افزودن شیت جدید"**

2. وارد کردن اطلاعات:
   - **نام شیت**: نام منحصر به فرد (مثال: "فروش شعبه شمال")
   - **Sheet ID**: شناسه Google Sheet (از URL کپی کنید)
     ```
     https://docs.google.com/spreadsheets/d/[SHEET_ID]/edit
     ```
   - **Sheet Name**: نام برگه در Google Sheet (مثال: "Sheet1")
   - **Range**: محدوده داده‌ها (مثال: "A1:Z")

3. **تنظیمات پیشرفته:**
   - **سطر شروع**: از کدام سطر داده شروع شود (پیش‌فرض: 2)
   - **کلید یکتا**: ستونی که برای تشخیص تکرار استفاده شود

4. **Mapping ستون‌ها:**
   ```json
   {
       "نام ستون در Sheet": "نام ستون در دیتابیس",
       "کد محصول": "product_code",
       "نام محصول": "product_name",
       "قیمت": "price"
   }
   ```

5. **ذخیره**

#### ویرایش/حذف:
- کلیک راست روی Sheet → "ویرایش" یا "حذف"

### 3️⃣ استخراج داده

**مسیر:** تب "📥 استخراج داده"

#### مراحل استخراج:

1. **بررسی آمار:**
   - تعداد Sheet های فعال
   - آخرین استخراج
   - تعداد رکوردها

2. **کلیک روی "▶️ شروع استخراج"**

3. **پیشرفت استخراج:**
   - نوار پیشرفت
   - لاگ زنده عملیات
   - تعداد رکوردهای جدید/موجود

4. **نتیجه:**
   - ✅ موفق: تعداد رکوردهای جدید
   - ⚠️ هشدار: Duplicate ها
   - ❌ خطا: پیغام خطا

#### مدیریت Duplicate ها:

هنگام تشخیص تکرار، دیالوگ انتخاب نمایش داده می‌شود:

- **رد کردن**: رکورد جدید نادیده گرفته شود
- **جایگزینی**: رکورد قدیمی با جدید جایگزین شود
- **هر دو**: هر دو ذخیره شوند (با ID متفاوت)

### 4️⃣ تولید خروجی Excel

**مسیر:** تب "📤 Export و داده‌ها"

#### روش 1: Export ساده

1. کلیک روی **"📤 Export جدید"**
2. انتخاب Sheet
3. انتخاب محدوده زمانی (اختیاری)
4. انتخاب فایل Excel مقصد
5. **ذخیره**

#### روش 2: استفاده از Template

1. **ایجاد Template:**
   - کلیک روی **"🗂️ مدیریت Template ها"**
   - افزودن Template جدید:
     - نام Template
     - فایل Excel الگو
     - نام Worksheet مقصد
     - موقعیت شروع (سطر/ستون)
     - Mapping ستون‌ها

2. **استفاده از Template:**
   - انتخاب Template از لیست
   - انتخاب Sheet
   - محدوده زمانی (اختیاری)
   - **Export**

#### ویژگی‌های Export:

- ✅ حفظ فرمت Excel موجود
- ✅ درج در موقعیت دلخواه
- ✅ Mapping خودکار ستون‌ها
- ✅ فیلتر بر اساس تاریخ
- ✅ فیلتر Status (همه/Export شده/نشده)

### 5️⃣ گزارش‌ها

**مسیر:** تب "📈 گزارش‌ها"

#### انواع گزارش:

1. **گزارش خلاصه:**
   - تعداد کل رکوردها
   - تعداد Export شده‌ها
   - آخرین استخراج
   - آخرین Export

2. **گزارش بر اساس Sheet:**
   - تعداد رکورد هر Sheet
   - وضعیت Export
   - آمار Duplicate

3. **گزارش زمانی:**
   - داده‌های روزانه
   - داده‌های ماهانه
   - مقایسه دوره‌ها

4. **گزارش Template ها:**
   - تعداد استفاده از هر Template
   - آخرین استفاده
   - وضعیت فعال/غیرفعال

### 6️⃣ تنظیمات

**مسیر:** تب "⚙️ تنظیمات"

#### بخش‌های تنظیمات:

1. **تنظیمات عمومی:**
   - زبان رابط کاربری
   - تم (روشن/تیره)
   - اندازه فونت

2. **تنظیمات Google Sheets:**
   - مسیر فایل Credentials
   - تست اتصال
   - تنظیم Timeout

3. **تنظیمات دیتابیس:**
   - مسیر دیتابیس
   - Backup خودکار
   - تعداد روزهای نگهداری Archive
   - بهینه‌سازی (Vacuum)

4. **تنظیمات Export:**
   - مسیر پیش‌فرض Export
   - مسیر Template ها
   - فرمت نام فایل

---

## 🛠️ راهنمای توسعه‌دهنده

### ساختار پروژه

```
GT-Land/
├── app/
│   ├── core/           # هسته برنامه
│   │   ├── database.py       # مدیریت دیتابیس
│   │   ├── google_sheets.py  # اتصال به Google Sheets
│   │   ├── excel_exporter.py # Export به Excel
│   │   └── logger.py         # سیستم Log
│   │
│   ├── gui/            # رابط کاربری
│   │   ├── main_window.py    # پنجره اصلی
│   │   ├── dialogs/          # دیالوگ‌ها
│   │   └── widgets/          # ویجت‌های سفارشی
│   │
│   ├── models/         # مدل‌های داده
│   │   ├── base.py           # کلاس پایه
│   │   ├── sales_data.py     # مدل داده‌های فروش
│   │   ├── sheet_config.py   # مدل تنظیمات Sheet
│   │   └── export_template.py # مدل Template
│   │
│   ├── utils/          # ابزارهای کمکی
│   │   ├── constants.py      # ثوابت برنامه
│   │   ├── ui_constants.py   # ثوابت UI
│   │   ├── helpers.py        # توابع کمکی
│   │   ├── excel_helper.py   # کمکی Excel
│   │   └── data_helper.py    # کمکی داده
│   │
│   └── main.py         # نقطه ورود برنامه
│
├── config/             # تنظیمات
│   └── credentials.json      # کلید Google API
│
├── data/               # داده‌ها
│   ├── gt_land.db           # دیتابیس اصلی
│   ├── backups/             # پشتیبان‌ها
│   ├── archives/            # آرشیوها
│   └── exports/             # فایل‌های Export شده
│
├── logs/               # لاگ‌ها
│   └── app.log
│
├── templates/          # Template های Excel
│
├── .env                # تنظیمات محیط
├── requirements.txt    # پکیج‌های Python
├── setup_database.py   # اسکریپت راه‌اندازی دیتابیس
└── GT-Land.bat        # اجرای برنامه (Windows)
```

### معماری کلی

#### 1. لایه دیتابیس (Database Layer)

**فایل:** `app/core/database.py`

**کلاس اصلی:** `DatabaseManager`

**متدهای کلیدی:**
```python
# اتصال
def connect() -> Connection

# Sheet Config
def create_sheet_config(data: dict) -> bool
def get_all_sheet_configs() -> List[SheetConfig]
def update_sheet_config(id: int, data: dict) -> bool

# Sales Data
def insert_sales_data(data: dict) -> int
def check_duplicate(unique_key: str, value: str) -> Optional[SalesData]
def fetch_data_by_sheet_config(sheet_id: int) -> List[SalesData]

# Export Template
def create_export_template(data: dict) -> bool
def get_all_export_templates() -> List[ExportTemplate]

# Statistics
def get_statistics() -> dict

# Maintenance
def create_backup() -> str
def vacuum_database() -> bool
```

#### 2. لایه Google Sheets

**فایل:** `app/core/google_sheets.py`

**کلاس اصلی:** `GoogleSheetExtractor`

**متدهای کلیدی:**
```python
def authenticate() -> gspread.Client
def extract_data(sheet_config: SheetConfig) -> List[dict]
def get_sheet_info(sheet_id: str) -> dict
```

**جریان استخراج:**
```
1. احراز هویت با Google API
2. باز کردن Spreadsheet
3. انتخاب Worksheet
4. خواندن Range
5. تبدیل به دیکشنری با Mapping
6. بازگشت List[dict]
```

#### 3. لایه Export

**فایل:** `app/core/excel_exporter.py`

**کلاس اصلی:** `ExcelExporter`

**متدهای کلیدی:**
```python
def export_to_excel(
    data: List[SalesData],
    template: ExportTemplate,
    output_path: str
) -> bool

def apply_column_mapping(
    data: dict,
    mapping: dict
) -> dict
```

**جریان Export:**
```
1. بارگذاری Template Excel
2. انتخاب Worksheet
3. یافتن موقعیت شروع (start_row, start_column)
4. اعمال Mapping ستون‌ها
5. نوشتن داده‌ها
6. ذخیره فایل
7. به‌روزرسانی Status در دیتابیس
```

#### 4. لایه UI

**فایل اصلی:** `app/gui/main_window.py`

**کلاس اصلی:** `MainWindow`

**ساختار تب‌ها:**
- Dashboard → `create_dashboard_tab()`
- مدیریت شیت‌ها → `SheetListWidget`
- استخراج → `ExtractionWidget`
- Export → `DataViewerWidget` + Dialogs
- گزارش‌ها → `ReportsWidget`
- تنظیمات → `SettingsDialog`

### استانداردهای UI

**فایل:** `app/utils/ui_constants.py`

```python
# Font Sizes
FONT_SIZE_TITLE = 18
FONT_SIZE_SECTION = 14
FONT_SIZE_BUTTON = 11

# Button Heights
BUTTON_HEIGHT_LARGE = 50
BUTTON_HEIGHT_MEDIUM = 40

# Colors
COLOR_PRIMARY = "#2196F3"
COLOR_SUCCESS = "#4CAF50"
COLOR_DANGER = "#F44336"

# Functions
get_button_style(color, font_size, height)
get_responsive_dialog_size(screen, ratio_type)
```

**استفاده:**
```python
from app.utils.ui_constants import (
    BUTTON_HEIGHT_MEDIUM,
    COLOR_SUCCESS,
    get_button_style
)

button = QPushButton("ذخیره")
button.setMinimumHeight(BUTTON_HEIGHT_MEDIUM)
button.setStyleSheet(get_button_style(COLOR_SUCCESS))
```

### مدل‌های داده

#### 1. SheetConfig
```python
@dataclass
class SheetConfig:
    id: int
    name: str
    source_type: str = "google_sheets"
    sheet_id: str = ""
    sheet_name: str = ""
    range: str = "A1:Z"
    start_row: int = 2
    column_mapping: dict = field(default_factory=dict)
    unique_key_column: Optional[str] = None
    is_active: bool = True
```

#### 2. SalesData
```python
@dataclass
class SalesData:
    id: int
    sheet_config_id: int
    data: dict
    extracted_at: datetime
    is_exported: bool = False
    exported_at: Optional[datetime] = None
```

#### 3. ExportTemplate
```python
@dataclass
class ExportTemplate:
    id: int
    name: str
    template_path: str
    target_worksheet: str = "Sheet1"
    start_row: int = 2
    start_column: int = 1
    column_mappings: dict = field(default_factory=dict)
    is_active: bool = True
```

### API داخلی

#### Database Manager

```python
from app.core.database import db_manager

# دریافت همه Sheet ها
configs = db_manager.get_all_sheet_configs()

# درج داده جدید
data = {
    'sheet_config_id': 1,
    'data': {'product': 'A', 'price': 100}
}
record_id = db_manager.insert_sales_data(data)

# بررسی تکرار
duplicate = db_manager.check_duplicate('id_column', 'value123')
if duplicate:
    # مدیریت تکرار
    pass

# آمار
stats = db_manager.get_statistics()
print(stats['total_records'])
```

#### Google Sheets Extractor

```python
from app.core.google_sheets import GoogleSheetExtractor

extractor = GoogleSheetExtractor()

# استخراج از یک Sheet
data_list = extractor.extract_data(sheet_config)

for row in data_list:
    # پردازش داده
    print(row)
```

#### Excel Exporter

```python
from app.core.excel_exporter import ExcelExporter

exporter = ExcelExporter()

# Export با Template
success = exporter.export_to_excel(
    data=sales_data_list,
    template=export_template,
    output_path="data/exports/output.xlsx"
)
```

### افزودن ویژگی جدید

#### مثال: افزودن نوع داده جدید

1. **مدل داده (`app/models/new_data.py`):**
```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class NewData:
    id: int
    name: str
    value: float
    created_at: datetime
```

2. **جدول دیتابیس:**
```python
# در setup_database.py
cursor.execute("""
    CREATE TABLE IF NOT EXISTS new_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        value REAL NOT NULL,
        created_at TEXT NOT NULL
    )
""")
```

3. **متدهای Database Manager:**
```python
# در app/core/database.py
def create_new_data(self, data: dict) -> int:
    cursor = self.conn.cursor()
    cursor.execute("""
        INSERT INTO new_data (name, value, created_at)
        VALUES (?, ?, ?)
    """, (data['name'], data['value'], datetime.now()))
    self.conn.commit()
    return cursor.lastrowid
```

4. **Widget UI:**
```python
# در app/gui/widgets/new_data_widget.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout

class NewDataWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        # UI components
```

5. **افزودن به MainWindow:**
```python
# در app/gui/main_window.py
from app.gui.widgets.new_data_widget import NewDataWidget

def create_new_data_tab(self):
    self.new_data_widget = NewDataWidget()
    self.tabs.addTab(self.new_data_widget, "📊 داده جدید")
```

---

## 💾 مدیریت دیتابیس

### ساختار جداول

#### 1. sheet_configs
```sql
CREATE TABLE sheet_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    source_type TEXT DEFAULT 'google_sheets',
    sheet_id TEXT NOT NULL,
    sheet_name TEXT NOT NULL,
    range TEXT DEFAULT 'A1:Z',
    start_row INTEGER DEFAULT 2,
    column_mapping TEXT,  -- JSON
    unique_key_column TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT
);
```

#### 2. sales_data
```sql
CREATE TABLE sales_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sheet_config_id INTEGER NOT NULL,
    data TEXT NOT NULL,  -- JSON
    extracted_at TEXT NOT NULL,
    is_exported INTEGER DEFAULT 0,
    exported_at TEXT,
    FOREIGN KEY (sheet_config_id) REFERENCES sheet_configs(id)
);
```

#### 3. export_templates
```sql
CREATE TABLE export_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    template_type TEXT DEFAULT 'custom',
    template_path TEXT,
    target_worksheet TEXT DEFAULT 'Sheet1',
    start_row INTEGER DEFAULT 2,
    start_column INTEGER DEFAULT 1,
    column_mappings TEXT,  -- JSON
    is_active INTEGER DEFAULT 1,
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT
);
```

#### 4. export_logs
```sql
CREATE TABLE export_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER,
    sheet_config_id INTEGER,
    export_path TEXT,
    record_count INTEGER,
    status TEXT,
    exported_at TEXT NOT NULL,
    FOREIGN KEY (template_id) REFERENCES export_templates(id),
    FOREIGN KEY (sheet_config_id) REFERENCES sheet_configs(id)
);
```

#### 5. process_logs
```sql
CREATE TABLE process_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    process_type TEXT NOT NULL,
    sheet_config_id INTEGER,
    status TEXT NOT NULL,
    message TEXT,
    records_processed INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY (sheet_config_id) REFERENCES sheet_configs(id)
);
```

### Index ها

```sql
-- سرعت جستجو در sales_data
CREATE INDEX idx_sales_sheet ON sales_data(sheet_config_id);
CREATE INDEX idx_sales_exported ON sales_data(is_exported);
CREATE INDEX idx_sales_date ON sales_data(extracted_at);

-- سرعت جستجو در export_logs
CREATE INDEX idx_export_template ON export_logs(template_id);
CREATE INDEX idx_export_date ON export_logs(exported_at);

-- سرعت جستجو در process_logs
CREATE INDEX idx_process_type ON process_logs(process_type);
CREATE INDEX idx_process_date ON process_logs(created_at);
```

### Backup و Archive

#### Backup خودکار

تنظیمات در `.env`:
```env
AUTO_BACKUP=true
BACKUP_RETENTION_DAYS=30
```

**زمان‌بندی:**
- قبل از هر عملیات Export
- روزانه در ساعت 00:00 (اگر فعال باشد)
- قبل از عملیات Vacuum

**مسیر:** `data/backups/`

**فرمت نام:** `backup_YYYYMMDD_HHMMSS.db`

#### Archive قدیمی

**زمان:** هر 30 روز یک بار

**فرآیند:**
1. داده‌های بیش از 90 روز انتخاب می‌شوند
2. به فایل Archive جدید منتقل می‌شوند
3. از دیتابیس اصلی حذف می‌شوند

**مسیر:** `data/archives/`

**فرمت نام:** `archive_YYYYMMDD_HHMMSS.db`

#### دستورات مدیریتی

```python
from app.core.database import db_manager

# ایجاد Backup دستی
backup_path = db_manager.create_backup()
print(f"Backup: {backup_path}")

# بهینه‌سازی (Vacuum)
success = db_manager.vacuum_database()

# پاک‌سازی Backup های قدیمی
db_manager.cleanup_old_backups(days=30)

# آرشیو داده‌های قدیمی
archive_path = db_manager.archive_old_data(days=90)
```

### Query های مفید

```sql
-- تعداد رکوردها بر اساس Sheet
SELECT 
    sc.name,
    COUNT(sd.id) as total_records,
    SUM(CASE WHEN sd.is_exported = 1 THEN 1 ELSE 0 END) as exported,
    SUM(CASE WHEN sd.is_exported = 0 THEN 1 ELSE 0 END) as pending
FROM sheet_configs sc
LEFT JOIN sales_data sd ON sc.id = sd.sheet_config_id
GROUP BY sc.id, sc.name;

-- رکوردهای امروز
SELECT * FROM sales_data
WHERE DATE(extracted_at) = DATE('now');

-- آمار Export های ماه جاری
SELECT 
    COUNT(*) as total_exports,
    SUM(record_count) as total_records,
    template_id
FROM export_logs
WHERE strftime('%Y-%m', exported_at) = strftime('%Y-%m', 'now')
GROUP BY template_id;

-- لاگ‌های خطا
SELECT * FROM process_logs
WHERE status = 'error'
ORDER BY created_at DESC
LIMIT 50;
```

---

## 🔧 عیب‌یابی

### مشکلات رایج

#### 1. خطای احراز هویت Google

**علامت:**
```
Error: Unable to authenticate with Google Sheets API
```

**راه‌حل:**
1. بررسی `config/credentials.json`
2. اطمینان از فعال بودن Google Sheets API
3. بررسی دسترسی Service Account به Sheet
4. تست اتصال از تنظیمات

#### 2. خطای دیتابیس قفل شده

**علامت:**
```
Error: database is locked
```

**راه‌حل:**
1. بستن برنامه و اجرای مجدد
2. حذف فایل `.db-journal` در صورت وجود
3. اجرای Vacuum:
   ```python
   db_manager.vacuum_database()
   ```

#### 3. خطای Import پکیج

**علامت:**
```
ModuleNotFoundError: No module named 'PyQt6'
```

**راه‌حل:**
```bash
pip install -r requirements.txt --upgrade
```

#### 4. خطای مسیر فایل

**علامت:**
```
FileNotFoundError: [Errno 2] No such file or directory
```

**راه‌حل:**
1. بررسی مسیرهای `.env`
2. ایجاد پوشه‌های لازم:
   ```bash
   mkdir -p data/backups data/archives data/exports logs templates
   ```

#### 5. داده‌های تکراری

**علامت:**
- پیام Duplicate در استخراج

**راه‌حل:**
1. بررسی `unique_key_column` در SheetConfig
2. تنظیم ستون یکتای مناسب
3. انتخاب استراتژی مدیریت تکرار

### لاگ‌ها

**مسیر:** `logs/app.log`

**سطوح Log:**
- `DEBUG`: اطلاعات تفصیلی برای توسعه
- `INFO`: اطلاعات عمومی
- `WARNING`: هشدارها
- `ERROR`: خطاها
- `CRITICAL`: خطاهای بحرانی

**مشاهده زنده:**
```bash
# Windows
Get-Content logs/app.log -Tail 50 -Wait

# Linux/Mac
tail -f logs/app.log
```

### ابزارهای دیباگ

#### 1. تست اتصال Google
```python
from app.core.google_sheets import GoogleSheetExtractor

extractor = GoogleSheetExtractor()
client = extractor.authenticate()
print("✅ Connected to Google Sheets")
```

#### 2. بررسی دیتابیس
```bash
sqlite3 data/gt_land.db
.tables
.schema sales_data
SELECT COUNT(*) FROM sales_data;
.quit
```

#### 3. تست Export
```python
from app.core.excel_exporter import ExcelExporter
from app.core.database import db_manager

exporter = ExcelExporter()
data = db_manager.fetch_data_by_sheet_config(1, limit=5)
# تست با 5 رکورد
```

---

## ❓ FAQ

### سوالات عمومی

**Q: حداکثر چند Sheet می‌توانم اضافه کنم؟**  
A: محدودیتی وجود ندارد، اما توصیه می‌شود کمتر از 50 Sheet فعال داشته باشید.

**Q: آیا می‌توانم از Google Drive فایل Excel بخوانم؟**  
A: خیر، فقط Google Sheets پشتیبانی می‌شود. باید فایل را به Sheet تبدیل کنید.

**Q: Duplicate ها چگونه تشخیص داده می‌شوند؟**  
A: بر اساس ستون `unique_key_column` که در SheetConfig تعریف می‌کنید.

**Q: آیا می‌توانم فرمول Excel در Template داشته باشم؟**  
A: بله، فرمول‌ها حفظ می‌شوند و فقط داده‌ها درج می‌شوند.

**Q: حداکثر تعداد رکورد در یک Export چقدر است؟**  
A: محدودیت Excel: 1,048,576 سطر

### سوالات فنی

**Q: چگونه می‌توانم ستون جدید به دیتابیس اضافه کنم؟**  
A: ستون‌ها در فیلد JSON `data` ذخیره می‌شوند، نیازی به تغییر Schema نیست.

**Q: آیا می‌توانم از PostgreSQL به جای SQLite استفاده کنم؟**  
A: باید کلاس `DatabaseManager` را بازنویسی کنید. توصیه نمی‌شود.

**Q: چگونه می‌توانم اعلان‌های Desktop اضافه کنم؟**  
A: از پکیج `plyer` استفاده کنید:
```python
from plyer import notification
notification.notify(title="GT-Land", message="استخراج تکمیل شد")
```

**Q: آیا می‌توانم برنامه را به EXE تبدیل کنم؟**  
A: بله، با PyInstaller:
```bash
pip install pyinstaller
pyinstaller --onefile --windowed app/main.py
```

---

## 📞 پشتیبانی

### راه‌های ارتباطی

- **ایمیل:** support@gtland.com
- **تلگرام:** @GTLandSupport
- **GitHub Issues:** [مخزن پروژه]

### گزارش باگ

لطفاً موارد زیر را شامل شود:
1. نسخه برنامه
2. سیستم عامل
3. مراحل بازتولید مشکل
4. پیغام خطا (از Log)
5. Screenshot (در صورت امکان)

### درخواست ویژگی

از بخش Issues در GitHub استفاده کنید با برچسب `enhancement`.

---

## 📜 License

این پروژه تحت مجوز MIT منتشر شده است.

---

## 🙏 تشکر

از تمام کسانی که در توسعه این پروژه مشارکت داشته‌اند، تشکر می‌کنیم.

**نسخه:** 2.2.0  
**آخرین بروزرسانی:** نوامبر 2025

---

**🚀 GT-Land Manager - ساده، قدرتمند، کارآمد**
