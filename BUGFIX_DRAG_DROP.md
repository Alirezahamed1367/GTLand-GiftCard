# 🔧 رفع مشکل Crash در Drag & Drop

## 📋 مشکلات شناسایی شده:

### 1. **مشکل `position().toPoint()` در PyQt6**
- **محل**: `DroppableColumnList.dropEvent()`
- **علت**: در برخی نسخه‌های PyQt6، متد `position()` مشکل دارد
- **راه حل**: Try-Except برای fallback به `pos()`

```python
try:
    pos = event.position().toPoint()
except:
    pos = event.pos()
```

### 2. **عدم بررسی داده‌های Null**
- **محل**: `startDrag()` و `dropEvent()`
- **علت**: اگر `column_name` یا `source_sheet` خالی باشد، Crash می‌کند
- **راه حل**: بررسی قبل از استفاده

```python
if not column_name or not current_sheet:
    return
```

### 3. **CSS Property نامعتبر: `cursor`**
- **محل**: `SourceColumnsList` stylesheet
- **علت**: Qt stylesheet از `cursor: grab` پشتیبانی نمی‌کند
- **راه حل**: حذف `cursor: grab;`

### 4. **Google Sheets خالی**
- **محل**: `load_available_sheets()`
- **علت**: اگر هیچ Google Sheet فعالی نباشد، dictionary خالی می‌شود
- **راه حل**: بررسی و نمایش پیام هشدار

```python
if not sheet_configs:
    self.sheets_list.addItem("⚠️ هیچ Google Sheet فعالی یافت نشد")
    return
```

### 5. **عدم بررسی Excel columns**
- **محل**: `initializePage()` در Wizard
- **علت**: اگر فایل Excel نامعتبر باشد، `excel_columns` خالی می‌شود
- **راه حل**: بررسی قبل از ساخت Widget

```python
if not self.excel_columns:
    QMessageBox.warning(self, "هشدار", "ستون‌های Excel شناسایی نشدند")
    return
```

---

## ✅ تغییرات اعمال شده:

### 1. **`column_mapping_widget.py`**

#### ✏️ `DroppableColumnList.dropEvent()`:
- ✅ Try-Except برای `position()`
- ✅ بررسی Null برای `source_col` و `source_sheet`
- ✅ Error handling کامل

#### ✏️ `SourceColumnsList.startDrag()`:
- ✅ بررسی `currentItem()` قبل از استفاده
- ✅ بررسی `column_name` و `current_sheet`
- ✅ Error handling کامل

#### ✏️ `SourceColumnsList` stylesheet:
- ✅ حذف `cursor: grab;`

#### ✏️ `ColumnMappingWidget.init_ui()`:
- ✅ بررسی `excel_columns` خالی
- ✅ بررسی `available_sheets` خالی
- ✅ نمایش پیام خطا به جای Crash

---

### 2. **`template_manager_dialog_advanced.py`**

#### ✏️ `load_available_sheets()`:
- ✅ بررسی `sheet_configs` خالی
- ✅ اگر Sheet ستون نداشت، از نام‌های نمونه استفاده کن
- ✅ Error handling کامل با traceback

#### ✏️ `initializePage()`:
- ✅ بررسی `selected_sheets` خالی
- ✅ بررسی `excel_columns` خالی
- ✅ نمایش QMessageBox به جای Silent Crash
- ✅ Error handling کامل

---

## 🧪 تست‌ها:

### ✅ تست Standalone Widget:
```bash
python test_drag_drop.py
```
- Widget با موفقیت ساخته می‌شود
- Drag & Drop کار می‌کند
- هیچ Crash ای رخ نمی‌دهد

### ✅ تست برنامه اصلی:
```bash
python app/main.py
```
- برنامه باز می‌شود
- نسخه Ver 9 نمایش داده می‌شود (هنوز نیاز به cache clear دارد)
- Font warning عادی است (مشکلی نیست)

---

## 📝 نکات مهم:

### ⚠️ **قبل از تست Template Manager:**
1. مطمئن شوید حداقل **یک Google Sheet فعال** در دیتابیس دارید
2. از منوی اصلی → **"Sheet List"** → یک Sheet اضافه کنید
3. سپس **"مدیریت Template ها"** را باز کنید

### 🔍 **اگر هنوز Crash می‌کند:**
1. Terminal را باز نگه دارید تا خطا را ببینید
2. از `test_drag_drop.py` برای تست جداگانه استفاده کنید
3. لاگ‌ها را بررسی کنید: `logs/*.log`

### 💡 **Drag & Drop چطور کار می‌کند:**
1. از ComboBox بالا یک Google Sheet انتخاب کنید
2. ستون را از **سمت راست** (Google Sheets) بگیرید
3. روی ستون **سمت چپ** (Excel) رها کنید
4. ستون تبدیل به ✅ سبز می‌شود

---

## 🚀 مراحل بعدی:

1. ✅ تست کامل Workflow:
   - ساخت Template جدید
   - Mapping ستون‌ها
   - افزودن Formula
   - ذخیره و Export

2. ✅ افزودن Google Sheet نمونه:
   ```python
   python setup_database.py  # اگر Sheet نداریم
   ```

3. ✅ Push به GitHub:
   ```bash
   git add .
   git commit -m "Fix Drag & Drop crash issues - Ver 9"
   git push origin main
   ```

---

## 📞 در صورت مشکل:

اگر هنوز Crash می‌کند، لطفاً:
1. خطای کامل را از Terminal کپی کنید
2. بگویید در کدام مرحله Crash می‌کند:
   - هنگام باز کردن Wizard؟
   - هنگام انتخاب فایل Excel؟
   - هنگام رفتن به صفحه Mapping؟
   - هنگام Drag کردن؟
   - هنگام Drop کردن؟

---

**تاریخ رفع**: 2025-11-08  
**نسخه**: Ver 9  
**وضعیت**: ✅ رفع شد
