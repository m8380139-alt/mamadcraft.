import os
import json
import uuid
import ctypes
import hashlib
import subprocess

import minecraft_launcher_lib as mll
import requests

import paths

BASE_DIR = paths.DATA_DIR
SETTINGS_FILE = os.path.join(paths.DATA_DIR, "settings.json")
DEFAULT_MC_DIR = os.path.join(os.getenv("APPDATA") or os.path.expanduser("~"), ".mamadcraft")

DEFAULT_SETTINGS = {
    # Game
    "fullscreen": False,
    "use_default_resolution": True,
    "width": 854,
    "height": 480,
    "use_default_storage": True,
    "storage_dir": "",
    "ram_mb": 2560,
    "jvm_args": "",
    "java_path": "",
    # General
    "remember_version": True,
    "last_version": "",
    "show_snapshots": False,
    "close_on_launch": False,
    # Appearance
    "theme": "dark",            # dark / light / system
    "accent": "#ff7a00",
    "dynamic_accent": False,
    "corner_radius": 12,
    "opacity": 100,
    "motion": "system",         # system / reduced / full
}


# ---------- تنظیمات ----------
def load_settings():
    s = dict(DEFAULT_SETTINGS)
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            s.update(json.load(f))
    except Exception:
        pass
    return s


def save_settings(s):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(s, f, indent=2)


def reset_settings():
    """همه‌ی تنظیمات رو به حالت اول برمی‌گردونه"""
    try:
        os.remove(SETTINGS_FILE)
    except FileNotFoundError:
        pass


# ---------- پوشه‌ها ----------
def get_mc_dir():
    s = load_settings()
    if not s["use_default_storage"] and s["storage_dir"]:
        return s["storage_dir"]
    return DEFAULT_MC_DIR


def get_versions_dir():
    return os.path.join(get_mc_dir(), "versions")


def get_logs_dir():
    return os.path.join(get_mc_dir(), "logs")


def get_total_ram_mb():
    """رم کل سیستم (مگابایت)"""
    try:
        class MEMSTAT(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]
        stat = MEMSTAT()
        stat.dwLength = ctypes.sizeof(MEMSTAT)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        return int(stat.ullTotalPhys // (1024 * 1024))
    except Exception:
        return 8192


# ---------- ماینکرفت ----------
def offline_uuid(name):
    h = bytearray(hashlib.md5(("OfflinePlayer:" + name).encode()).digest())
    h[6] = (h[6] & 0x0F) | 0x30
    h[8] = (h[8] & 0x3F) | 0x80
    return str(uuid.UUID(bytes=bytes(h)))


def get_versions(show_all=False):
    versions = mll.utils.get_version_list()
    if show_all:
        return [v["id"] for v in versions]
    return [v["id"] for v in versions if v["type"] == "release"]


def get_version_infos():
    """همه‌ی ورژن‌ها با نوع و تاریخ انتشار (برای صفحه Versions)"""
    return mll.utils.get_version_list()


MARKER = ".mamadcraft_ok"   # نشونه‌ی «دانلود این ورژن کامل تموم شده»


def is_installed(version):
    """فقط وقتی True می‌ده که دانلود ورژن کامل تموم شده باشه"""
    if os.path.isfile(os.path.join(get_versions_dir(), version, MARKER)):
        return True
    # نسخه‌های سفارشی (مثل OptiFine) که روی یه ورژن نصب‌شده سوار می‌شن
    try:
        path = os.path.join(get_versions_dir(), version, version + ".json")
        with open(path, "r", encoding="utf-8") as f:
            parent = json.load(f).get("inheritsFrom")
    except Exception:
        return False
    if parent:
        return os.path.isfile(os.path.join(get_versions_dir(), parent, MARKER))
    return False


def get_installed_versions():
    """ورژن‌های کاملاً دانلود‌شده رو از روی کامپیوتر پیدا می‌کنه (برای حالت آفلاین)"""
    folder = get_versions_dir()
    found = []
    try:
        for name in os.listdir(folder):
            vdir = os.path.join(folder, name)
            jpath = os.path.join(vdir, name + ".json")
            if os.path.isfile(jpath) and is_installed(name):
                found.append((os.path.getmtime(jpath), name))
    except Exception:
        return []
    found.sort(reverse=True)   # جدیدترین دانلود اول
    return [name for _, name in found]


# ---------- Fabric و ماد‌ها ----------
FABRIC_PREFIX = "fabric-loader-"
MODRINTH = "https://api.modrinth.com/v2"
HEADERS = {"User-Agent": "mrfox/MamadCraftLauncher/1.0"}

# (اسم در Modrinth، اسم نمایشی، توضیح)
RECOMMENDED_MODS = [
    ("fabric-api", "Fabric API", "Required by most Fabric mods."),
    ("sodium", "Sodium", "Big FPS boost. A much faster rendering engine."),
    ("lithium", "Lithium", "Faster game logic, less lag."),
    ("ferrite-core", "FerriteCore", "Uses much less memory (RAM)."),
    ("entityculling", "Entity Culling", "Skips rendering of hidden entities."),
    ("immediatelyfast", "ImmediatelyFast", "Faster menus and HUD drawing."),
    ("iris", "Iris Shaders", "Shader support (works with Sodium)."),
    ("modmenu", "Mod Menu", "Shows your mods list in the game menu."),
]
PACK_SLUGS = ["fabric-api", "sodium", "lithium", "ferrite-core",
              "entityculling", "immediatelyfast"]


def _field(item, name):
    try:
        return item[name]
    except Exception:
        return getattr(item, name)


def get_fabric_supported():
    """ورژن‌های ماینکرفتی که Fabric ازشون پشتیبانی می‌کنه"""
    return [_field(v, "version") for v in mll.fabric.get_all_minecraft_versions()]


def get_parent_version(version):
    """ورژن اصلی ماینکرفتِ یه ورژن سفارشی (مثلاً برای Fabric)"""
    try:
        path = os.path.join(get_versions_dir(), version, version + ".json")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f).get("inheritsFrom")
    except Exception:
        return None


def get_game_dir(version):
    """ورژن‌های Fabric پوشه‌ی بازی جدا دارن تا ماد‌هاشون قاطی نشه"""
    if version.startswith(FABRIC_PREFIX):
        path = os.path.join(get_mc_dir(), "instances", version)
    else:
        path = get_mc_dir()
    os.makedirs(path, exist_ok=True)
    return path


def install_fabric_version(mc_version, callback=None):
    """Fabric رو برای یه ورژن نصب می‌کنه و اسم ورژن ساخته‌شده رو برمی‌گردونه"""
    ensure_launcher_profiles()
    mc_dir = get_mc_dir()
    mll.fabric.install_fabric(mc_version, mc_dir, callback=callback)

    vid = None
    newest = 0
    for name in os.listdir(get_versions_dir()):
        jpath = os.path.join(get_versions_dir(), name, name + ".json")
        if name.startswith(FABRIC_PREFIX) and name.endswith("-" + mc_version) \
                and os.path.isfile(jpath):
            t = os.path.getmtime(jpath)
            if t > newest:
                newest, vid = t, name
    if vid is None:
        raise RuntimeError("Fabric version was not created")

    # دانلود هر دو (ورژن اصلی و Fabric) کامل شده
    for name in (mc_version, vid):
        folder = os.path.join(get_versions_dir(), name)
        if os.path.isdir(folder):
            with open(os.path.join(folder, MARKER), "w") as f:
                f.write("ok")
    return vid


def mods_dir(version):
    path = os.path.join(get_game_dir(version), "mods")
    os.makedirs(path, exist_ok=True)
    return path


def _mods_record_path(version):
    return os.path.join(get_game_dir(version), "mamadcraft_mods.json")


def load_installed_mods(version):
    try:
        with open(_mods_record_path(version), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def installed_mod_slugs(version):
    """ماد‌هایی که نصب شدن و فایلشون هنوز هست"""
    record = load_installed_mods(version)
    folder = mods_dir(version)
    return {slug for slug, name in record.items() if os.path.isfile(os.path.join(folder, name))}


def install_mod(version, slug, mc_version=None, _seen=None):
    """ماد رو از Modrinth دانلود می‌کنه (به‌همراه ماد‌های لازمش)"""
    mc_version = mc_version or get_parent_version(version)
    seen = _seen if _seen is not None else set()
    if slug in seen:
        return []
    seen.add(slug)

    r = requests.get("%s/project/%s/version" % (MODRINTH, slug),
                     params={"game_versions": json.dumps([mc_version]),
                             "loaders": json.dumps(["fabric"])},
                     headers=HEADERS, timeout=30)
    r.raise_for_status()
    versions = r.json()
    if not versions:
        raise RuntimeError("not available for Minecraft " + str(mc_version))

    v = versions[0]
    files = v["files"]
    f = next((x for x in files if x.get("primary")), files[0])
    path = os.path.join(mods_dir(version), f["filename"])
    if not os.path.isfile(path):
        data = requests.get(f["url"], headers=HEADERS, timeout=120)
        data.raise_for_status()
        with open(path, "wb") as fh:
            fh.write(data.content)

    # اسم واقعی پروژه رو بگیر تا توی لیست «نصب‌شده» درست نشون داده بشه
    real_slug = slug
    try:
        pr = requests.get("%s/project/%s" % (MODRINTH, slug), headers=HEADERS, timeout=30)
        if pr.ok:
            real_slug = pr.json().get("slug", slug)
    except Exception:
        pass
    record = load_installed_mods(version)
    record[real_slug] = f["filename"]
    with open(_mods_record_path(version), "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2)

    done = [f["filename"]]
    for dep in v.get("dependencies", []):
        if dep.get("dependency_type") == "required" and dep.get("project_id"):
            done += install_mod(version, dep["project_id"], mc_version, seen)
    return done


def ensure_launcher_profiles():
    """نصب‌کننده‌ی OptiFine و Forge این فایل رو توی پوشه‌ی بازی لازم دارن"""
    mc = get_mc_dir()
    path = os.path.join(mc, "launcher_profiles.json")
    if os.path.isfile(path):
        return
    try:
        os.makedirs(mc, exist_ok=True)
        data = {
            "profiles": {},
            "selectedProfile": "",
            "clientToken": "",
            "authenticationDatabase": {},
            "launcherVersion": {"name": "2.0.0", "format": 21, "profilesFormat": 2},
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print("Could not create launcher_profiles.json:", e)


def get_installed_infos():
    """مثل get_version_infos ولی فقط ورژن‌های نصب‌شده (بدون اینترنت)"""
    infos = []
    for name in get_installed_versions():
        kind = "release"
        try:
            path = os.path.join(get_versions_dir(), name, name + ".json")
            with open(path, "r", encoding="utf-8") as f:
                kind = json.load(f).get("type", "release")
        except Exception:
            pass
        infos.append({"id": name, "type": kind, "releaseTime": None})
    return infos


def install(version, callback=None):
    ensure_launcher_profiles()
    mll.install.install_minecraft_version(version, get_mc_dir(), callback=callback)
    # فقط وقتی دانلود بدون ارور تموم شد، علامت می‌ذاریم
    with open(os.path.join(get_versions_dir(), version, MARKER), "w") as f:
        f.write("ok")


def launch(version, name):
    s = load_settings()
    mc_dir = get_mc_dir()

    jvm = ["-Xmx%dM" % s["ram_mb"], "-Xms512M"] + s["jvm_args"].split()
    options = {
        "username": name,
        "uuid": offline_uuid(name),
        "token": "",
        "jvmArguments": jvm,
    }
    if not s["use_default_resolution"]:
        options["customResolution"] = True
        options["resolutionWidth"] = str(s["width"])
        options["resolutionHeight"] = str(s["height"])
    if s["java_path"]:
        options["executablePath"] = s["java_path"]

    game_dir = get_game_dir(version)
    if game_dir != mc_dir:
        options["gameDirectory"] = game_dir
    cmd = mll.command.get_minecraft_command(version, mc_dir, options)
    if s["fullscreen"]:
        cmd.append("--fullscreen")
    # بدون باز شدن پنجره‌ی سیاه CMD
    return subprocess.Popen(cmd, cwd=game_dir,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
