@echo off
chcp 65001 >nul
cls

echo ========================================
echo   🎮 GT-Land Manager
echo   نرم‌افزار مدیریت گیفت کارت
echo ========================================
echo.
echo 🚀 در حال اجرای برنامه...
echo.

python app\main.py

if errorlevel 1 (
    echo.
    echo ❌ خطا در اجرای برنامه!
    echo.
    echo 💡 اگر Python نصب نیست:
    echo    1. Python 3.14 را از python.org دانلود کنید
    echo    2. در زمان نصب "Add to PATH" را فعال کنید
    echo.
    pause
    exit /b 1
)

exit /b 0
