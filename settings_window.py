import os
import customtkinter as ctk
from tkinter import filedialog, messagebox, colorchooser

import appicon
import engine
import theme

P = theme.get()

APPEARANCE_KEYS = ["theme", "accent", "dynamic_accent", "corner_radius", "motion"]
THEME_NAMES = {"dark": "Dark", "light": "Light", "system": "System"}
MOTION_NAMES = {"system": "System Setting", "reduced": "Reduced", "full": "Full"}
REV_THEME = {v: k for k, v in THEME_NAMES.items()}
REV_MOTION = {v: k for k, v in MOTION_NAMES.items()}

BOLD = ("Segoe UI", 13, "bold")
SMALL = ("Segoe UI", 12)


class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Settings")
        appicon.apply(self)
        self.geometry("920x640")
        self.minsize(780, 540)
        self.configure(fg_color=P["bg"])

        self.s = engine.load_settings()
        self.old = dict(self.s)
        self.bool_vars = {}
        self.ram_max = max(1024, (engine.get_total_ram_mb() // 256) * 256 - 1024)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.build_sidebar()

        right = ctk.CTkFrame(self, fg_color=P["bg"], corner_radius=0)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        self.page_title = ctk.CTkLabel(right, text="Game", anchor="w",
                                       font=("Segoe UI", 16, "bold"))
        self.page_title.grid(row=0, column=0, sticky="ew", padx=24, pady=(16, 8))

        self.pages = {
            "General": self.build_general_page(right),
            "Appearance": self.build_appearance_page(right),
            "Game": self.build_game_page(right),
            "Advanced": self.build_advanced_page(right),
        }
        for page in self.pages.values():
            page.grid(row=1, column=0, sticky="nsew", padx=16)

        bottom = ctk.CTkFrame(right, fg_color=P["panel"], corner_radius=0, height=60)
        bottom.grid(row=2, column=0, sticky="ew")
        self.saved_label = ctk.CTkLabel(bottom, text="", text_color="#4caf50")
        self.saved_label.pack(side="left", padx=24)
        ctk.CTkButton(bottom, text="Save", width=120, height=36,
                      corner_radius=P["radius"], fg_color=P["accent"],
                      hover_color=P["accent_hover"], text_color=P["accent_text"],
                      command=self.save).pack(side="right", padx=24, pady=12)

        self.show_page("General")
        self.after(200, self.lift)

    # ---------- نوار کناری ----------
    def build_sidebar(self):
        side = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color=P["panel"])
        side.grid(row=0, column=0, sticky="ns")
        side.pack_propagate(False)

        ctk.CTkLabel(side, text="Settings", font=("Segoe UI", 20, "bold")
                     ).pack(anchor="w", padx=20, pady=(20, 16))

        self.tab_buttons = {}
        for name in ["General", "Appearance", "Game", "Advanced"]:
            btn = ctk.CTkButton(side, text=name, anchor="w", height=38,
                                corner_radius=P["radius"], fg_color="transparent",
                                hover_color=P["btn"], text_color=P["text"],
                                command=lambda n=name: self.show_page(n))
            btn.pack(fill="x", padx=12, pady=2)
            self.tab_buttons[name] = btn

    def show_page(self, name):
        self.page_title.configure(text=name)
        for key, page in self.pages.items():
            if key == name:
                page.grid()
            else:
                page.grid_remove()
        for key, btn in self.tab_buttons.items():
            btn.configure(fg_color=P["btn"] if key == name else "transparent")

    # ---------- ابزارهای ساخت ردیف ----------
    def new_page(self, parent):
        return ctk.CTkScrollableFrame(parent, fg_color="transparent")

    def section(self, parent, text):
        ctk.CTkLabel(parent, text=text, anchor="w", font=BOLD
                     ).pack(fill="x", padx=8, pady=(14, 4))

    def make_row(self, parent, title, desc):
        row = ctk.CTkFrame(parent, fg_color=P["row"], corner_radius=P["radius"])
        row.pack(fill="x", pady=2, padx=4)
        row.grid_columnconfigure(0, weight=1)

        text = ctk.CTkFrame(row, fg_color="transparent")
        text.grid(row=0, column=0, sticky="w", padx=16, pady=12)
        ctk.CTkLabel(text, text=title, anchor="w", font=BOLD).pack(anchor="w")
        ctk.CTkLabel(text, text=desc, anchor="w", justify="left", wraplength=440,
                     text_color=P["gray"], font=SMALL).pack(anchor="w")

        right = ctk.CTkFrame(row, fg_color="transparent")
        right.grid(row=0, column=1, sticky="e", padx=16)
        return row, right

    def add_switch(self, page, title, desc, key, command=None):
        _, right = self.make_row(page, title, desc)
        var = ctk.BooleanVar(value=self.s[key])
        ctk.CTkSwitch(right, text="", width=46, progress_color=P["accent"],
                      variable=var, command=command).pack()
        self.bool_vars[key] = var
        return var

    def add_slider(self, page, title, desc, key, lo, hi, steps, fmt):
        row, right = self.make_row(page, title, desc)
        var = ctk.DoubleVar(value=self.s[key])
        label = ctk.CTkLabel(right, text=fmt % self.s[key], font=("Segoe UI", 14, "bold"))
        label.pack()
        ctk.CTkSlider(row, from_=lo, to=hi, number_of_steps=steps, variable=var,
                      progress_color=P["accent"], button_color=P["accent"],
                      button_hover_color=P["accent_hover"],
                      command=lambda v: label.configure(text=fmt % v)
                      ).grid(row=1, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 14))
        return var

    def path_line(self, row, var, browse_cmd):
        line = ctk.CTkFrame(row, fg_color="transparent")
        line.grid(row=1, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 12))
        line.grid_columnconfigure(0, weight=1)
        entry = ctk.CTkEntry(line, textvariable=var, fg_color=P["btn"], border_width=0,
                             corner_radius=P["radius"])
        entry.grid(row=0, column=0, sticky="ew")
        btn = ctk.CTkButton(line, text="Browse", width=90, corner_radius=P["radius"],
                            fg_color=P["btn"], hover_color=P["btn_hover"],
                            text_color=P["text"], command=browse_cmd)
        btn.grid(row=0, column=1, padx=(8, 0))
        return entry, btn

    def small_button(self, parent, text, command, danger=False):
        return ctk.CTkButton(parent, text=text, width=110, height=32,
                             corner_radius=P["radius"],
                             fg_color="#7a1f1f" if danger else P["btn"],
                             hover_color="#a02828" if danger else P["btn_hover"],
                             text_color="white" if danger else P["text"],
                             command=command)

    # ---------- صفحه General ----------
    def build_general_page(self, parent):
        page = self.new_page(parent)

        self.section(page, "Launcher")
        self.add_switch(page, "Remember Last Version",
                        "Select the version you played last when the launcher opens.",
                        "remember_version")
        self.add_switch(page, "Show Snapshots by Default",
                        "Include snapshots and old versions in the version list at startup.",
                        "show_snapshots")
        self.add_switch(page, "Close Launcher When Game Starts",
                        "Automatically close the launcher after Minecraft is launched.",
                        "close_on_launch")
        return page

    # ---------- صفحه Appearance ----------
    def build_appearance_page(self, parent):
        page = self.new_page(parent)
        s = self.s

        self.section(page, "Theme")

        _, right = self.make_row(page, "Theme",
                                 "Select a theme to customize the look and feel of the launcher.")
        self.theme_seg = ctk.CTkSegmentedButton(
            right, values=list(THEME_NAMES.values()),
            selected_color=P["accent"], selected_hover_color=P["accent_hover"],
            unselected_color=P["btn"], unselected_hover_color=P["btn_hover"],
            fg_color=P["btn"], text_color=P["text"])
        self.theme_seg.set(THEME_NAMES.get(s["theme"], "Dark"))
        self.theme_seg.pack()

        row, right = self.make_row(page, "Accent Color",
                                   "Select the accent color for the launcher.")
        self.accent_var = ctk.StringVar(value=s["accent"])
        self.accent_btn = ctk.CTkButton(right, text="", width=44, height=30, corner_radius=8,
                                        fg_color=s["accent"], hover_color=s["accent"],
                                        command=self.pick_accent)
        self.accent_btn.pack()
        swatches = ctk.CTkFrame(row, fg_color="transparent")
        swatches.grid(row=1, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 12))
        for color in theme.ACCENT_PRESETS:
            ctk.CTkButton(swatches, text="", width=28, height=28, corner_radius=14,
                          fg_color=color, hover_color=theme.darken(color),
                          command=lambda c=color: self.set_accent(c)
                          ).pack(side="left", padx=(0, 6))

        self.add_switch(page, "Dynamic Accent Colors",
                        "Automatically apply a random accent color every time the launcher opens.",
                        "dynamic_accent")

        self.section(page, "Layout")
        self.radius_var = self.add_slider(
            page, "Corner Radius", "Adjust the corner radius used throughout the launcher.",
            "corner_radius", 0, 25, 25, "%d")
        self.opacity_var = self.add_slider(
            page, "Opacity", "Adjust the transparency level of the launcher window.",
            "opacity", 50, 100, 50, "%d%%")

        self.section(page, "Accessibility")
        _, right = self.make_row(page, "Motion Preference",
                                 "Choose how motion and animations behave in the launcher.")
        self.motion_var = ctk.StringVar(value=MOTION_NAMES.get(s["motion"], "System Setting"))
        ctk.CTkOptionMenu(right, values=list(MOTION_NAMES.values()), variable=self.motion_var,
                          width=160, corner_radius=P["radius"], fg_color=P["btn"],
                          button_color=P["btn_hover"], button_hover_color=P["accent"],
                          text_color=P["text"]).pack()
        return page

    def set_accent(self, color):
        self.accent_var.set(color)
        self.accent_btn.configure(fg_color=color, hover_color=color)

    def pick_accent(self):
        result = colorchooser.askcolor(color=self.accent_var.get(), parent=self)
        if result and result[1]:
            self.set_accent(result[1])

    # ---------- صفحه Game ----------
    def build_game_page(self, parent):
        page = self.new_page(parent)
        s = self.s

        self.section(page, "Display")
        self.add_switch(page, "Fullscreen",
                        "Configure that the game should launch in fullscreen or not.",
                        "fullscreen")

        _, right = self.make_row(page, "Default Game Resolution",
                                 "Turn off to use a custom window size.")
        self.default_res_var = ctk.BooleanVar(value=s["use_default_resolution"])
        self.bool_vars["use_default_resolution"] = self.default_res_var
        ctk.CTkSwitch(right, text="", width=46, progress_color=P["accent"],
                      variable=self.default_res_var, command=self.update_res_state
                      ).pack(side="right", padx=(12, 0))
        self.width_var = ctk.StringVar(value=str(s["width"]))
        self.height_var = ctk.StringVar(value=str(s["height"]))
        self.width_entry = ctk.CTkEntry(right, textvariable=self.width_var, width=70,
                                        justify="center", fg_color=P["btn"], border_width=0)
        self.width_entry.pack(side="left")
        ctk.CTkLabel(right, text="×").pack(side="left", padx=4)
        self.height_entry = ctk.CTkEntry(right, textvariable=self.height_var, width=70,
                                         justify="center", fg_color=P["btn"], border_width=0)
        self.height_entry.pack(side="left")
        self.update_res_state()

        self.section(page, "Directory")
        row, right = self.make_row(page, "Use Default Storage Directory",
                                   "When enabled, the launcher uses its default folder for game data.")
        self.default_dir_var = ctk.BooleanVar(value=s["use_default_storage"])
        self.bool_vars["use_default_storage"] = self.default_dir_var
        ctk.CTkSwitch(right, text="", width=46, progress_color=P["accent"],
                      variable=self.default_dir_var, command=self.update_dir_state).pack()
        self.storage_var = ctk.StringVar(value=s["storage_dir"] or engine.DEFAULT_MC_DIR)
        self.dir_entry, self.dir_btn = self.path_line(row, self.storage_var, self.pick_dir)
        self.update_dir_state()

        self.section(page, "Runtime")
        row, right = self.make_row(page, "Allocated Memory",
                                   "Adjust the amount of RAM allocated to the game.")
        self.ram_var = ctk.DoubleVar(value=min(max(s["ram_mb"], 512), self.ram_max))
        self.ram_label = ctk.CTkLabel(right, text="", font=("Segoe UI", 14, "bold"))
        self.ram_label.pack()

        box = ctk.CTkFrame(row, fg_color="transparent")
        box.grid(row=1, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 12))
        box.grid_columnconfigure(0, weight=1)
        ctk.CTkSlider(box, from_=512, to=self.ram_max,
                      number_of_steps=max(1, (self.ram_max - 512) // 256),
                      variable=self.ram_var, progress_color=P["accent"],
                      button_color=P["accent"], button_hover_color=P["accent_hover"],
                      command=self.on_ram).grid(row=0, column=0, sticky="ew", pady=(0, 8))
        presets = ctk.CTkFrame(box, fg_color="transparent")
        presets.grid(row=1, column=0, sticky="w")
        self.add_preset(presets, "2.5 GB", 2560)
        for gb in (2, 4, 6):
            self.add_preset(presets, str(gb), gb * 1024)
        self.on_ram(self.ram_var.get())

        row, _ = self.make_row(page, "JVM Arguments",
                               "Enter custom JVM arguments for advanced configuration.")
        self.jvm_box = ctk.CTkTextbox(row, height=80, fg_color=P["btn"])
        self.jvm_box.grid(row=1, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 12))
        self.jvm_box.insert("1.0", s["jvm_args"])

        row, _ = self.make_row(page, "Java Path",
                               "Leave empty to let the launcher pick Java automatically (recommended).")
        self.java_var = ctk.StringVar(value=s["java_path"])
        self.path_line(row, self.java_var, self.pick_java)
        return page

    def add_preset(self, parent, text, mb):
        if mb <= self.ram_max:
            ctk.CTkButton(parent, text=text, width=70, height=30,
                          corner_radius=P["radius"], fg_color=P["btn"],
                          hover_color=P["btn_hover"], text_color=P["text"],
                          command=lambda m=mb: self.set_ram(m)).pack(side="left", padx=(0, 6))

    def set_ram(self, mb):
        self.ram_var.set(mb)
        self.on_ram(mb)

    def on_ram(self, value):
        self.ram_label.configure(text="%d MB" % int(value))

    def update_res_state(self):
        state = "disabled" if self.default_res_var.get() else "normal"
        self.width_entry.configure(state=state)
        self.height_entry.configure(state=state)

    def update_dir_state(self):
        state = "disabled" if self.default_dir_var.get() else "normal"
        self.dir_entry.configure(state=state)
        self.dir_btn.configure(state=state)

    def pick_dir(self):
        path = filedialog.askdirectory(parent=self)
        if path:
            self.storage_var.set(path)

    def pick_java(self):
        path = filedialog.askopenfilename(
            parent=self, filetypes=[("Java", "java.exe javaw.exe"), ("All files", "*.*")])
        if path:
            self.java_var.set(path)

    # ---------- صفحه Advanced ----------
    def build_advanced_page(self, parent):
        page = self.new_page(parent)

        self.section(page, "Application")
        row, _ = self.make_row(page, "Application Folders",
                               "Open folders used by the launcher and Minecraft. "
                               "Only modify their contents if you know what you're doing.")
        box = ctk.CTkFrame(row, fg_color="transparent")
        box.grid(row=1, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 12))
        folders = [
            ("Launcher", lambda: engine.BASE_DIR),
            ("Minecraft", engine.get_mc_dir),
            ("Versions", engine.get_versions_dir),
            ("Logs", engine.get_logs_dir),
        ]
        for i, (name, getter) in enumerate(folders):
            box.grid_columnconfigure(i, weight=1)
            ctk.CTkButton(box, text=name, height=34, corner_radius=P["radius"],
                          fg_color=P["btn"], hover_color=P["btn_hover"],
                          text_color=P["text"],
                          command=lambda g=getter: self.open_folder(g())
                          ).grid(row=0, column=i, sticky="ew", padx=3)

        self.section(page, "Maintenance")
        _, right = self.make_row(page, "Restart App",
                                 "Restart the launcher to apply changes or fix issues.")
        self.small_button(right, "Restart", self.restart).pack()

        _, right = self.make_row(page, "Reset Settings",
                                 "Reset all settings to their default values.")
        self.small_button(right, "Reset", self.reset, danger=True).pack()
        return page

    def open_folder(self, path):
        os.makedirs(path, exist_ok=True)
        os.startfile(path)

    def restart(self):
        self.parent.restart_app()

    def reset(self):
        if messagebox.askyesno("Reset Settings",
                               "Reset ALL settings to default?\nThe launcher will restart.",
                               parent=self):
            engine.reset_settings()
            self.parent.restart_app()

    # ---------- ذخیره ----------
    def save(self):
        s = engine.load_settings()

        for key, var in self.bool_vars.items():
            s[key] = var.get()

        try:
            s["width"] = int(self.width_var.get())
            s["height"] = int(self.height_var.get())
        except ValueError:
            pass
        s["storage_dir"] = self.storage_var.get().strip()
        s["ram_mb"] = int(self.ram_var.get())
        s["jvm_args"] = self.jvm_box.get("1.0", "end").strip()
        s["java_path"] = self.java_var.get().strip()

        s["theme"] = REV_THEME.get(self.theme_seg.get(), "dark")
        s["accent"] = self.accent_var.get()
        s["corner_radius"] = int(self.radius_var.get())
        s["opacity"] = int(self.opacity_var.get())
        s["motion"] = REV_MOTION.get(self.motion_var.get(), "system")

        engine.save_settings(s)
        self.parent.apply_opacity(s["opacity"])

        changed = any(s[k] != self.old[k] for k in APPEARANCE_KEYS)
        self.old = dict(s)
        if changed:
            self.saved_label.configure(text="Saved ✓  (restart the app to apply the new look)")
        else:
            self.saved_label.configure(text="Saved ✓")
        self.after(4000, self.clear_saved)

    def clear_saved(self):
        if self.winfo_exists():
            self.saved_label.configure(text="")