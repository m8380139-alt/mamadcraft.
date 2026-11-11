import os
import ctypes
from PIL import Image

import paths

# باعث می‌شه توی نوار پایین ویندوز آیکون خودمون نشون داده بشه (نه آیکون پایتون)
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("MamadCraft.Launcher")
except Exception:
    pass

_ico_path = None
_tried = False


def ico_path():
    """از icon.png یه فایل icon.ico می‌سازه و مسیرش رو برمی‌گردونه"""
    global _ico_path, _tried
    if _tried:
        return _ico_path
    _tried = True

    src = paths.resource("icon.png")
    if not os.path.isfile(src):
        return None
    ico = os.path.join(paths.DATA_DIR, "icon.ico")
    try:
        img = Image.open(src).convert("RGBA")
        img.save(ico, format="ICO",
                 sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
        _ico_path = ico
    except Exception as e:
        print("Could not create icon:", e)
    return _ico_path


def _set(window, path):
    try:
        if window.winfo_exists():
            window.iconbitmap(path)
    except Exception:
        pass


def apply(window):
    """آیکون رو روی پنجره می‌ذاره (customtkinter آیکونش رو با تأخیر عوض می‌کنه، برای همین صبر می‌کنیم)"""
    path = ico_path()
    if path:
        window.after(300, lambda: _set(window, path))
