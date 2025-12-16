@echo off
chcp 65001 >nul
cls

echo ╔════════════════════════════════════════════════════════════╗
echo ║           🎮 GT-Land Manager                              ║
echo ║           نرم‌افزار مدیریت گیفت کارت                      ║
echo ║           Label-Based Financial System                    ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo 🚀 در حال اجرای برنامه...
echo.

REM بررسی Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python نصب نیست!
    echo.
    echo 💡 لطفاً ابتدا Setup-New-System.bat را اجرا کنید
    echo.
    pause
    exit /b 1
)

REM اجرای برنامه
python app\main.py

if errorlevel 1 (
    echo.
    echo ❌ خطا در اجرای برنامه!
    echo.
    echo 💡 راهنمایی:
    echo    • اگر Python نصب نیست: Setup-New-System.bat را اجرا کنید
    echo    • برای مشاهده خطای دقیق: python app\main.py
    echo    • برای نصب کتابخانه‌ها: pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ برنامه با موفقیت بسته شد
pause
exit /b 0
