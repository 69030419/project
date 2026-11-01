"""Flet desktop UI for the game rental application."""
import os
from datetime import date

import flet as ft

import logic

PLATFORMS = ["PS5", "PS4", "Xbox Series X", "Xbox One", "Nintendo Switch", "Steam Deck"]

BG = "#111916"
SURFACE = "#19231f"
SURFACE_ALT = "#202c27"
INK = "#edf5f0"
MUTED = "#9aaea4"
BRAND = "#1c5949"
ACCENT = "#e28b68"
LINE = "#2d3d35"
GOOD = "#6bd4a8"
WARN = "#f2bd67"
BAD = "#f07878"

FONT = "Segoe UI"


def display_value(value):
    if value is None or value == "":
        return "-"
    if isinstance(value, float):
        return f"{value:,.0f}"
    return str(value)


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


class RentalApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.view_index = 0
        self.selected_rental_id = None
        self.rentals = []
        self.consoles = []
        self.available_consoles = []
        self.rate_by_id = {}
        self.console_by_id = {}
        self.theme_mode = ft.ThemeMode.DARK

        page.title = "ร้านเช่าเครื่องเกม"
        page.theme = ft.Theme(color_scheme_seed=BRAND, font_family=FONT)
        page.dark_theme = ft.Theme(color_scheme_seed=BRAND, font_family=FONT)
        page.theme_mode = self.theme_mode
        page.bgcolor = BG
        page.padding = 0
        page.spacing = 0
        self.load_window_icon()
        self.open_staff_pin_dialog()

    def load_window_icon(self):
        icon_png = os.path.abspath("icon.png")
        icon_ico = os.path.abspath("icon.ico")

        if not os.path.exists(icon_ico) and os.path.exists(icon_png):
            try:
                from PIL import Image
                Image.open(icon_png).save(icon_ico)
            except Exception:
                pass

        if os.path.exists(icon_ico):
            self.page.window.icon = icon_ico
        elif os.path.exists(icon_png):
            self.page.window.icon = icon_png
        else:
            self.page.window.icon = None

        try:
            self.page.update()
        except Exception:
            pass

    def render(self):
        self.page.clean()
        self.page.add(self.header())
        destinations = self.destinations()
        self.rail = ft.NavigationRail(
            selected_index=self.view_index,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=92,
            bgcolor=SURFACE,
            indicator_color=BRAND,
            destinations=destinations,
            on_change=self.on_navigation_change,
        )
        self.body = ft.Container(expand=True, padding=28, bgcolor=BG)
        self.page.add(
            ft.Row(
                [self.rail, ft.VerticalDivider(width=1, color=LINE), self.body],
                expand=True,
                spacing=0,
                vertical_alignment=ft.CrossAxisAlignment.STRETCH,
            )
        )
        self.render_view()

    def header(self):
        actions = [
            ft.Text("โหมดพนักงาน", color=INK),
            ft.IconButton(
                icon=ft.Icons.LIGHT_MODE if self.theme_mode == ft.ThemeMode.DARK else ft.Icons.DARK_MODE,
                tooltip="สลับธีม",
                icon_color=INK,
                on_click=self.toggle_theme,
            ),
        ]
        return ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text("GAME RENTAL DESK", size=11, weight=ft.FontWeight.BOLD,
                                    color="#b7d8ca"),
                            ft.Text("ร้านเช่าเครื่องเกม", size=23, weight=ft.FontWeight.BOLD,
                                    color=INK),
                        ],
                        spacing=2,
                    ),
                    ft.Row(actions, spacing=4),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=BRAND,
            padding=ft.Padding(left=26, top=14, right=18, bottom=14),
        )

    def destinations(self):
        items = [
            (ft.Icons.INVENTORY_2, "รายการเครื่อง"),
            (ft.Icons.ADD_SHOPPING_CART, "เช่าเครื่อง"),
            (ft.Icons.ASSIGNMENT_RETURN, "คืนเครื่อง"),
            (ft.Icons.HISTORY, "ประวัติ"),
            (ft.Icons.ADD, "เพิ่มเครื่อง"),
            (ft.Icons.EXTENSION, "อุปกรณ์เสริม"),
            (ft.Icons.BUILD, "ซ่อมบำรุง"),
        ]
        return [ft.NavigationRailDestination(icon=icon, label=label) for icon, label in items]

    def on_navigation_change(self, event):
        self.view_index = event.control.selected_index
        self.selected_rental_id = None
        self.render_view()

    def render_view(self):
        try:
            self.body.content = self.build_view()
            self.page.update()
        except Exception as error:
            self.body.content = self.error_view(
                "โหลดข้อมูลไม่สำเร็จ",
                "ตรวจสอบ PostgreSQL และการตั้งค่า db_config.py แล้วลองรีเฟรชอีกครั้ง.",
            )
            self.page.update()
            print(f"UI data refresh failed: {error}")

    def build_view(self):
        return [self.staff_consoles_view, self.staff_rent_view, self.staff_returns_view,
            self.staff_history_view, self.staff_add_console_view,
            self.staff_accessories_view, self.staff_maintenance_view][self.view_index]()

    def page_heading(self, title, subtitle, refresh=True):
        controls = [
            ft.Column(
                [
                    ft.Text(title, size=27, weight=ft.FontWeight.BOLD, color=INK),
                    ft.Text(subtitle, size=14, color=MUTED),
                ],
                spacing=4,
                expand=True,
            )
        ]
        if refresh:
            controls.append(
                ft.IconButton(
                    ft.Icons.REFRESH,
                    tooltip="รีเฟรช",
                    icon_color=INK,
                    on_click=self.render_view,
                )
            )
        return ft.Row(controls, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    def section(self, content, padding=22):
        return ft.Container(
            content=content,
            padding=padding,
            bgcolor=SURFACE,
            border=ft.Border.all(1, LINE),
            border_radius=16,
        )

    def empty_state(self, message):
        return self.section(
            ft.Column(
                [
                    ft.Icon(ft.Icons.INBOX, size=34, color=MUTED),
                    ft.Text(message, color=MUTED, size=14),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
            padding=36,
        )

    def console_table(self, consoles, include_status=False):
        labels = ["รหัส", "ชื่อเครื่อง", "แพลตฟอร์ม", "ราคา/วัน"]
        if include_status:
            labels.append("สถานะ")
        columns = [ft.DataColumn(ft.Text(label, color=MUTED, weight=ft.FontWeight.BOLD))
                   for label in labels]
        rows = []
        for console in consoles:
            values = [console["console_id"], console["name"], console["platform"],
                      f"{console['daily_rate']:,.0f} บาท"]
            if include_status:
                status_labels = {
                    "available": "ว่าง",
                    "rented": "ถูกเช่า",
                    "maintenance": "กำลังซ่อม",
                }
                values.append(status_labels.get(console["status"], console["status"]))
            rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text(str(value), color=INK))
                                          for value in values]))
        return self.data_table(columns, rows)

    def data_table(self, columns, rows):
        return ft.Row(
            [
                ft.DataTable(
                    columns=columns,
                    rows=rows,
                    show_checkbox_column=False,
                    border=ft.Border.all(1, LINE),
                    border_radius=12,
                    heading_row_color=SURFACE_ALT,
                    heading_row_height=48,
                    data_row_min_height=52,
                    data_text_style=ft.TextStyle(color=INK, size=13),
                    divider_thickness=0.6,
                    column_spacing=24,
                )
            ],
            scroll=ft.ScrollMode.AUTO,
        )

    def staff_consoles_view(self):
        self.consoles = logic.get_all_consoles()
        available_count = sum(console["status"] == "available" for console in self.consoles)
        rented_count = sum(console["status"] == "rented" for console in self.consoles)
        maintenance_count = sum(
            console["status"] == "maintenance" for console in self.consoles)
        summary = ft.Row(
            [
                self.metric_card("เครื่องทั้งหมด", str(len(self.consoles)), ft.Icons.INVENTORY_2, ACCENT),
                self.metric_card("ว่าง", str(available_count), ft.Icons.CHECK_CIRCLE, GOOD),
                self.metric_card("ถูกเช่า", str(rented_count), ft.Icons.SCHEDULE, WARN),
                self.metric_card("กำลังซ่อม", str(maintenance_count), ft.Icons.BUILD, BAD),
            ],
            spacing=14,
        )
        content = [
            self.page_heading("รายการเครื่อง", "ภาพรวมสถานะเครื่องทั้งหมด"),
            summary,
        ]
        if self.consoles:
            content.append(self.section(self.console_table(self.consoles, include_status=True)))
        else:
            content.append(self.empty_state("ยังไม่มีเครื่องในระบบ"))
        return ft.Column(content, spacing=18, scroll=ft.ScrollMode.AUTO, expand=True)

    def metric_card(self, label, value, icon, color):
        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        content=ft.Icon(icon, color=color, size=22),
                        width=42,
                        height=42,
                        alignment=ft.Alignment.CENTER,
                        bgcolor=SURFACE_ALT,
                        border_radius=12,
                    ),
                    ft.Column(
                        [ft.Text(label, size=12, color=MUTED),
                         ft.Text(value, size=22, weight=ft.FontWeight.BOLD, color=INK)],
                        spacing=2,
                    ),
                ],
                spacing=12,
            ),
            padding=18,
            bgcolor=SURFACE,
            border=ft.Border.all(1, LINE),
            border_radius=14,
            expand=True,
        )

    def staff_rent_view(self):
        return self.rent_form()

    def rent_form(self):
        self.available_consoles = logic.get_available_consoles()
        self.available_accessories = [
            item for item in logic.get_all_accessories()
            if item["active"] and item["quantity_available"] > 0
        ]
        self.accessory_by_id = {
            item["accessory_id"]: item for item in self.available_accessories
        }
        self.rent_accessory_fields = []
        self.console_by_id = {console["console_id"]: console
                              for console in self.available_consoles}
        options = [
            ft.DropdownOption(
                key=str(console["console_id"]),
                text=f"{console['name']} · {console['platform']} · {console['daily_rate']:,.0f} บาท/วัน",
            )
            for console in self.available_consoles
        ]
        self.staff_console_field = ft.Dropdown(
            label="เลือกเครื่อง",
            options=options,
            enable_search=True,
            on_select=self.update_rent_estimate,
            width=520,
        )
        self.staff_name_field = ft.TextField(label="ชื่อลูกค้า", width=520)
        self.staff_phone_field = ft.TextField(label="เบอร์โทร 10 หลัก", width=520,
                                              keyboard_type=ft.KeyboardType.PHONE)
        self.staff_days_field = ft.TextField(label="จำนวนวัน", value="1", width=180,
                                             keyboard_type=ft.KeyboardType.NUMBER,
                                             on_change=self.update_rent_estimate)
        self.staff_estimate = ft.Text("ราคาโดยประมาณ: -", size=17,
                                      weight=ft.FontWeight.BOLD, color=WARN)

        accessory_rows = []
        for accessory in self.available_accessories:
            selected = ft.Checkbox(
                label=(f"{accessory['name']} ({accessory['platform']}) · "
                       f"{accessory['daily_rate']:,.0f} บาท/วัน "
                       f"(เหลือ {accessory['quantity_available']})"),
                on_change=self.update_rent_estimate,
            )
            quantity = ft.TextField(
                value="1",
                width=90,
                label="จำนวน",
                keyboard_type=ft.KeyboardType.NUMBER,
                on_change=self.update_rent_estimate,
            )
            accessory_row = ft.Row(
                [selected, quantity],
                spacing=12,
                visible=not accessory["platform"],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
            self.rent_accessory_fields.append((
                accessory["accessory_id"], selected, quantity,
                accessory["platform"], accessory_row))
            accessory_rows.append(accessory_row)

        if not options:
            return ft.Column(
                [self.page_heading("เช่าเครื่อง", "ทำรายการเช่าให้ลูกค้า"),
                 self.empty_state("ไม่มีเครื่องว่างให้เช่าในขณะนี้")],
                spacing=20,
                expand=True,
            )

        console_field = self.staff_console_field
        name_field = self.staff_name_field
        phone_field = self.staff_phone_field
        days_field = self.staff_days_field
        estimate = self.staff_estimate
        return ft.Column(
            [
                self.page_heading("เช่าเครื่อง", "กรอกข้อมูลลูกค้าและเลือกระยะเวลาเช่า", refresh=False),
                self.section(
                    ft.Column(
                        [
                            console_field,
                            name_field,
                            phone_field,
                            ft.Row([days_field, estimate], spacing=24,
                                   vertical_alignment=ft.CrossAxisAlignment.CENTER),
                            self.section(
                                ft.Column(
                                    [ft.Text("อุปกรณ์เสริม (ไม่บังคับ)", weight=ft.FontWeight.BOLD),
                                     ft.Text("เลือกเครื่องก่อนเพื่อแสดงอุปกรณ์ที่ใช้ร่วมกันได้",
                                             color=MUTED),
                                     *(accessory_rows or [ft.Text("ไม่มีอุปกรณ์เสริมพร้อมให้เช่า",
                                                                   color=MUTED)])],
                                    spacing=8,
                                ),
                                padding=18,
                            ),
                            ft.FilledButton(
                                "ยืนยันการเช่า",
                                icon=ft.Icons.CHECK,
                                on_click=self.submit_rental,
                            ),
                        ],
                        spacing=18,
                        width=600,
                    ),
                    padding=28,
                ),
            ],
            spacing=20,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def update_rent_estimate(self):
        console_field = self.staff_console_field
        days_field = self.staff_days_field
        estimate = self.staff_estimate
        try:
            console_id = int(console_field.value)
            days = int(days_field.value)
            console = self.console_by_id[console_id]
            rate = console["daily_rate"]
        except (TypeError, ValueError, KeyError):
            estimate.value = "ราคาโดยประมาณ: -"
            for _, selected, _, platform, accessory_row in self.rent_accessory_fields:
                accessory_row.visible = not platform
                if platform:
                    selected.value = False
        else:
            accessory_total = 0
            try:
                for accessory_id, selected, quantity, platform, accessory_row in self.rent_accessory_fields:
                    accessory_row.visible = (
                        not platform or platform == console["platform"])
                    # ยกเลิกอุปกรณ์ที่ซ่อนอยู่เมื่อเปลี่ยนไปเลือกเครื่องคนละแพลตฟอร์ม
                    if not accessory_row.visible:
                        selected.value = False
                    if selected.value:
                        accessory_total += (
                            self.accessory_by_id[accessory_id]["daily_rate"]
                            * int(quantity.value) * days
                        )
            except (TypeError, ValueError):
                estimate.value = "ตรวจสอบจำนวนอุปกรณ์เสริม"
            else:
                estimate.value = f"ราคาโดยประมาณ: {rate * days + accessory_total:,.0f} บาท"
        if self.page is not None:
            self.page.update()

    def submit_rental(self):
        console_field = self.staff_console_field
        name_field = self.staff_name_field
        phone_field = self.staff_phone_field
        days_field = self.staff_days_field
        try:
            console_id = int(console_field.value)
        except (TypeError, ValueError):
            self.show_message("กรุณาเลือกเครื่องก่อน", error=True)
            return
        accessories = [
            {"accessory_id": accessory_id, "quantity": quantity.value}
            for accessory_id, selected, quantity, _, _ in self.rent_accessory_fields
            if selected.value
        ]
        ok, message = logic.add_rental(
            console_id,
            name_field.value.strip(),
            phone_field.value.strip(),
            days_field.value.strip(),
            accessories=accessories,
        )
        if not ok:
            self.show_message(message, error=True)
            return
        self.show_message(message)
        self.view_index = 0
        self.render()

    def staff_returns_view(self):
        self.rentals = logic.get_all_rentals()
        active = [rental for rental in self.rentals if rental.get("return_date") is None]
        content = [
            self.page_heading("ตรวจรับคืนเครื่อง", "ตรวจเครื่องจริงก่อนกดยืนยันและปล่อยเครื่องว่าง"),
        ]
        if active:
            rows = []
            # ซิงก์ checkbox ทุกแถว เพราะยืนยันคืนได้ครั้งละหนึ่งรายการ
            self.staff_return_checkboxes = {}
            for rental in active:
                color = BAD if rental["due_date"] < date.today().isoformat() else (
                    GOOD if rental.get("return_requested_at") is not None else INK
                )
                rental_id = rental["rental_id"]
                selection = ft.Checkbox(
                    value=self.selected_rental_id == rental_id,
                    on_change=lambda event, selected_id=rental_id:
                        self.select_staff_rental(event, selected_id),
                )
                self.staff_return_checkboxes[rental_id] = selection
                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(selection),
                            ft.DataCell(ft.Text(str(rental["rental_id"]), color=color)),
                            ft.DataCell(ft.Text(rental["console_name"], color=color)),
                            ft.DataCell(ft.Text(rental.get("accessory_summary") or "-", color=color)),
                            ft.DataCell(ft.Text(rental["customer_name"], color=color)),
                            ft.DataCell(ft.Text(rental["phone"], color=color)),
                            ft.DataCell(ft.Text(rental["due_date"], color=color)),
                            ft.DataCell(ft.Text(rental_status(rental), color=color)),
                        ],
                    )
                )
            content.append(
                self.section(
                    ft.Column(
                        [
                            self.data_table(
                                [ft.DataColumn(ft.Text(label)) for label in
                                                                 ("เลือก", "รหัสเช่า", "เครื่อง", "อุปกรณ์เสริม", "ลูกค้า",
                                                                    "เบอร์โทร", "กำหนดคืน", "สถานะ")],
                                rows,
                            ),
                            ft.FilledButton(
                                "ยืนยันรับคืนเครื่อง",
                                icon=ft.Icons.CHECK,
                                on_click=self.confirm_staff_return,
                            ),
                        ],
                        spacing=16,
                    )
                )
            )
        else:
            content.append(self.empty_state("ไม่มีรายการที่รอคืน"))
        return ft.Column(content, spacing=18, scroll=ft.ScrollMode.AUTO, expand=True)

    def select_staff_rental(self, event, rental_id):
        self.selected_rental_id = rental_id if event.control.value else None
        for checkbox_id, checkbox in self.staff_return_checkboxes.items():
            checkbox.value = checkbox_id == self.selected_rental_id
        self.page.update()

    def confirm_staff_return(self):
        rental_id = self.selected_rental_id
        if rental_id is None:
            self.show_message("กรุณาเลือกรายการคืนเครื่องก่อน", error=True)
            return
        self.confirm(
            "ยืนยันรับคืน",
            "ตรวจรับเครื่องจริงแล้ว และต้องการปิดรายการเช่านี้ใช่ไหม",
            lambda: self.finish_staff_return(rental_id),
        )

    def finish_staff_return(self, rental_id):
        ok, message = logic.return_console(rental_id)
        self.show_message(message, error=not ok)
        self.selected_rental_id = None
        self.render_view()

    def staff_history_view(self):
        rentals = logic.get_all_rentals()
        if not rentals:
            return ft.Column(
                [self.page_heading("ประวัติการเช่า", "รายการเช่าและคืนทั้งหมด"),
                 self.empty_state("ยังไม่มีประวัติการเช่า")],
                spacing=20,
                expand=True,
            )
        table = self.data_table(
            [ft.DataColumn(ft.Text(label)) for label in
                 ("รหัส", "เครื่อง", "อุปกรณ์เสริม", "ลูกค้า", "เบอร์โทร", "เช่า",
                  "กำหนดคืน", "คืนจริง", "ยอดรวม")],
            [
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(rental["rental_id"]))),
                        ft.DataCell(ft.Text(rental["console_name"])),
                        ft.DataCell(ft.Text(rental.get("accessory_summary") or "-")),
                        ft.DataCell(ft.Text(rental["customer_name"])),
                        ft.DataCell(ft.Text(rental["phone"])),
                        ft.DataCell(ft.Text(rental["rent_date"])),
                        ft.DataCell(ft.Text(rental["due_date"])),
                        ft.DataCell(ft.Text(display_value(rental.get("return_date")))),
                        ft.DataCell(ft.Text(f"{rental['total_price']:,.0f} บาท")),
                    ]
                )
                for rental in rentals
            ],
        )
        return ft.Column(
            [self.page_heading("ประวัติการเช่า", "รายการเช่าและคืนทั้งหมด"),
             self.section(table)],
            spacing=18,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def staff_add_console_view(self):
        self.new_console_name = ft.TextField(label="ชื่อเครื่อง", width=520)
        self.new_console_platform = ft.Dropdown(
            label="แพลตฟอร์ม",
            width=520,
            editable=True,
            options=[ft.DropdownOption(key=platform, text=platform) for platform in PLATFORMS],
        )
        self.new_console_rate = ft.TextField(
            label="ราคาเช่าต่อวัน (บาท)",
            width=240,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        return ft.Column(
            [
                self.page_heading("เพิ่มเครื่อง", "เพิ่มอุปกรณ์ใหม่ในรายการของร้าน", refresh=False),
                self.section(
                    ft.Column(
                        [
                            self.new_console_name,
                            self.new_console_platform,
                            self.new_console_rate,
                            ft.FilledButton("เพิ่มเครื่อง", icon=ft.Icons.ADD,
                                            on_click=self.submit_new_console),
                        ],
                        spacing=18,
                        width=600,
                    ),
                    padding=28,
                ),
            ],
            spacing=20,
            expand=True,
        )

    def submit_new_console(self):
        ok, message = logic.add_console(
            self.new_console_name.value,
            self.new_console_platform.value,
            self.new_console_rate.value,
        )
        self.show_message(message, error=not ok)
        if ok:
            self.view_index = 0
            self.render()

    def staff_accessories_view(self):
        accessories = logic.get_all_accessories()
        self.new_accessory_name = ft.TextField(label="ชื่ออุปกรณ์", width=520)
        self.new_accessory_platform = ft.Dropdown(
            label="แพลตฟอร์ม",
            width=240,
            options=[ft.DropdownOption(key=platform, text=platform)
                     for platform in PLATFORMS],
        )
        self.new_accessory_rate = ft.TextField(
            label="ราคาเช่าต่อวัน (บาท, ใส่ 0 หากไม่คิดเงิน)",
            value="0",
            width=300,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        self.new_accessory_quantity = ft.TextField(
            label="จำนวนทั้งหมด",
            width=180,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        content = [
            self.page_heading("จัดการอุปกรณ์เสริม", "เพิ่มอุปกรณ์และตรวจสอบจำนวนที่พร้อมให้เช่า"),
        ]
        if accessories:
            rows = [
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(item["accessory_id"]))),
                    ft.DataCell(ft.Text(item["name"])),
                    ft.DataCell(ft.Text(item["platform"] or "ทุกแพลตฟอร์ม")),
                    ft.DataCell(ft.Text(f"{item['daily_rate']:,.0f} บาท")),
                    ft.DataCell(ft.Text(str(item["quantity_total"]))),
                    ft.DataCell(ft.Text(str(item["quantity_available"]))),
                    ft.DataCell(ft.Text("ใช้งาน" if item["active"] else "ปิดใช้งาน")),
                ])
                for item in accessories
            ]
            content.append(self.section(self.data_table(
                [ft.DataColumn(ft.Text(label)) for label in
                 ("รหัส", "อุปกรณ์", "แพลตฟอร์ม", "ราคา/วัน", "ทั้งหมด",
                  "พร้อมให้เช่า", "สถานะ")],
                rows,
            )))
        else:
            content.append(self.empty_state("ยังไม่มีอุปกรณ์เสริมในระบบ"))
        content.append(
            self.section(
                ft.Column(
                    [
                        ft.Text("เพิ่มอุปกรณ์", size=17, weight=ft.FontWeight.BOLD, color=INK),
                        self.new_accessory_name,
                        ft.Row([self.new_accessory_platform, self.new_accessory_rate], spacing=14),
                        self.new_accessory_quantity,
                        ft.FilledButton("เพิ่มอุปกรณ์", icon=ft.Icons.ADD,
                                        on_click=self.submit_new_accessory),
                    ],
                    spacing=16,
                    width=600,
                ),
                padding=24,
            )
        )
        return ft.Column(content, spacing=18, scroll=ft.ScrollMode.AUTO, expand=True)

    def submit_new_accessory(self):
        ok, message = logic.add_accessory(
            self.new_accessory_name.value,
            self.new_accessory_platform.value,
            self.new_accessory_rate.value,
            self.new_accessory_quantity.value,
        )
        self.show_message(message, error=not ok)
        if ok:
            self.render_view()

    def staff_maintenance_view(self):
        consoles = [console for console in logic.get_all_consoles()
                    if console["status"] == "available"]
        options = [
            ft.DropdownOption(
                key=str(console["console_id"]),
                text=f"{console['name']} · {console['platform']}",
            )
            for console in consoles
        ]
        self.maintenance_console_field = ft.Dropdown(
            label="เลือกเครื่องที่ว่าง",
            options=options,
            enable_search=True,
            width=520,
        )
        self.maintenance_issue_field = ft.TextField(
            label="อาการเสียหรือรายละเอียดที่พบ",
            multiline=True,
            min_lines=2,
            max_lines=4,
            width=520,
        )
        records = logic.get_maintenance_records(open_only=True)
        content = [
            self.page_heading("ซ่อมบำรุงเครื่อง", "เปิดงานซ่อมและบันทึกผลก่อนนำเครื่องกลับมาให้เช่า"),
            self.section(
                ft.Column(
                    [
                        ft.Text("แจ้งซ่อม", size=17, weight=ft.FontWeight.BOLD, color=INK),
                        self.maintenance_console_field,
                        self.maintenance_issue_field,
                        ft.FilledButton("เปิดงานซ่อม", icon=ft.Icons.BUILD,
                                        on_click=self.submit_maintenance_report),
                    ],
                    spacing=16,
                    width=600,
                ),
                padding=24,
            ),
        ]
        if records:
            rows = [
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(record["maintenance_id"]))),
                    ft.DataCell(ft.Text(record["console_name"])),
                    ft.DataCell(ft.Text(record["platform"])),
                    ft.DataCell(ft.Text(record["issue"])),
                    ft.DataCell(ft.Text(record["reported_at"])),
                    ft.DataCell(ft.OutlinedButton(
                        "บันทึกซ่อมเสร็จ",
                        icon=ft.Icons.CHECK,
                        on_click=lambda event, record_id=record["maintenance_id"]:
                            self.open_maintenance_completion_dialog(record_id),
                    )),
                ])
                for record in records
            ]
            content.append(self.section(self.data_table(
                [ft.DataColumn(ft.Text(label)) for label in
                 ("รหัสงาน", "เครื่อง", "แพลตฟอร์ม", "อาการ", "วันที่แจ้ง", "จัดการ")],
                rows,
            )))
        else:
            content.append(self.empty_state("ไม่มีงานซ่อมที่เปิดอยู่"))
        return ft.Column(content, spacing=18, scroll=ft.ScrollMode.AUTO, expand=True)

    def submit_maintenance_report(self):
        try:
            console_id = int(self.maintenance_console_field.value)
        except (TypeError, ValueError):
            self.show_message("กรุณาเลือกเครื่องก่อน", error=True)
            return
        ok, message = logic.report_console_issue(
            console_id, self.maintenance_issue_field.value)
        self.show_message(message, error=not ok)
        if ok:
            self.render_view()

    def open_maintenance_completion_dialog(self, maintenance_id):
        repair_cost = ft.TextField(
            label="ค่าซ่อม (บาท)",
            value="0",
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        notes = ft.TextField(
            label="หมายเหตุ",
            multiline=True,
            min_lines=2,
            max_lines=4,
        )

        def finish_repair():
            ok, message = logic.complete_console_repair(
                maintenance_id, repair_cost.value, notes.value)
            self.page.pop_dialog()
            self.show_message(message, error=not ok)
            if ok:
                self.render_view()

        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("บันทึกผลซ่อม"),
                content=ft.Column([repair_cost, notes], tight=True, spacing=12),
                actions=[
                    ft.TextButton("ยกเลิก", on_click=self.page.pop_dialog),
                    ft.FilledButton("ปิดงานซ่อม", on_click=finish_repair),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )

    def confirm(self, title, message, action):
        def close_dialog():
            self.page.pop_dialog()

        def confirm_action():
            self.page.pop_dialog()
            action()

        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text(title),
                content=ft.Text(message),
                actions=[
                    ft.TextButton("ยกเลิก", on_click=close_dialog),
                    ft.FilledButton("ยืนยัน", on_click=confirm_action),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )

    def open_staff_pin_dialog(self):
        pin_field = ft.TextField(label="PIN พนักงาน", password=True,
                                 can_reveal_password=True, autofocus=True)

        def submit_pin():
            if not logic.check_staff_pin(pin_field.value or ""):
                pin_field.value = ""
                pin_field.error_text = "PIN ไม่ถูกต้อง"
                pin_field.update()
                return
            self.page.pop_dialog()
            self.selected_rental_id = None
            self.view_index = 0
            self.render()

        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("เข้าสู่โหมดพนักงาน"),
                content=pin_field,
                actions=[
                    ft.FilledButton("เข้าสู่ระบบ", on_click=submit_pin),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )

    def toggle_theme(self):
        self.theme_mode = (ft.ThemeMode.LIGHT if self.theme_mode == ft.ThemeMode.DARK
                           else ft.ThemeMode.DARK)
        self.page.theme_mode = self.theme_mode
        self.render()

    def show_message(self, message, error=False):
        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("ไม่สำเร็จ" if error else "เรียบร้อย"),
                content=ft.Text(message),
                actions=[ft.TextButton("ตกลง", on_click=self.page.pop_dialog)],
            )
        )

    def error_view(self, title, message):
        return ft.Column(
            [
                self.page_heading(title, message, refresh=False),
                ft.OutlinedButton("ลองอีกครั้ง", icon=ft.Icons.REFRESH,
                                  on_click=self.render_view),
            ],
            spacing=18,
        )


def main(page: ft.Page):
    RentalApp(page)


if __name__ == "__main__":
    ft.run(main, view=ft.AppView.FLET_APP)
