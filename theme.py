import random
import ctypes

import engine

ACCENT_PRESETS = ["#ff7a00", "#e53935", "#43a047", "#1e88e5",
                  "#8e24aa", "#ec407a", "#00acc1", "#fdd835"]

_DARK = {
    "bg": "#0b0b0d", "panel": "#121215", "row": "#1a1a1f", "btn": "#1c1c21",
    "btn_hover": "#2a2a31", "text": "#ffffff", "text_dim": "#d0d0d6", "gray": "#9a9aa3",
}
_LIGHT = {
    "bg": "#f1f1f5", "panel": "#ffffff", "row": "#e9e9ef", "btn": "#dcdce4",
    "btn_hover": "#cfcfd9", "text": "#111114", "text_dim": "#2b2b33", "gray": "#6b6b75",
}

_cache = None


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def darken(h, factor=0.82):
    r, g, b = hex_to_rgb(h)
    return "#%02x%02x%02x" % (int(r * factor), int(g * factor), int(b * factor))


def luminance(h):
    r, g, b = hex_to_rgb(h)
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255


def system_is_dark():
    """تم ویندوز تیره‌ست یا روشن"""
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        return value == 0
    except Exception:
        return True


def system_animations_enabled():
    """انیمیشن‌ها توی ویندوز روشنه یا خاموش"""
    try:
        flag = ctypes.c_int(1)
        ctypes.windll.user32.SystemParametersInfoW(0x1042, 0, ctypes.byref(flag), 0)
        return bool(flag.value)
    except Exception:
        return True


def build(s):
    mode = s["theme"]
    if mode == "system":
        mode = "dark" if system_is_dark() else "light"

    p = dict(_DARK if mode == "dark" else _LIGHT)
    accent = random.choice(ACCENT_PRESETS) if s["dynamic_accent"] else s["accent"]

    p["mode"] = mode
    p["accent"] = accent
    p["accent_hover"] = darken(accent)
    p["accent_text"] = "#111114" if luminance(accent) > 0.65 else "#ffffff"
    p["radius"] = int(s["corner_radius"])
    p["opacity"] = max(0.5, min(1.0, s["opacity"] / 100.0))

    motion = s["motion"]
    p["animate"] = (motion == "full") or (motion == "system" and system_animations_enabled())
    return p


def get():
    """رنگ‌ها و ظاهر برنامه (فقط یک بار موقع اجرا ساخته می‌شه)"""
    global _cache
    if _cache is None:
        _cache = build(engine.load_settings())
    return _cache
