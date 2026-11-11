import os
import sys
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)


def fail(message):
    print("\n[ERROR] " + message)
    input("\nPress Enter to exit...")
    sys.exit(1)


def run(cmd, title):
    print("\n==> " + title)
    result = subprocess.run(cmd)
    if result.returncode != 0:
        fail("Failed at step: " + title + "\nCopy the error above and send it to Claude.")


def main():
    print("==============================")
    print("  MamadCraft Launcher - Build")
    print("==============================")

    for name in ("launcher.py", "logo.png", "icon.png"):
        if not os.path.isfile(name):
            fail(name + " was not found in: " + HERE)

    # اگه لانچر باز بود ببندش (وگرنه ویندوز اجازه‌ی ساخت exe جدید رو نمی‌ده)
    subprocess.run(["taskkill", "/F", "/IM", "MamadCraftLauncher.exe"],
                   capture_output=True)

    run([sys.executable, "-m", "pip", "install", "--upgrade",
         "pyinstaller", "customtkinter", "pillow", "minecraft-launcher-lib", "requests"],
        "1/3 Installing packages")

    print("\n==> 2/3 Creating icon.ico")
    from PIL import Image
    img = Image.open("icon.png").convert("RGBA")
    img.save("icon.ico", format="ICO",
             sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])

    data = ["--add-data", "logo.png;.", "--add-data", "icon.png;."]
    if os.path.isfile("design.png"):
        data += ["--add-data", "design.png;."]
    else:
        print("[WARNING] design.png not found - small fox logo in the sidebar will be hidden.")

    for folder in ("build", "dist"):
        shutil.rmtree(folder, ignore_errors=True)

    run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile",
         "--windowed", "--name", "MamadCraftLauncher", "--icon", "icon.ico",
         "--collect-all", "customtkinter", "--collect-all", "minecraft_launcher_lib"]
        + data + ["launcher.py"],
        "3/3 Building the exe (a few minutes)")

    exe = os.path.join(HERE, "dist", "MamadCraftLauncher.exe")
    if os.path.isfile(exe):
        size = os.path.getsize(exe) / (1024 * 1024)
        print("\n[DONE] %s  (%.1f MB)" % (exe, size))
        try:
            os.startfile(os.path.join(HERE, "dist"))
        except Exception:
            pass
    else:
        fail("The build finished but MamadCraftLauncher.exe is missing.\n"
             "Your antivirus (360 Total Security?) probably deleted or quarantined it.\n"
             "Open the antivirus quarantine, restore the file, and add this folder to its exclusions:\n"
             + HERE)

    input("\nPress Enter to exit...")


main()
