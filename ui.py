"""ui.py - หน้าจอของระบบร้านเช่าเครื่องเกม (Tkinter + ttkbootstrap)
กฎ: ไฟล์นี้เรียกได้เฉพาะ logic.py เท่านั้น (ห้าม import database)
ติดตั้ง: pip install ttkbootstrap
"""
import os
import tkinter as tk
from datetime import date
from tkinter import messagebox, simpledialog

import ttkbootstrap as ttk
from ttkbootstrap.constants import BOTH, LEFT, RIGHT, X, Y, YES

import logic

FONT = ("Leelawadee UI", 11)
FONT_BOLD = ("Leelawadee UI", 11, "bold")
FONT_KICKER = ("Leelawadee UI", 9, "bold")
FONT_TITLE = ("Leelawadee UI", 22, "bold")
FONT_SECTION = ("Leelawadee UI", 16, "bold")

THEME_DARK = "darkly"
THEME_LIGHT = "minty"

PALETTE_LIGHT = {
    "canvas": "#edf3ef",
    "surface": "#ffffff",
    "ink": "#20332e",
    "muted": "#6e8179",
    "brand": "#17473d",
    "accent": "#d36f50",
    "line": "#dce7e1",
}
PALETTE_DARK = {
    "canvas": "#17211e",
    "surface": "#202d29",
    "ink": "#e8f0ec",
    "muted": "#adbbb5",
    "brand": "#163b33",
    "accent": "#e58b6c",
    "line": "#3a4b45",
}

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


def rental_status(rental):
    if rental.get("return_date") is not None:
        return "คืนแล้ว"
    if rental.get("return_requested_at") is not None:
        return "รอพนักงานยืนยัน"
    today = date.today().isoformat()
    if rental["due_date"] < today:
        return "เกินกำหนด"
    if rental["due_date"] == today:
        return "ครบกำหนดวันนี้"
    return "กำลังเช่า"


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
        self.geometry("1080x700")
        self.minsize(940, 620)
        self.set_app_icon()
        self.mode = None
        self.database_error_shown = False

        self.available_map = {}   # ข้อความใน combobox -> console_id
        self.rate_map = {}        # console_id -> ราคา/วัน (ใช้โชว์ราคาโดยประมาณ)
        self.customer_console_map = {}

        self.rent_console = tk.StringVar()
        self.rent_name = tk.StringVar()
        self.rent_phone = tk.StringVar()
        self.rent_days = tk.StringVar(value="1")
        self.rent_estimate = tk.StringVar(value="ราคาโดยประมาณ: -")
        self.customer_console = tk.StringVar()
        self.customer_name = tk.StringVar()
        self.customer_phone = tk.StringVar()
        self.customer_days = tk.StringVar(value="1")
        self.customer_estimate = tk.StringVar(value="ราคาโดยประมาณ: -")
        self.customer_lookup_phone = tk.StringVar()

        self.new_name = tk.StringVar()
        self.new_platform = tk.StringVar()
        self.new_rate = tk.StringVar()

        self.apply_style()
        self.rent_console.trace_add("write", self.update_estimate)
        self.rent_days.trace_add("write", self.update_estimate)
        self.customer_console.trace_add("write", self.update_customer_estimate)
        self.customer_days.trace_add("write", self.update_customer_estimate)

        self.build_header()
        self.content = ttk.Frame(self, style="Page.TFrame")
        self.content.pack(fill=BOTH, expand=YES, padx=16, pady=(0, 16))
        self.show_mode_chooser()

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
        palette = (PALETTE_DARK if self.style.theme.name == THEME_DARK
                   else PALETTE_LIGHT)
        self.configure(background=palette["canvas"])
        self.style.configure(".", font=FONT, foreground=palette["ink"])
        self.style.configure("TFrame", background=palette["canvas"])
        self.style.configure("TLabel", background=palette["canvas"],
                             foreground=palette["ink"])
        self.style.configure("TLabelframe", background=palette["surface"],
                             bordercolor=palette["line"])
        self.style.configure("TLabelframe.Label", background=palette["surface"],
                             foreground=palette["brand"], font=FONT_BOLD)
        self.style.configure("Page.TFrame", background=palette["canvas"])
        self.style.configure("Brand.TFrame", background=palette["brand"])
        self.style.configure("Brand.TLabel", background=palette["brand"],
                             foreground="#ffffff")
        self.style.configure("Brand.Kicker.TLabel", background=palette["brand"],
                             foreground="#b7d8ca", font=FONT_KICKER)
        self.style.configure("Muted.TLabel", background=palette["canvas"],
                             foreground=palette["muted"])
        self.style.configure("Section.TLabel", background=palette["surface"],
                             foreground=palette["ink"], font=FONT_SECTION)
        self.style.configure("Treeview", font=FONT, rowheight=40,
                             background=palette["surface"],
                             fieldbackground=palette["surface"],
                             foreground=palette["ink"],
                             bordercolor=palette["line"])
        self.style.configure("Treeview.Heading", font=FONT_BOLD,
                             background=palette["canvas"],
                             foreground=palette["muted"], padding=(10, 10))
        self.style.map("Treeview", background=[("selected", palette["brand"])],
                       foreground=[("selected", "#ffffff")])
        self.style.configure("TNotebook", background=palette["canvas"], borderwidth=0)
        self.style.configure("TNotebook.Tab", font=FONT_BOLD, padding=(18, 11))
        self.style.configure("TEntry", padding=(9, 8))
        self.style.configure("TCombobox", padding=(8, 7))

    def build_header(self):
        header = ttk.Frame(self, padding=(24, 15, 24, 15), style="Brand.TFrame")
        header.pack(fill=X)
        title_block = ttk.Frame(header, style="Brand.TFrame")
        title_block.pack(side=LEFT)
        ttk.Label(title_block, text="GAME RENTAL DESK",
                  style="Brand.Kicker.TLabel").pack(anchor="w")
        ttk.Label(title_block, text="ร้านเช่าเครื่องเกม", font=FONT_TITLE,
                  style="Brand.TLabel").pack(anchor="w", pady=(2, 0))
        ttk.Button(header, text="เลือกโหมด", bootstyle="light-outline",
                   command=self.show_mode_chooser).pack(side=RIGHT, padx=(8, 0))
        self.theme_button = ttk.Button(header, text="ธีมสว่าง", bootstyle="light-outline",
                                       command=self.toggle_theme)
        self.theme_button.pack(side=RIGHT)

    def toggle_theme(self):
        new_theme = THEME_LIGHT if self.style.theme.name == THEME_DARK else THEME_DARK
        self.style.theme_use(new_theme)
        self.apply_style()
        self.theme_button.configure(text="ธีมสว่าง" if new_theme == THEME_DARK else "ธีมมืด")

    def clear_content(self):
        for child in self.content.winfo_children():
            child.destroy()

    def show_mode_chooser(self):
        self.mode = None
        self.clear_content()
        panel = ttk.Frame(self.content, style="Page.TFrame", padding=(28, 38))
        panel.pack(fill=BOTH, expand=YES)
        ttk.Label(panel, text="ยินดีต้อนรับ", font=FONT_TITLE,
                  style="PageTitle.TLabel").pack(anchor="center", pady=(12, 4))
        ttk.Label(panel, text="เลือกโหมดเพื่อเริ่มใช้งาน",
                  style="Muted.TLabel").pack(anchor="center", pady=(0, 26))

        choices = ttk.Frame(panel, style="Page.TFrame")
        choices.pack(fill=X, expand=YES, padx=30)
        customer_card = ttk.Labelframe(choices, text="  สำหรับลูกค้า  ",
                                       padding=24, bootstyle="success")
        customer_card.pack(side=LEFT, fill=BOTH, expand=YES, padx=(0, 10))
        ttk.Label(customer_card, text="เช่าเครื่องเกม", style="Section.TLabel").pack(
            anchor="w", pady=(8, 6))
        ttk.Label(customer_card, text="ดูเครื่องที่ว่าง และจัดการรายการเช่าของคุณ",
                  style="Muted.TLabel", wraplength=320, justify=LEFT).pack(
                      anchor="w", pady=(0, 20))
        ttk.Button(customer_card, text="เข้าใช้งาน", bootstyle="success",
                   command=self.show_customer_mode).pack(anchor="w", ipadx=16, ipady=4)

        staff_card = ttk.Labelframe(choices, text="  สำหรับพนักงาน  ",
                                    padding=24, bootstyle="primary")
        staff_card.pack(side=LEFT, fill=BOTH, expand=YES, padx=(10, 0))
        ttk.Label(staff_card, text="จัดการหน้าร้าน", style="Section.TLabel").pack(
            anchor="w", pady=(8, 6))
        ttk.Label(staff_card, text="จัดการเครื่อง การเช่า การคืน และประวัติ",
                  style="Muted.TLabel", wraplength=320, justify=LEFT).pack(
                      anchor="w", pady=(0, 20))
        ttk.Button(staff_card, text="เข้าสู่ระบบพนักงาน", bootstyle="primary",
                   command=self.request_staff_mode).pack(anchor="w", ipadx=16, ipady=4)

    def request_staff_mode(self):
        pin = simpledialog.askstring("เข้าสู่โหมดพนักงาน", "กรุณาใส่ PIN:", show="*")
        if pin is None:
            return
        if not logic.check_staff_pin(pin):
            messagebox.showerror("เข้าสู่ระบบไม่สำเร็จ", "PIN ไม่ถูกต้อง")
            return
        self.show_staff_mode()

    def show_staff_mode(self):
        self.mode = "staff"
        self.clear_content()
        self.notebook = ttk.Notebook(self.content, bootstyle="primary")
        self.notebook.pack(fill=BOTH, expand=YES)
        self.build_consoles_tab()
        self.build_rent_tab()
        self.build_return_tab()
        self.build_history_tab()
        self.build_add_console_tab()
        self.notebook.bind("<<NotebookTabChanged>>",
                   lambda event: self.refresh_all() if event.widget else None)
        self.refresh_all()

    def show_customer_mode(self):
        self.mode = "customer"
        self.clear_content()
        self.notebook = ttk.Notebook(self.content, bootstyle="success")
        self.notebook.pack(fill=BOTH, expand=YES)
        self.build_customer_available_tab()
        self.build_customer_rent_tab()
        self.build_customer_rentals_tab()
        self.notebook.bind("<<NotebookTabChanged>>",
                   lambda event: self.refresh_all() if event.widget else None)
        self.refresh_all()

    def build_customer_available_tab(self):
        tab = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(tab, text="  เครื่องที่ว่าง  ")
        self.customer_available_tree = make_tree(tab, [
            ("console_id", "รหัส", 80), ("name", "ชื่อเครื่อง", 260),
            ("platform", "แพลตฟอร์ม", 180), ("daily_rate", "ราคา/วัน (บาท)", 160)])
        ttk.Button(tab, text="รีเฟรช", bootstyle="success-outline",
                   command=self.refresh_all).pack(pady=(10, 0))

    def build_customer_rent_tab(self):
        tab = ttk.Frame(self.notebook, padding=24)
        self.notebook.add(tab, text="  เช่าเครื่อง  ")
        box = ttk.Labelframe(tab, text=" ข้อมูลการเช่า ", padding=24,
                             bootstyle="success")
        box.pack(anchor="n", pady=8)

        ttk.Label(box, text="เลือกเครื่อง").grid(row=0, column=0, sticky="e", pady=8, padx=8)
        self.customer_rent_combo = ttk.Combobox(
            box, textvariable=self.customer_console, state="readonly", width=38, font=FONT)
        self.customer_rent_combo.grid(row=0, column=1, pady=8)
        ttk.Label(box, text="ชื่อผู้เช่า").grid(row=1, column=0, sticky="e", pady=8, padx=8)
        ttk.Entry(box, textvariable=self.customer_name, width=40,
                  font=FONT).grid(row=1, column=1, pady=8)
        ttk.Label(box, text="เบอร์โทร").grid(row=2, column=0, sticky="e", pady=8, padx=8)
        ttk.Entry(box, textvariable=self.customer_phone, width=40,
                  font=FONT).grid(row=2, column=1, pady=8)
        ttk.Label(box, text="จำนวนวัน").grid(row=3, column=0, sticky="e", pady=8, padx=8)
        ttk.Spinbox(box, from_=1, to=30, textvariable=self.customer_days,
                    width=8, font=FONT).grid(row=3, column=1, sticky="w", pady=8)
        ttk.Label(box, textvariable=self.customer_estimate, font=FONT_BOLD,
                  bootstyle="warning").grid(row=4, column=0, columnspan=2, pady=(12, 4))
        ttk.Button(box, text="ยืนยันการเช่า", bootstyle="success", width=24,
                   command=self.on_customer_rent).grid(
                       row=5, column=0, columnspan=2, pady=(10, 0))

    def build_customer_rentals_tab(self):
        tab = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(tab, text="  การเช่าของฉัน  ")
        controls = ttk.Frame(tab)
        controls.pack(fill=X, pady=(0, 10))
        ttk.Label(controls, text="เบอร์โทร").pack(side=LEFT, padx=(0, 8))
        ttk.Entry(controls, textvariable=self.customer_lookup_phone,
                  width=20, font=FONT).pack(side=LEFT)
        ttk.Button(controls, text="ค้นหา", bootstyle="primary-outline",
                   command=self.refresh_all).pack(side=LEFT, padx=8)
        ttk.Button(controls, text="แจ้งขอคืนเครื่อง", bootstyle="success",
                   command=self.on_customer_return).pack(side=RIGHT)
        self.customer_rentals_tree = make_tree(tab, [
            ("rental_id", "รหัสเช่า", 80), ("console_name", "เครื่อง", 180),
            ("rent_date", "วันที่เช่า", 120), ("due_date", "กำหนดคืน", 120),
            ("return_date", "วันที่คืน", 120), ("total_price", "ราคารวม (บาท)", 140),
            ("return_status", "สถานะ", 150)])

    def update_customer_estimate(self, *_):
        console_id = self.customer_console_map.get(self.customer_console.get())
        rate = self.rate_map.get(console_id)
        try:
            days = int(self.customer_days.get())
        except ValueError:
            days = None
        if rate is None or days is None:
            self.customer_estimate.set("ราคาโดยประมาณ: -")
        else:
            self.customer_estimate.set(f"ราคาโดยประมาณ: {rate * days:,.0f} บาท")

    def on_customer_rent(self):
        console_id = self.customer_console_map.get(self.customer_console.get())
        if console_id is None:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกเครื่อง")
            return
        phone = self.customer_phone.get().strip()
        ok, message = logic.add_rental(
            console_id, self.customer_name.get().strip(), phone, self.customer_days.get())
        if ok:
            messagebox.showinfo("สำเร็จ", message)
            self.customer_lookup_phone.set(phone)
            self.customer_name.set("")
            self.customer_phone.set("")
            self.customer_days.set("1")
            self.customer_console.set("")
            self.notebook.select(2)
            self.refresh_all()
        else:
            messagebox.showerror("ไม่สำเร็จ", message)

    def refresh_customer_rentals(self):
        phone = self.customer_lookup_phone.get().strip()
        if not phone:
            self.customer_rentals_tree.delete(*self.customer_rentals_tree.get_children())
            return
        rentals = [dict(rental, return_status=rental_status(rental))
               for rental in logic.get_rentals_by_phone(phone)]
        fill_tree(self.customer_rentals_tree, rentals,
                  ["rental_id", "console_name", "rent_date", "due_date",
               "return_date", "total_price", "return_status"],
                  tag_fn=lambda rental: "bad" if rental.get("return_date") is None
                  and rental["due_date"] < date.today().isoformat() else "")

    def on_customer_return(self):
        selected = self.customer_rentals_tree.selection()
        if not selected:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกรายการที่ต้องการคืน")
            return
        if not messagebox.askyesno(
                "แจ้งขอคืน", "ส่งคำขอคืนรายการนี้ใช่ไหม? กรุณานำเครื่องให้พนักงานตรวจรับ"):
            return
        ok, message = logic.request_my_return(
            int(selected[0]), self.customer_lookup_phone.get().strip())
        if ok:
            messagebox.showinfo("ส่งคำขอแล้ว", message)
            self.refresh_all()
        else:
            messagebox.showerror("ไม่สำเร็จ", message)

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
                            "phone", "rent_date", "due_date", "return_status"]
        self.return_tree = make_tree(tab, [
            ("rental_id", "รหัสเช่า", 80), ("console_name", "เครื่อง", 180),
            ("customer_name", "ลูกค้า", 170), ("phone", "เบอร์โทร", 130),
            ("rent_date", "วันที่เช่า", 120), ("due_date", "กำหนดคืน", 120),
            ("return_status", "สถานะ", 150)])
        ttk.Label(tab, text="ตรวจรับเครื่องก่อนกดยืนยันคืน | แถวสีแดง = เกินกำหนด",
                  bootstyle="danger").pack(pady=(8, 0))
        ttk.Button(tab, text="ยืนยันรับคืนเครื่อง", bootstyle="success",
                   command=self.on_return).pack(pady=(8, 0))

    def on_return(self):
        selected = self.return_tree.selection()
        if not selected:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกรายการที่ต้องการคืน")
            return
        if not messagebox.askyesno(
            "ยืนยันรับคืน", "ตรวจรับเครื่องจริงแล้ว และต้องการปิดรายการเช่านี้ใช่ไหม"):
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
        try:
            if self.mode == "customer":
                self.refresh_customer_data()
            elif self.mode == "staff":
                self.refresh_staff_data()
            self.database_error_shown = False
        except Exception:
            if not self.database_error_shown:
                messagebox.showerror(
                    "ฐานข้อมูลไม่พร้อมใช้งาน",
                    "เชื่อมต่อฐานข้อมูลไม่ได้ กรุณาตรวจสอบว่า PostgreSQL เปิดอยู่ "
                    "และตั้งค่า db_config.py ถูกต้อง")
                self.database_error_shown = True

    def refresh_customer_data(self):
        available = logic.get_available_consoles()
        self.customer_console_map = {
            f"{c['console_id']} - {c['name']} ({c['daily_rate']:.0f} บาท/วัน)": c["console_id"]
            for c in available}
        self.rate_map = {c["console_id"]: c["daily_rate"] for c in available}
        self.customer_rent_combo["values"] = list(self.customer_console_map.keys())
        if self.customer_console.get() not in self.customer_console_map:
            self.customer_console.set("")
        fill_tree(self.customer_available_tree, available,
                  ["console_id", "name", "platform", "daily_rate"])
        self.refresh_customer_rentals()
        self.update_customer_estimate()

    def refresh_staff_data(self):
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
        active = [dict(r, return_status=rental_status(r)) for r in rentals
              if r.get("return_date") is None]
        fill_tree(self.return_tree, active, self.active_keys,
              tag_fn=lambda r: "bad" if r["due_date"] < today else
              "ok" if r.get("return_requested_at") is not None else
              "warn" if r["due_date"] == today else "")
        fill_tree(self.history_tree, rentals, self.history_keys)

        self.update_estimate()


if __name__ == "__main__":
    App().mainloop()
