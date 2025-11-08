@echo off
chcp 65001 >nul
cls

echo ========================================
echo   GT-Land Manager - نرم افزار مدیریت
echo ========================================
echo.

REM بررسی وجود محیط مجازی
if not exist "venv\Scripts\python.exe" (
    echo ❌ خطا: محیط مجازی یافت نشد!
    echo.
    echo لطفاً ابتدا فایل run.bat را اجرا کنید و گزینه 1 را انتخاب کنید.
    echo.
    pause
    exit /b 1
)

echo ✅ محیط مجازی یافت شد
echo 🚀 در حال اجرای برنامه...
echo.

REM اجرای برنامه
venv\Scripts\python.exe app\main.py

if errorlevel 1 (
    echo.
    echo ❌ خطا در اجرای برنامه!
    echo.
    pause
    exit /b 1
)

exit /b 0
