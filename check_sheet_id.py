from app.core.database import db_manager

config = db_manager.get_sheet_config(2)
if config:
    print(f"شیت ID=2: {config.name}")
else:
    print("شیت ID=2 پیدا نشد")

# لیست همه شیت‌ها
all_configs = db_manager.get_all_sheet_configs()
print(f"\nهمه شیت‌ها:")
for c in all_configs:
    print(f"  {c.id}: {c.name}")
