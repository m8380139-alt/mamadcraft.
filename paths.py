import os
import sys
import shutil

# آیا برنامه به‌صورت exe اجرا شده؟
FROZEN = getattr(sys, "frozen", False)

if FROZEN:
    # عکس‌هایی که داخل exe بسته‌بندی شدن
    RESOURCE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    # پوشه‌ای که exe توشه
    APP_DIR = os.path.dirname(sys.executable)
else:
    RESOURCE_DIR = os.path.dirname(os.path.abspath(__file__))
    APP_DIR = RESOURCE_DIR

# تنظیمات و اکانت‌ها اینجا ذخیره می‌شن (C:\Users\...\AppData\Roaming\MamadCraftLauncher)
DATA_DIR = os.path.join(os.getenv("APPDATA") or os.path.expanduser("~"), "MamadCraftLauncher")
os.makedirs(DATA_DIR, exist_ok=True)

# اگه از قبل فایل تنظیمات کنار برنامه بود، یه بار کپی می‌شه به پوشه‌ی جدید
for _name in ("settings.json", "account.json"):
    _old = os.path.join(APP_DIR, _name)
    _new = os.path.join(DATA_DIR, _name)
    if os.path.isfile(_old) and not os.path.isfile(_new):
        try:
            shutil.copy2(_old, _new)
        except Exception:
            pass


def resource(name):
    """مسیر یه فایل همراه برنامه (مثل logo.png)"""
    return os.path.join(RESOURCE_DIR, name)
