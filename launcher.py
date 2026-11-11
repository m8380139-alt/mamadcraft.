import os
import sys
import json
import subprocess
import threading
import webbrowser
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image

import appicon
import engine
import paths
import theme
from settings_window import SettingsWindow
from accounts import AccountsWindow, load_name, save_name
from versions_window import VersionsWindow
from mods_window import ModsWindow

P = theme.get()
ctk.set_appearance_mode(P["mode"])
R = P["radius"]

DESIGN = paths.resource("design.png")   # طرح کامل لانچر (برای لوگوی کوچیک)
HERO = paths.resource("logo.png")       # روباه تاج‌دار وسط صفحه اول

SITE_URL = "https://m8380139-alt.github.io/mamadcraft"   # سایت ممد کرفت
RUBIKA_URL = "https://rubika.ir/mamaddcraft"             # کانال روبیکا




def crop_part(img, left, top, right, bottom):
    """بخشی از عکس رو با درصد می‌بره"""
    w, h = img.size
    return img.crop((int(w * left), int(h * top), int(w * right), int(h * bottom)))


def cover(img, w, h):
    """عکس رو طوری تنظیم می‌کنه که کل کادر رو پر کنه"""
    scale = max(w / img.width, h / img.height)
    img = img.resize((int(img.width * scale) + 1, int(img.height * scale) + 1), Image.LANCZOS)
    x = (img.width - w) // 2
    y = (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))


class Launcher(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MamadCraft Launcher")
        appicon.apply(self)
        self.geometry("1180x660")
        self.resizable(False, False)
        self.configure(fg_color=P["bg"])

        self.busy = False
        self.first_fill = True
        self.max_value = 1
        self.settings_win = None
        self.accounts_win = None
        self.versions_win = None
        self.mods_win = None
        self.banner_img = None
        self.logo_img = None
        self.settings = engine.load_settings()
        engine.ensure_launcher_profiles()
        self.load_images()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.build_sidebar()
        self.build_main()
        self.start_loading_versions()

        # شفافیت و انیمیشن شروع
        if P["animate"]:
            self.attributes("-alpha", 0.0)
            self.after(60, lambda: self.fade_in(0.0))
        else:
            self.attributes("-alpha", P["opacity"])

    # ---------- شفافیت ----------
    def fade_in(self, current):
        current += 0.08
        if current >= P["opacity"]:
            self.attributes("-alpha", P["opacity"])
            return
        self.attributes("-alpha", current)
        self.after(16, lambda: self.fade_in(current))

    def apply_opacity(self, percent):
        self.attributes("-alpha", max(0.5, min(1.0, percent / 100.0)))

    # ---------- ری‌استارت ----------
    def restart_app(self):
        env = dict(os.environ, PYINSTALLER_RESET_ENVIRONMENT="1")
        if paths.FROZEN:
            subprocess.Popen([sys.executable], cwd=paths.APP_DIR, env=env)
        else:
            subprocess.Popen([sys.executable, os.path.abspath(__file__)],
                             cwd=paths.APP_DIR, env=env)
        self.destroy()

    # ---------- عکس‌ها ----------
    def load_images(self):
        # عکس وسط صفحه اول (logo.png)
        if os.path.isfile(HERO):
            hero = Image.open(HERO).convert("RGBA")
            hero.thumbnail((900, 540), Image.LANCZOS)
            bg = theme.hex_to_rgb(P["bg"]) + (255,)
            canvas = Image.new("RGBA", (950, 570), bg)
            x = (950 - hero.width) // 2
            y = (570 - hero.height) // 2
            canvas.paste(hero, (x, y), hero)
            canvas = canvas.convert("RGB")
            self.banner_img = ctk.CTkImage(light_image=canvas, dark_image=canvas,
                                           size=(950, 570))

        # لوگوی کوچیک نوار کناری (از design.png)
        if os.path.isfile(DESIGN):
            design = Image.open(DESIGN).convert("RGB")
            if self.banner_img is None:
                art = cover(crop_part(design, 0.178, 0.081, 1.0, 0.882), 950, 570)
                self.banner_img = ctk.CTkImage(light_image=art, dark_image=art,
                                               size=(950, 570))
            small = crop_part(design, 0.03, 0.665, 0.143, 0.877)
            self.logo_img = ctk.CTkImage(light_image=small, dark_image=small,
                                         size=(145, 154))

    # ---------- نوار کناری ----------
    def build_sidebar(self):
        side = ctk.CTkFrame(self, width=230, corner_radius=0, fg_color=P["panel"])
        side.grid(row=0, column=0, sticky="ns")
        side.pack_propagate(False)

        ctk.CTkLabel(side, text="MamadCraft", text_color=P["accent"],
                     font=("Segoe UI", 20, "bold")
                     ).pack(anchor="w", padx=22, pady=(22, 14))

        items = [
            ("🏠", "Home", self.show_home),
            ("⚙", "Settings", self.open_settings),
            ("📦", "Accounts", self.go_accounts),
            ("📋", "Versions", self.go_versions),
            ("📁", "Logs", self.open_logs),
            ("🌐", "Website", self.open_site),
            ("💬", "Rubika", self.open_rubika),
            ("ℹ", "About", self.show_about),
        ]
        for i, (icon, name, cmd) in enumerate(items):
            active = (i == 0)
            ctk.CTkButton(side, text=icon + "    " + name, anchor="w", height=42,
                          corner_radius=R,
                          fg_color=P["accent"] if active else "transparent",
                          hover_color=P["accent_hover"] if active else P["btn"],
                          text_color=P["accent_text"] if active else P["text_dim"],
                          font=("Segoe UI", 15, "bold"),
                          command=cmd).pack(fill="x", padx=12, pady=2)

        self.version_label = ctk.CTkLabel(side, text="", text_color=P["gray"])
        self.version_label.pack(side="bottom", anchor="w", padx=22, pady=(0, 16))
        if self.logo_img:
            ctk.CTkLabel(side, text="", image=self.logo_img).pack(side="bottom", pady=(0, 6))

    # ---------- بخش اصلی ----------
    def build_main(self):
        main = ctk.CTkFrame(self, fg_color=P["bg"], corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(0, weight=1)

        # بنر
        ctk.CTkLabel(main, text="", image=self.banner_img, fg_color=P["bg"],
                     corner_radius=0).grid(row=0, column=0, sticky="nsew")

        # نوار پایین
        bar = ctk.CTkFrame(main, height=90, corner_radius=0, fg_color=P["panel"])
        bar.grid(row=1, column=0, sticky="ew")
        bar.grid_propagate(False)
        bar.grid_columnconfigure(1, weight=1)
        bar.grid_rowconfigure(1, weight=1)

        self.progress = ctk.CTkProgressBar(bar, height=4, corner_radius=0,
                                           progress_color=P["accent"], fg_color=P["btn"])
        self.progress.grid(row=0, column=0, columnspan=6, sticky="ew")
        self.progress.set(0)

        status_box = ctk.CTkFrame(bar, fg_color="transparent")
        status_box.grid(row=1, column=0, sticky="w", padx=(22, 0))
        ctk.CTkLabel(status_box, text="●", text_color="#2ecc71",
                     font=("Segoe UI", 16)).pack(side="left")
        self.status = ctk.CTkLabel(status_box, text="Loading versions...", width=250,
                                   anchor="w", text_color=P["text"],
                                   font=("Segoe UI", 14))
        self.status.pack(side="left", padx=(8, 0))

        self.name_var = ctk.StringVar(value=load_name())
        self.name_entry = ctk.CTkEntry(bar, textvariable=self.name_var, width=150,
                                       height=42, corner_radius=R, fg_color=P["btn"],
                                       border_width=0, placeholder_text="Account name")
        self.name_entry.grid(row=1, column=2, padx=6)

        self.version_var = ctk.StringVar()
        self.version_box = ctk.CTkComboBox(bar, variable=self.version_var, values=[],
                                           state="readonly", width=140, height=42,
                                           corner_radius=R, fg_color=P["btn"],
                                           border_width=0, button_color=P["btn"],
                                           command=self.on_version_change)
        self.version_box.grid(row=1, column=3, padx=6)

        self.show_all = ctk.BooleanVar(value=self.settings["show_snapshots"])
        ctk.CTkCheckBox(bar, text="Snapshots", width=100, variable=self.show_all,
                        command=self.start_loading_versions,
                        fg_color=P["accent"], hover_color=P["accent_hover"]
                        ).grid(row=1, column=4, padx=6)

        self.play_btn = ctk.CTkButton(bar, text="▶   Play", width=170, height=52,
                                      corner_radius=R, fg_color=P["accent"],
                                      hover_color=P["accent_hover"],
                                      text_color=P["accent_text"],
                                      font=("Segoe UI", 20, "bold"),
                                      command=self.on_play)
        self.play_btn.grid(row=1, column=5, padx=(6, 18))

    # ---------- دکمه‌های نوار کناری ----------
    def show_home(self):
        pass

    def open_settings(self):
        if self.settings_win is not None and self.settings_win.winfo_exists():
            self.settings_win.focus()
            return
        self.settings_win = SettingsWindow(self)

    def go_accounts(self):
        if self.accounts_win is not None and self.accounts_win.winfo_exists():
            self.accounts_win.focus()
            return
        self.accounts_win = AccountsWindow(self)

    def set_account(self, name):
        self.name_var.set(name)
        save_name(name)

    def go_versions(self):
        if self.versions_win is not None and self.versions_win.winfo_exists():
            self.versions_win.focus()
            return
        self.versions_win = VersionsWindow(self)

    def select_version(self, version):
        """ورژن انتخاب‌شده از صفحه Versions رو توی نوار پایین می‌ذاره"""
        values = list(self.version_box.cget("values"))
        if version not in values:
            values.insert(0, version)
            self.version_box.configure(values=values)
        self.version_var.set(version)
        self.version_label.configure(text="v" + version)
        self.status.configure(text="Selected " + version)

    def install_only(self, version):
        """ورژن رو انتخاب و فقط دانلود می‌کنه (بدون اجرای بازی)"""
        self.select_version(version)
        if self.busy:
            return
        if engine.is_installed(version):
            self.status.configure(text=version + " is already installed")
            return
        self.busy = True
        self.play_btn.configure(state="disabled")
        self.progress.set(0)
        threading.Thread(target=self.download_only, args=(version,), daemon=True).start()

    def download_only(self, version):
        callback = {
            "setStatus": lambda t: self.after(0, lambda: self.status.configure(text=t)),
            "setProgress": lambda v: self.after(0, lambda: self.set_progress(v)),
            "setMax": lambda v: self.after(0, lambda: self.set_max(v)),
        }
        try:
            self.after(0, lambda: self.status.configure(text="Downloading " + version + "..."))
            engine.install(version, callback)
            self.after(0, lambda: self.status.configure(text=version + " installed ✓"))
        except Exception as e:
            print("ERROR:", e)
            err = str(e)
            self.after(0, lambda: messagebox.showerror("MamadCraft", "Error:\n" + err))
            self.after(0, lambda: self.status.configure(text="Error"))
        finally:
            self.busy = False
            self.after(0, lambda: self.play_btn.configure(state="normal"))

    def open_mods(self, version):
        if self.mods_win is not None and self.mods_win.winfo_exists():
            self.mods_win.destroy()
        self.mods_win = ModsWindow(self, version)

    def install_fabric(self, mc_version):
        """Fabric رو برای یه ورژن نصب می‌کنه (بدون اجرای بازی)"""
        if self.busy:
            messagebox.showinfo("MamadCraft", "Please wait for the current download to finish.")
            return
        self.busy = True
        self.play_btn.configure(state="disabled")
        self.progress.set(0)
        threading.Thread(target=self.fabric_job, args=(mc_version,), daemon=True).start()

    def fabric_job(self, mc_version):
        callback = {
            "setStatus": lambda t: self.after(0, lambda: self.status.configure(text=t)),
            "setProgress": lambda v: self.after(0, lambda: self.set_progress(v)),
            "setMax": lambda v: self.after(0, lambda: self.set_max(v)),
        }
        try:
            self.after(0, lambda: self.status.configure(
                text="Installing Fabric for " + mc_version + "..."))
            vid = engine.install_fabric_version(mc_version, callback)
            self.after(0, lambda: self.fabric_done(vid))
        except Exception as e:
            print("ERROR:", e)
            err = str(e)
            self.after(0, lambda: messagebox.showerror("MamadCraft", "Error:\n" + err))
            self.after(0, lambda: self.status.configure(text="Error"))
        finally:
            self.busy = False
            self.after(0, lambda: self.play_btn.configure(state="normal"))

    def fabric_done(self, vid):
        self.start_loading_versions()
        self.select_version(vid)
        self.status.configure(text="Fabric installed ✓  (use Versions > Mods to add mods)")

    def open_logs(self):
        folder = engine.get_logs_dir()
        if not os.path.isdir(folder):
            folder = engine.get_mc_dir()
        os.makedirs(folder, exist_ok=True)
        os.startfile(folder)

    def open_site(self):
        webbrowser.open(SITE_URL)

    def open_rubika(self):
        webbrowser.open(RUBIKA_URL)

    def show_about(self):
        messagebox.showinfo("About", "MamadCraft Launcher\nMade by mrfox")

    # ---------- ورژن‌ها ----------
    def on_version_change(self, choice):
        self.version_label.configure(text="v" + choice)

    def start_loading_versions(self):
        self.status.configure(text="Loading versions...")
        threading.Thread(target=self.load_versions, daemon=True).start()

    def load_versions(self):
        try:
            ids = engine.get_versions(self.show_all.get())
            # نسخه‌های سفارشی نصب‌شده (مثل OptiFine) بالای لیست
            custom = [v for v in engine.get_installed_versions() if v not in ids]
            ids = custom + ids
            self.after(0, lambda: self.fill_versions(ids))
        except Exception as e:
            print("ERROR:", e)
            # آفلاین: ورژن‌هایی که قبلاً کامل دانلود شدن رو نشون بده
            installed = engine.get_installed_versions()
            if installed:
                self.after(0, lambda: self.fill_versions(
                    installed, "Offline mode - installed versions only"))
            else:
                self.after(0, lambda: self.status.configure(
                    text="No internet and no installed versions (VPN?)"))

    def fill_versions(self, ids, status="Ready to play!"):
        self.version_box.configure(values=ids)
        s = engine.load_settings()
        last = s.get("last_version", "")
        if self.first_fill and s["remember_version"] and last in ids:
            self.version_var.set(last)
        elif ids and self.version_var.get() not in ids:
            self.version_var.set(ids[0])
        self.first_fill = False
        self.version_label.configure(text="v" + self.version_var.get())
        self.status.configure(text=status)

    # ---------- پلی ----------
    def on_play(self):
        if self.busy:
            return
        name = self.name_var.get().strip()
        version = self.version_var.get()
        if not name or not version:
            messagebox.showwarning("MamadCraft", "Enter a name and choose a version.")
            return

        save_name(name)
        s = engine.load_settings()
        s["last_version"] = version
        engine.save_settings(s)

        self.busy = True
        self.play_btn.configure(state="disabled")
        threading.Thread(target=self.install_and_launch, args=(name, version),
                         daemon=True).start()

    def set_max(self, v):
        self.max_value = max(v, 1)

    def set_progress(self, v):
        self.progress.set(min(v / self.max_value, 1))

    def install_and_launch(self, name, version):
        callback = {
            "setStatus": lambda t: self.after(0, lambda: self.status.configure(text=t)),
            "setProgress": lambda v: self.after(0, lambda: self.set_progress(v)),
            "setMax": lambda v: self.after(0, lambda: self.set_max(v)),
        }
        try:
            if not engine.is_installed(version):
                self.after(0, lambda: self.status.configure(text="Downloading " + version + "..."))
                engine.install(version, callback)

            self.after(0, lambda: self.status.configure(text="Launching Minecraft..."))
            engine.launch(version, name)
            self.after(0, lambda: self.status.configure(text="Minecraft started!"))

            if engine.load_settings()["close_on_launch"]:
                self.after(0, lambda: self.after(2500, self.destroy))
        except Exception as e:
            print("ERROR:", e)
            err = str(e)
            self.after(0, lambda: messagebox.showerror("MamadCraft", "Error:\n" + err))
            self.after(0, lambda: self.status.configure(text="Error"))
        finally:
            self.busy = False
            self.after(0, lambda: self.play_btn.configure(state="normal"))


if __name__ == "__main__":
    Launcher().mainloop()
