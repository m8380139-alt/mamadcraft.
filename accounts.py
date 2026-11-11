import os
import re
import json
import customtkinter as ctk
from tkinter import messagebox

import appicon
import paths
import theme

P = theme.get()
R = P["radius"]

ACCOUNT_FILE = os.path.join(paths.DATA_DIR, "account.json")
NAME_RE = re.compile(r"^[A-Za-z0-9_]{3,16}$")


# ---------- ذخیره‌ی اکانت‌ها ----------
def _read():
    try:
        with open(ACCOUNT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _write(data):
    try:
        with open(ACCOUNT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print("Could not save accounts:", e)


def load_name():
    """اکانت انتخاب‌شده (اگه نبود، Player)"""
    return _read().get("name", "Player")


def load_accounts():
    data = _read()
    accounts = list(data.get("accounts", []))
    name = data.get("name")
    if name and name not in accounts:
        accounts.insert(0, name)
    return accounts


def save_name(name):
    """اسم رو به‌عنوان اکانت فعلی ذخیره می‌کنه و به لیست اضافه می‌کنه"""
    data = _read()
    accounts = load_accounts()
    if name not in accounts:
        accounts.append(name)
    data["name"] = name
    data["accounts"] = accounts
    _write(data)


def delete_account(name):
    data = _read()
    accounts = [a for a in load_accounts() if a != name]
    data["accounts"] = accounts
    if data.get("name") == name:
        data["name"] = accounts[0] if accounts else "Player"
    _write(data)


# ---------- پنجره‌ی اکانت‌ها ----------
class AccountsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Accounts")
        appicon.apply(self)
        self.geometry("460x560")
        self.minsize(420, 480)
        self.configure(fg_color=P["bg"])

        ctk.CTkLabel(self, text="Accounts", font=("Segoe UI", 20, "bold")
                     ).pack(anchor="w", padx=22, pady=(20, 2))
        ctk.CTkLabel(self, text="Offline accounts. Pick the one you want to play with.",
                     text_color=P["gray"], font=("Segoe UI", 12)
                     ).pack(anchor="w", padx=22, pady=(0, 10))

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=12)

        add_box = ctk.CTkFrame(self, fg_color=P["panel"], corner_radius=0)
        add_box.pack(fill="x", side="bottom")
        self.new_var = ctk.StringVar()
        entry = ctk.CTkEntry(add_box, textvariable=self.new_var, height=40, corner_radius=R,
                             fg_color=P["btn"], border_width=0,
                             placeholder_text="New account name")
        entry.pack(side="left", fill="x", expand=True, padx=(18, 8), pady=16)
        entry.bind("<Return>", lambda e: self.add())
        ctk.CTkButton(add_box, text="Add", width=90, height=40, corner_radius=R,
                      fg_color=P["accent"], hover_color=P["accent_hover"],
                      text_color=P["accent_text"], command=self.add
                      ).pack(side="right", padx=(0, 18), pady=16)

        self.refresh()
        self.after(200, self.lift)

    def refresh(self):
        for child in self.list_frame.winfo_children():
            child.destroy()

        current = self.parent.name_var.get().strip()
        accounts = load_accounts()
        if current and current not in accounts:
            accounts.insert(0, current)

        if not accounts:
            ctk.CTkLabel(self.list_frame, text="No accounts yet.",
                         text_color=P["gray"]).pack(pady=30)
            return

        for name in accounts:
            is_current = (name == current)
            row = ctk.CTkFrame(self.list_frame, fg_color=P["row"], corner_radius=R)
            row.pack(fill="x", pady=3, padx=4)
            row.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(row, text=name, anchor="w", font=("Segoe UI", 14, "bold")
                         ).grid(row=0, column=0, sticky="w", padx=16, pady=14)

            ctk.CTkButton(row, text="✕", width=34, height=32, corner_radius=R,
                          fg_color="transparent", hover_color="#a02828",
                          text_color=P["gray"],
                          command=lambda n=name: self.remove(n)
                          ).grid(row=0, column=2, padx=(0, 10))

            ctk.CTkButton(row, text="Selected" if is_current else "Select", width=90,
                          height=32, corner_radius=R,
                          fg_color=P["accent"] if is_current else P["btn"],
                          hover_color=P["accent_hover"] if is_current else P["btn_hover"],
                          text_color=P["accent_text"] if is_current else P["text"],
                          state="disabled" if is_current else "normal",
                          command=lambda n=name: self.select(n)
                          ).grid(row=0, column=1, padx=6)

    def select(self, name):
        self.parent.set_account(name)
        self.refresh()

    def add(self):
        name = self.new_var.get().strip()
        if not NAME_RE.match(name):
            messagebox.showwarning(
                "Accounts",
                "Name must be 3-16 characters: English letters, numbers or underscore (_).",
                parent=self)
            return
        self.parent.set_account(name)
        self.new_var.set("")
        self.refresh()

    def remove(self, name):
        if not messagebox.askyesno("Accounts", "Delete account '" + name + "'?", parent=self):
            return
        was_current = (name == self.parent.name_var.get().strip())
        delete_account(name)
        if was_current:
            self.parent.name_var.set(load_name())
        self.refresh()