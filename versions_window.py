import threading
import customtkinter as ctk

import appicon
import engine
import theme

P = theme.get()
R = P["radius"]

FILTERS = ["Release", "Snapshot", "Old", "All"]
PAGE = 40  # چند ورژن هر بار نشون داده بشه (برای سریع موندن)

KIND_NAMES = {
    "release": "Release",
    "snapshot": "Snapshot",
    "old_beta": "Beta",
    "old_alpha": "Alpha",
}


class VersionsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Versions")
        appicon.apply(self)
        self.geometry("740x700")
        self.minsize(560, 520)
        self.configure(fg_color=P["bg"])

        self.all_versions = []
        self.offline = False
        self.fabric_supported = set()
        self.fabric_done = set()
        self.shown = PAGE

        # --- بالای پنجره ---
        head = ctk.CTkFrame(self, fg_color=P["panel"], corner_radius=0)
        head.pack(fill="x")

        ctk.CTkLabel(head, text="Versions", font=("Segoe UI", 20, "bold")
                     ).pack(anchor="w", padx=22, pady=(18, 0))
        ctk.CTkLabel(head, text="Pick a version to play. Install downloads it without launching.",
                     text_color=P["gray"], font=("Segoe UI", 12)
                     ).pack(anchor="w", padx=22, pady=(0, 10))

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *a: self.on_filter())
        ctk.CTkEntry(head, textvariable=self.search_var, height=40, corner_radius=R,
                     fg_color=P["btn"], border_width=0,
                     placeholder_text="Search (example: 1.21)"
                     ).pack(fill="x", padx=22, pady=(0, 10))

        self.filter_seg = ctk.CTkSegmentedButton(
            head, values=FILTERS, command=lambda v: self.on_filter(),
            selected_color=P["accent"], selected_hover_color=P["accent_hover"],
            unselected_color=P["btn"], unselected_hover_color=P["btn_hover"],
            fg_color=P["btn"], text_color=P["text"])
        self.filter_seg.set("Release")
        self.filter_seg.pack(fill="x", padx=22, pady=(0, 14))

        self.count_label = ctk.CTkLabel(self, text="Loading versions...",
                                        text_color=P["gray"], anchor="w")
        self.count_label.pack(fill="x", padx=26, pady=(8, 0))

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=12, pady=(4, 12))

        threading.Thread(target=self.load, daemon=True).start()
        self.after(200, self.lift)

    # ---------- گرفتن لیست ----------
    def load(self):
        try:
            versions = engine.get_version_infos()
            have = {v["id"] for v in versions}
            custom = [v for v in engine.get_installed_infos() if v["id"] not in have]
            versions = custom + list(versions)
            try:
                supported = set(engine.get_fabric_supported())
            except Exception as e:
                print("Fabric list failed:", e)
                supported = set()
            self.after(0, lambda: self.loaded(versions, False, supported))
        except Exception as e:
            print("ERROR:", e)
            # آفلاین: فقط ورژن‌های نصب‌شده
            installed = engine.get_installed_infos()
            if installed:
                self.after(0, lambda: self.loaded(installed, True))
            else:
                self.after(0, lambda: self.failed())

    def loaded(self, versions, offline=False, supported=None):
        if not self.winfo_exists():
            return
        self.all_versions = versions
        self.offline = offline
        self.fabric_supported = supported or set()
        self.fabric_done = {engine.get_parent_version(v["id"]) for v in versions
                            if v["id"].startswith(engine.FABRIC_PREFIX)}
        if offline:
            self.filter_seg.set("All")
        self.render()

    def failed(self):
        if self.winfo_exists():
            self.count_label.configure(text="Could not load versions (check internet/VPN)")

    # ---------- فیلتر ----------
    def on_filter(self):
        self.shown = PAGE
        self.render()

    def matches(self, v):
        mode = self.filter_seg.get()
        kind = v["type"]
        if mode == "Release" and kind != "release":
            return False
        if mode == "Snapshot" and kind != "snapshot":
            return False
        if mode == "Old" and not kind.startswith("old"):
            return False
        text = self.search_var.get().strip().lower()
        if text and text not in v["id"].lower():
            return False
        return True

    # ---------- نمایش ----------
    def render(self):
        for child in self.list_frame.winfo_children():
            child.destroy()

        found = [v for v in self.all_versions if self.matches(v)]
        shown = found[:self.shown]
        prefix = "Offline - installed only.  " if self.offline else ""
        self.count_label.configure(
            text=prefix + "Showing %d of %d versions" % (len(shown), len(found)))

        if not found:
            ctk.CTkLabel(self.list_frame, text="No versions found.",
                         text_color=P["gray"]).pack(pady=40)
            return

        for v in shown:
            self.add_card(v)

        if len(found) > len(shown):
            ctk.CTkButton(self.list_frame, text="Show more", height=38, corner_radius=R,
                          fg_color=P["btn"], hover_color=P["btn_hover"],
                          text_color=P["text"], command=self.show_more
                          ).pack(pady=10)

    def show_more(self):
        self.shown += PAGE
        self.render()

    def add_card(self, v):
        vid = v["id"]
        kind = v["type"]
        installed = engine.is_installed(vid)

        try:
            date = v["releaseTime"].strftime("%Y-%m-%d")
        except Exception:
            date = ""

        if kind == "release":
            badge_color, badge_text = P["accent"], P["accent_text"]
        elif kind == "snapshot":
            badge_color, badge_text = "#3f51b5", "#ffffff"
        else:
            badge_color, badge_text = "#6d4c41", "#ffffff"

        row = ctk.CTkFrame(self.list_frame, fg_color=P["row"], corner_radius=R)
        row.pack(fill="x", pady=3, padx=4)
        row.grid_columnconfigure(0, weight=1)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.grid(row=0, column=0, sticky="w", padx=16, pady=10)

        top = ctk.CTkFrame(info, fg_color="transparent")
        top.pack(anchor="w")
        ctk.CTkLabel(top, text=vid, font=("Segoe UI", 15, "bold")).pack(side="left")
        ctk.CTkLabel(top, text=KIND_NAMES.get(kind, kind), width=70, height=22,
                     corner_radius=8, fg_color=badge_color, text_color=badge_text,
                     font=("Segoe UI", 11, "bold")).pack(side="left", padx=(10, 0))
        if installed:
            ctk.CTkLabel(top, text="✓ Installed", text_color="#4caf50",
                         font=("Segoe UI", 12, "bold")).pack(side="left", padx=(10, 0))
        ctk.CTkLabel(info, text=date, text_color=P["gray"],
                     font=("Segoe UI", 12)).pack(anchor="w")

        btns = ctk.CTkFrame(row, fg_color="transparent")
        btns.grid(row=0, column=1, padx=12)
        if vid.startswith(engine.FABRIC_PREFIX):
            ctk.CTkButton(btns, text="Mods", width=70, height=32, corner_radius=R,
                          fg_color=P["btn"], hover_color=P["btn_hover"],
                          text_color=P["text"],
                          command=lambda i=vid: self.open_mods(i)).pack(side="left", padx=4)
        elif vid in self.fabric_supported and vid not in self.fabric_done:
            ctk.CTkButton(btns, text="+ Fabric", width=80, height=32, corner_radius=R,
                          fg_color=P["btn"], hover_color=P["btn_hover"],
                          text_color=P["text"],
                          command=lambda i=vid: self.install_fabric(i)).pack(side="left", padx=4)
        if not installed:
            ctk.CTkButton(btns, text="Install", width=80, height=32, corner_radius=R,
                          fg_color=P["btn"], hover_color=P["btn_hover"],
                          text_color=P["text"],
                          command=lambda i=vid: self.install(i)).pack(side="left", padx=4)
        ctk.CTkButton(btns, text="Select", width=80, height=32, corner_radius=R,
                      fg_color=P["accent"], hover_color=P["accent_hover"],
                      text_color=P["accent_text"],
                      command=lambda i=vid: self.select(i)).pack(side="left", padx=4)

    # ---------- کارها ----------
    def select(self, vid):
        self.parent.select_version(vid)
        self.destroy()

    def install(self, vid):
        self.parent.install_only(vid)
        self.destroy()

    def install_fabric(self, vid):
        self.parent.install_fabric(vid)
        self.destroy()

    def open_mods(self, vid):
        self.parent.open_mods(vid)
