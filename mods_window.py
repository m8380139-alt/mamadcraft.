import os
import threading
import customtkinter as ctk

import appicon
import engine
import theme

P = theme.get()
R = P["radius"]


class ModsWindow(ctk.CTkToplevel):
    def __init__(self, parent, version):
        super().__init__(parent)
        self.parent = parent
        self.version = version
        self.mc_version = engine.get_parent_version(version) or version
        self.busy = False

        self.title("Mods")
        appicon.apply(self)
        self.geometry("580x680")
        self.minsize(520, 520)
        self.configure(fg_color=P["bg"])

        head = ctk.CTkFrame(self, fg_color=P["panel"], corner_radius=0)
        head.pack(fill="x")
        ctk.CTkLabel(head, text="Mods", font=("Segoe UI", 20, "bold")
                     ).pack(anchor="w", padx=22, pady=(18, 0))
        ctk.CTkLabel(head, text="Fabric for Minecraft " + self.mc_version,
                     text_color=P["gray"], font=("Segoe UI", 12)
                     ).pack(anchor="w", padx=22, pady=(0, 10))

        buttons = ctk.CTkFrame(head, fg_color="transparent")
        buttons.pack(fill="x", padx=22, pady=(0, 16))
        self.pack_btn = ctk.CTkButton(buttons, text="⚡ Install optimization pack", height=40,
                                      corner_radius=R, fg_color=P["accent"],
                                      hover_color=P["accent_hover"],
                                      text_color=P["accent_text"],
                                      font=("Segoe UI", 14, "bold"),
                                      command=self.install_pack)
        self.pack_btn.pack(side="left")
        ctk.CTkButton(buttons, text="Open mods folder", height=40, corner_radius=R,
                      fg_color=P["btn"], hover_color=P["btn_hover"], text_color=P["text"],
                      command=self.open_folder).pack(side="left", padx=(10, 0))

        self.status = ctk.CTkLabel(self, text="", text_color=P["gray"], anchor="w",
                                   justify="left", wraplength=520)
        self.status.pack(fill="x", padx=26, pady=(8, 0))

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=12, pady=(4, 12))

        self.render()
        self.after(200, self.lift)

    # ---------- نمایش ----------
    def render(self):
        for child in self.list_frame.winfo_children():
            child.destroy()

        installed = engine.installed_mod_slugs(self.version)
        for slug, name, desc in engine.RECOMMENDED_MODS:
            row = ctk.CTkFrame(self.list_frame, fg_color=P["row"], corner_radius=R)
            row.pack(fill="x", pady=3, padx=4)
            row.grid_columnconfigure(0, weight=1)

            info = ctk.CTkFrame(row, fg_color="transparent")
            info.grid(row=0, column=0, sticky="w", padx=16, pady=10)
            ctk.CTkLabel(info, text=name, anchor="w", font=("Segoe UI", 14, "bold")
                         ).pack(anchor="w")
            ctk.CTkLabel(info, text=desc, anchor="w", justify="left", wraplength=330,
                         text_color=P["gray"], font=("Segoe UI", 12)).pack(anchor="w")

            if slug in installed:
                ctk.CTkLabel(row, text="✓ Installed", text_color="#4caf50",
                             font=("Segoe UI", 12, "bold")
                             ).grid(row=0, column=1, padx=16)
            else:
                ctk.CTkButton(row, text="Install", width=90, height=32, corner_radius=R,
                              fg_color=P["accent"], hover_color=P["accent_hover"],
                              text_color=P["accent_text"],
                              command=lambda s=slug: self.run_jobs([s])
                              ).grid(row=0, column=1, padx=16)

    def set_status(self, text):
        if self.winfo_exists():
            self.status.configure(text=text)

    # ---------- نصب ----------
    def install_pack(self):
        self.run_jobs(engine.PACK_SLUGS)

    def run_jobs(self, slugs):
        if self.busy:
            return
        self.busy = True
        self.pack_btn.configure(state="disabled")
        self.set_status("Starting...")
        threading.Thread(target=self.worker, args=(list(slugs),), daemon=True).start()

    def worker(self, slugs):
        errors = []
        have = engine.installed_mod_slugs(self.version)
        for slug in slugs:
            if slug in have:
                continue
            self.after(0, lambda s=slug: self.set_status("Downloading " + s + "..."))
            try:
                engine.install_mod(self.version, slug, self.mc_version)
            except Exception as e:
                print("MOD ERROR:", slug, e)
                errors.append(slug + ": " + str(e)[:110])
        self.after(0, lambda: self.finished(errors))

    def finished(self, errors):
        if not self.winfo_exists():
            return
        self.busy = False
        self.pack_btn.configure(state="normal")
        if errors:
            self.set_status("Some mods failed (VPN? / not available for this version):\n"
                            + "\n".join(errors[:3]))
        else:
            self.set_status("Done ✓")
        self.render()

    def open_folder(self):
        os.startfile(engine.mods_dir(self.version))
