# اسکریپت پاکسازی cache و اجرای برنامه

Write-Host "🧹 پاکسازی cache های Python..." -ForegroundColor Yellow

# پاکسازی همه __pycache__ ها
Get-ChildItem -Path "app" -Recurse -Filter "__pycache__" -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "✅ Cache ها پاک شدند" -ForegroundColor Green

Write-Host "`n🚀 اجرای برنامه با UI جدید..." -ForegroundColor Cyan

# اجرای برنامه
& ".\venv\Scripts\python.exe" -m app.main

Write-Host "`n✅ برنامه بسته شد" -ForegroundColor Green
