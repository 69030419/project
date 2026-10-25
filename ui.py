"""ui.py - หน้าจอของระบบร้านเช่าเครื่องเกม (Tkinter + ttkbootstrap)
กฎ: ไฟล์นี้เรียกได้เฉพาะ logic.py เท่านั้น (ห้าม import database)
ติดตั้ง: pip install ttkbootstrap
"""
import os
import tkinter as tk
from datetime import date
from tkinter import messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import BOTH, LEFT, RIGHT, X, Y, YES

import logic

FONT = ("Leelawadee UI", 11)
FONT_BOLD = ("Leelawadee UI", 11, "bold")
FONT_TITLE = ("Leelawadee UI", 20, "bold")

THEME_DARK = "darkly"
THEME_LIGHT = "flatly"

STATUS_TH = {"available": "ว่าง", "rented": "ถูกเช่า"}
PLATFORMS = ["PS5", "PS4", "Xbox Series X", "Xbox One", "Nintendo Switch", "Steam Deck"]

COLOR_OK = "#20c997"
COLOR_WARN = "#fd7e14"
COLOR_BAD = "#ff4d5e"


def make_tree(parent, columns):
    """columns = [(key, หัวตาราง, ความกว้าง), ...] คืน Treeview ที่มี scrollbar"""
    frame = ttk.Frame(parent)
    frame.pack(fill=BOTH, expand=YES)
    tree = ttk.Treeview(frame, columns=[c[0] for c in columns],
                        show="headings", bootstyle="primary")
    for key, heading, width in columns:
        tree.heading(key, text=heading)
        tree.column(key, width=width, anchor="center")
    scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview,
                           bootstyle="round")
    tree.configure(yscrollcommand=scroll.set)
    tree.pack(side=LEFT, fill=BOTH, expand=YES)
    scroll.pack(side=RIGHT, fill=Y)
    tree.tag_configure("ok", foreground=COLOR_OK)
    tree.tag_configure("warn", foreground=COLOR_WARN)
    tree.tag_configure("bad", foreground=COLOR_BAD)
    return tree


def show_value(value):
    if value is None or value == "":
        return "-"
    if isinstance(value, float):
        return f"{value:,.0f}"
    return value


def fill_tree(tree, rows, keys, tag_fn=None):
    tree.delete(*tree.get_children())
    for row in rows:
        tags = (tag_fn(row),) if tag_fn else ()
        tree.insert("", "end", iid=str(row[keys[0]]),
                    values=[show_value(row.get(k)) for k in keys], tags=tags)


class App(ttk.Window):
    def __init__(self):
        super().__init__(themename=THEME_DARK)
        self.title("ร้านเช่าเครื่องเกม")
        self.geometry("980x620")
        self.minsize(860, 540)
        self.set_app_icon()

        self.available_map = {}   # ข้อความใน combobox -> console_id
        self.rate_map = {}        # console_id -> ราคา/วัน (ใช้โชว์ราคาโดยประมาณ)

        self.rent_console = tk.StringVar()
        self.rent_name = tk.StringVar()
        self.rent_phone = tk.StringVar()
        self.rent_days = tk.StringVar(value="1")
        self.rent_estimate = tk.StringVar(value="ราคาโดยประมาณ: -")

        self.new_name = tk.StringVar()
        self.new_platform = tk.StringVar()
        self.new_rate = tk.StringVar()

        self.apply_style()
        self.build_header()

        self.notebook = ttk.Notebook(self, bootstyle="primary")
        self.notebook.pack(fill=BOTH, expand=YES, padx=16, pady=(0, 16))

        self.build_consoles_tab()
        self.build_rent_tab()
        self.build_return_tab()
        self.build_history_tab()
        self.build_add_console_tab()

        self.rent_console.trace_add("write", self.update_estimate)
        self.rent_days.trace_add("write", self.update_estimate)
        self.notebook.bind("<<NotebookTabChanged>>", lambda e: self.refresh_all())
        self.refresh_all()

    # ---------- สไตล์ / หัวเรื่อง ----------
    def set_app_icon(self):
        """ตั้งค่าไอคอนหน้าต่าง (รองรับทั้ง icon.png และ icon.ico ในโฟลเดอร์เดียวกัน)"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        png_path = os.path.join(base_dir, "icon.png")
        ico_path = os.path.join(base_dir, "icon.ico")

        try:
            if os.path.exists(png_path):
                self._icon_img = tk.PhotoImage(file=png_path)
                self.iconphoto(False, self._icon_img)
            elif os.path.exists(ico_path):
                self.iconbitmap(ico_path)
        except Exception:
            pass  # ถ้าไม่มีไฟล์หรือโหลดไม่ได้ ให้ใช้ไอคอนเริ่มต้นของระบบ

    def apply_style(self):
        self.style.configure(".", font=FONT)
        self.style.configure("Treeview", font=FONT, rowheight=34)
        self.style.configure("Treeview.Heading", font=FONT_BOLD)
        self.style.configure("TNotebook.Tab", font=FONT_BOLD, padding=(16, 8))

    def build_header(self):
        header = ttk.Frame(self, padding=(20, 16, 20, 10))
        header.pack(fill=X)
        ttk.Label(header, text="ร้านเช่าเครื่องเกม", font=FONT_TITLE,
                  bootstyle="primary").pack(side=LEFT)
        ttk.Button(header, text="สลับโหมดมืด/สว่าง", bootstyle="secondary-outline",
                   command=self.toggle_theme).pack(side=RIGHT)

    def toggle_theme(self):
        new_theme = THEME_LIGHT if self.style.theme.name == THEME_DARK else THEME_DARK
        self.style.theme_use(new_theme)
        self.apply_style()

    # ---------- แท็บ 1: รายการเครื่อง ----------
    def build_consoles_tab(self):
        tab = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(tab, text="  รายการเครื่อง  ")
        self.consoles_keys = ["console_id", "name", "platform", "daily_rate", "status_th"]
        self.consoles_tree = make_tree(tab, [
            ("console_id", "รหัส", 70), ("name", "ชื่อเครื่อง", 240),
            ("platform", "แพลตฟอร์ม", 140), ("daily_rate", "ราคา/วัน (บาท)", 140),
            ("status_th", "สถานะ", 120)])
        ttk.Button(tab, text="รีเฟรช", bootstyle="primary-outline",
                   command=self.refresh_all).pack(pady=(10, 0))

    # ---------- แท็บ 2: เช่าเครื่อง ----------
    def build_rent_tab(self):
        tab = ttk.Frame(self.notebook, padding=24)
        self.notebook.add(tab, text="  เช่าเครื่อง  ")

        box = ttk.Labelframe(tab, text=" ข้อมูลการเช่า ", padding=24,
                             bootstyle="primary")
        box.pack(anchor="n", pady=8)

        ttk.Label(box, text="เลือกเครื่อง").grid(row=0, column=0, sticky="e", pady=8, padx=8)
        self.rent_combo = ttk.Combobox(box, textvariable=self.rent_console,
                                       state="readonly", width=38, font=FONT)
        self.rent_combo.grid(row=0, column=1, pady=8)

        ttk.Label(box, text="ชื่อลูกค้า").grid(row=1, column=0, sticky="e", pady=8, padx=8)
        ttk.Entry(box, textvariable=self.rent_name, width=40,
                  font=FONT).grid(row=1, column=1, pady=8)

        ttk.Label(box, text="เบอร์โทร").grid(row=2, column=0, sticky="e", pady=8, padx=8)
        ttk.Entry(box, textvariable=self.rent_phone, width=40,
                  font=FONT).grid(row=2, column=1, pady=8)

        ttk.Label(box, text="จำนวนวัน").grid(row=3, column=0, sticky="e", pady=8, padx=8)
        ttk.Spinbox(box, from_=1, to=30, textvariable=self.rent_days,
                    width=8, font=FONT).grid(row=3, column=1, sticky="w", pady=8)

        ttk.Label(box, textvariable=self.rent_estimate, font=FONT_BOLD,
                  bootstyle="warning").grid(row=4, column=0, columnspan=2, pady=(12, 4))

        ttk.Button(box, text="ยืนยันการเช่า", bootstyle="success", width=24,
                   command=self.on_rent).grid(row=5, column=0, columnspan=2, pady=(10, 0))

    def update_estimate(self, *_):
        rate = self.rate_map.get(self.available_map.get(self.rent_console.get()))
        try:
            days = int(self.rent_days.get())
        except ValueError:
            days = None
        if rate is None or days is None:
            self.rent_estimate.set("ราคาโดยประมาณ: -")
        else:
            self.rent_estimate.set(f"ราคาโดยประมาณ: {rate * days:,.0f} บาท")

    def on_rent(self):
        console_id = self.available_map.get(self.rent_console.get())
        if console_id is None:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกเครื่อง")
            return
        ok, message = logic.add_rental(console_id, self.rent_name.get().strip(),
                                       self.rent_phone.get().strip(), self.rent_days.get())
        if ok:
            messagebox.showinfo("สำเร็จ", message)
            self.rent_name.set("")
            self.rent_phone.set("")
            self.rent_days.set("1")
            self.rent_console.set("")
            self.refresh_all()
        else:
            messagebox.showerror("ไม่สำเร็จ", message)

    # ---------- แท็บ 3: คืนเครื่อง ----------
    def build_return_tab(self):
        tab = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(tab, text="  คืนเครื่อง  ")
        self.active_keys = ["rental_id", "console_name", "customer_name",
                            "phone", "rent_date", "due_date"]
        self.return_tree = make_tree(tab, [
            ("rental_id", "รหัสเช่า", 80), ("console_name", "เครื่อง", 180),
            ("customer_name", "ลูกค้า", 170), ("phone", "เบอร์โทร", 130),
            ("rent_date", "วันที่เช่า", 120), ("due_date", "กำหนดคืน", 120)])
        ttk.Label(tab, text="แถวสีแดง = เกินกำหนดคืนแล้ว (มีค่าปรับ)",
                  bootstyle="danger").pack(pady=(8, 0))
        ttk.Button(tab, text="คืนเครื่องที่เลือก", bootstyle="success",
                   command=self.on_return).pack(pady=(8, 0))

    def on_return(self):
        selected = self.return_tree.selection()
        if not selected:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกรายการที่ต้องการคืน")
            return
        if not messagebox.askyesno("ยืนยัน", "ต้องการคืนเครื่องรายการนี้ใช่ไหม"):
            return
        ok, message = logic.return_console(int(selected[0]))
        if ok:
            messagebox.showinfo("คืนเครื่องสำเร็จ", message)
            self.refresh_all()
        else:
            messagebox.showerror("ไม่สำเร็จ", message)

    # ---------- แท็บ 4: ประวัติการเช่า ----------
    def build_history_tab(self):
        tab = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(tab, text="  ประวัติการเช่า  ")
        self.history_keys = ["rental_id", "console_name", "customer_name", "rent_date",
                             "due_date", "return_date", "total_price"]
        self.history_tree = make_tree(tab, [
            ("rental_id", "รหัส", 60), ("console_name", "เครื่อง", 150),
            ("customer_name", "ลูกค้า", 150), ("rent_date", "เช่า", 110),
            ("due_date", "กำหนดคืน", 110), ("return_date", "คืนจริง", 110),
            ("total_price", "ราคารวม (บาท)", 120)])

    # ---------- แท็บ 5: เพิ่มเครื่อง ----------
    def build_add_console_tab(self):
        tab = ttk.Frame(self.notebook, padding=24)
        self.notebook.add(tab, text="  เพิ่มเครื่อง  ")

        box = ttk.Labelframe(tab, text=" ข้อมูลเครื่องใหม่ ", padding=24,
                             bootstyle="info")
        box.pack(anchor="n", pady=8)

        ttk.Label(box, text="ชื่อเครื่อง").grid(row=0, column=0, sticky="e", pady=8, padx=8)
        ttk.Entry(box, textvariable=self.new_name, width=40,
                  font=FONT).grid(row=0, column=1, pady=8)

        ttk.Label(box, text="แพลตฟอร์ม").grid(row=1, column=0, sticky="e", pady=8, padx=8)
        ttk.Combobox(box, textvariable=self.new_platform, values=PLATFORMS,
                     width=38, font=FONT).grid(row=1, column=1, pady=8)

        ttk.Label(box, text="ราคา/วัน (บาท)").grid(row=2, column=0, sticky="e", pady=8, padx=8)
        ttk.Entry(box, textvariable=self.new_rate, width=14,
                  font=FONT).grid(row=2, column=1, sticky="w", pady=8)

        ttk.Button(box, text="เพิ่มเครื่อง", bootstyle="info", width=24,
                   command=self.on_add_console).grid(row=3, column=0, columnspan=2,
                                                     pady=(16, 0))

    def on_add_console(self):
        ok, message = logic.add_console(self.new_name.get().strip(),
                                        self.new_platform.get().strip(),
                                        self.new_rate.get().strip())
        if ok:
            messagebox.showinfo("สำเร็จ", message)
            self.new_name.set("")
            self.new_platform.set("")
            self.new_rate.set("")
            self.notebook.select(0)   # กลับไปแท็บรายการเครื่อง (จะรีเฟรชเอง)
            self.refresh_all()
        else:
            messagebox.showerror("ไม่สำเร็จ", message)

    # ---------- โหลดข้อมูลใหม่ ----------
    def refresh_all(self):
        consoles = logic.get_all_consoles()
        rows = [dict(c, status_th=STATUS_TH.get(c["status"], c["status"])) for c in consoles]
        fill_tree(self.consoles_tree, rows, self.consoles_keys,
                  tag_fn=lambda r: "ok" if r["status"] == "available" else "warn")

        available = logic.get_available_consoles()
        self.available_map = {
            f"{c['console_id']} - {c['name']} ({c['daily_rate']:.0f} บาท/วัน)": c["console_id"]
            for c in available}
        self.rate_map = {c["console_id"]: c["daily_rate"] for c in available}
        self.rent_combo["values"] = list(self.available_map.keys())
        if self.rent_console.get() not in self.available_map:
            self.rent_console.set("")

        rentals = logic.get_all_rentals()
        today = date.today().isoformat()
        active = [r for r in rentals if r.get("return_date") is None]
        fill_tree(self.return_tree, active, self.active_keys,
                  tag_fn=lambda r: "bad" if r["due_date"] < today else "")
        fill_tree(self.history_tree, rentals, self.history_keys)

        self.update_estimate()


if __name__ == "__main__":
    App().mainloop()
