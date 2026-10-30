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
        self.mode = None
        self.view_index = 0
        self.selected_rental_id = None
        self.customer_lookup_phone = ""
        self.customer_rentals = []
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
        self.render()

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
        if self.mode is None:
            self.page.add(self.mode_picker())
            self.page.update()
            return

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
        mode_text = "เลือกโหมด" if self.mode is None else (
            "โหมดลูกค้า" if self.mode == "customer" else "โหมดพนักงาน"
        )
        actions = [
            ft.TextButton(
                mode_text,
                icon=ft.Icons.SWAP_HORIZ,
                on_click=self.show_mode_picker,
                style=ft.ButtonStyle(color=INK),
            ),
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

    def mode_picker(self):
        customer_card = self.mode_card(
            "สำหรับลูกค้า",
            "เช่าเครื่องเกม",
            "ดูเครื่องที่ว่าง เช่าเครื่อง และติดตามรายการเช่าของคุณ",
            ft.Icons.SPORTS_ESPORTS,
            "เข้าใช้งาน",
            self.enter_customer_mode,
            GOOD,
        )
        staff_card = self.mode_card(
            "สำหรับพนักงาน",
            "จัดการหน้าร้าน",
            "จัดการเครื่อง การเช่า การคืน และประวัติ",
            ft.Icons.STORE,
            "เข้าสู่ระบบพนักงาน",
            self.open_staff_pin_dialog,
            ACCENT,
        )
        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(height=18),
                    ft.Text("ยินดีต้อนรับ", size=32, weight=ft.FontWeight.BOLD, color=INK),
                    ft.Text("เลือกโหมดการใช้งาน", size=15, color=MUTED),
                    ft.Container(height=16),
                    ft.Row([customer_card, staff_card], spacing=18, expand=True),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
                expand=True,
            ),
            padding=ft.Padding(left=32, top=28, right=32, bottom=32),
            expand=True,
            bgcolor=BG,
        )

    def mode_card(self, eyebrow, title, description, icon, button_text, action, accent):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Icon(icon, size=28, color=accent),
                        width=54,
                        height=54,
                        alignment=ft.Alignment.CENTER,
                        bgcolor=SURFACE_ALT,
                        border_radius=16,
                    ),
                    ft.Text(eyebrow.upper(), size=11, weight=ft.FontWeight.BOLD, color=accent),
                    ft.Text(title, size=24, weight=ft.FontWeight.BOLD, color=INK),
                    ft.Text(description, size=14, color=MUTED),
                    ft.Container(expand=True),
                    ft.FilledButton(button_text, icon=ft.Icons.ARROW_FORWARD, on_click=action),
                ],
                spacing=12,
                expand=True,
            ),
            padding=28,
            bgcolor=SURFACE,
            border=ft.Border.all(1, LINE),
            border_radius=18,
            expand=True,
        )

    def destinations(self):
        if self.mode == "customer":
            items = [
                (ft.Icons.VIDEOGAME_ASSET, "เครื่องว่าง"),
                (ft.Icons.ADD_SHOPPING_CART, "เช่าเครื่อง"),
                (ft.Icons.RECEIPT_LONG, "รายการของฉัน"),
            ]
        else:
            items = [
                (ft.Icons.INVENTORY_2, "รายการเครื่อง"),
                (ft.Icons.ADD_SHOPPING_CART, "เช่าเครื่อง"),
                (ft.Icons.ASSIGNMENT_RETURN, "คืนเครื่อง"),
                (ft.Icons.HISTORY, "ประวัติ"),
                (ft.Icons.ADD, "เพิ่มเครื่อง"),
                (ft.Icons.EXTENSION, "อุปกรณ์เสริม"),
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
        if self.mode == "customer":
            return [self.customer_available_view, self.customer_rent_view,
                    self.customer_rentals_view][self.view_index]()
        return [self.staff_consoles_view, self.staff_rent_view, self.staff_returns_view,
            self.staff_history_view, self.staff_add_console_view,
            self.staff_accessories_view][self.view_index]()

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
                values.append("ว่าง" if console["status"] == "available" else "ถูกเช่า")
            rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text(str(value), color=INK))
                                          for value in values]))
        return self.data_table(columns, rows)

    def data_table(self, columns, rows, selectable=False):
        return ft.Row(
            [
                ft.DataTable(
                    columns=columns,
                    rows=rows,
                    show_checkbox_column=selectable,
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

    def customer_available_view(self):
        self.available_consoles = logic.get_available_consoles()
        content = [self.page_heading("เครื่องที่พร้อมให้เช่า", "เลือกเครื่องจากรายการและดูราคาเช่าต่อวัน")]
        if self.available_consoles:
            content.append(self.section(self.console_table(self.available_consoles)))
        else:
            content.append(self.empty_state("ตอนนี้ยังไม่มีเครื่องว่าง"))
        return ft.Column(content, spacing=20, scroll=ft.ScrollMode.AUTO, expand=True)

    def staff_consoles_view(self):
        self.consoles = logic.get_all_consoles()
        available_count = sum(console["status"] == "available" for console in self.consoles)
        rented_count = len(self.consoles) - available_count
        summary = ft.Row(
            [
                self.metric_card("เครื่องทั้งหมด", str(len(self.consoles)), ft.Icons.INVENTORY_2, ACCENT),
                self.metric_card("ว่าง", str(available_count), ft.Icons.CHECK_CIRCLE, GOOD),
                self.metric_card("ถูกเช่า", str(rented_count), ft.Icons.SCHEDULE, WARN),
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

    def customer_rent_view(self):
        return self.rent_form(customer=True)

    def staff_rent_view(self):
        return self.rent_form(customer=False)

    def rent_form(self, customer):
        self.available_consoles = logic.get_available_consoles()
        self.available_accessories = [
            item for item in logic.get_all_accessories()
            if item["active"] and item["quantity_available"] > 0
        ]
        self.accessory_by_id = {
            item["accessory_id"]: item for item in self.available_accessories
        }
        self.rent_accessory_fields = []
        self.rate_by_id = {console["console_id"]: console["daily_rate"]
                           for console in self.available_consoles}
        self.console_by_id = {console["console_id"]: console
                              for console in self.available_consoles}
        options = [
            ft.DropdownOption(
                key=str(console["console_id"]),
                text=f"{console['name']} · {console['platform']} · {console['daily_rate']:,.0f} บาท/วัน",
            )
            for console in self.available_consoles
        ]
        if customer:
            self.customer_console_field = ft.Dropdown(
                label="เลือกเครื่อง",
                options=options,
                enable_search=True,
                on_select=self.update_rent_estimate,
                width=520,
            )
            self.customer_name_field = ft.TextField(label="ชื่อผู้เช่า", width=520)
            self.customer_phone_field = ft.TextField(label="เบอร์โทร 10 หลัก", width=520,
                                                     keyboard_type=ft.KeyboardType.PHONE)
            self.customer_days_field = ft.TextField(label="จำนวนวัน", value="1", width=180,
                                                    keyboard_type=ft.KeyboardType.NUMBER,
                                                    on_change=self.update_rent_estimate)
            self.customer_estimate = ft.Text("ราคาโดยประมาณ: -", size=17,
                                             weight=ft.FontWeight.BOLD, color=WARN)
        else:
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
                label=(f"{accessory['name']} · {accessory['daily_rate']:,.0f} บาท/วัน "
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
            self.rent_accessory_fields.append(
                (accessory["accessory_id"], selected, quantity))
            accessory_rows.append(
                ft.Row([selected, quantity], spacing=12,
                       vertical_alignment=ft.CrossAxisAlignment.CENTER))

        if not options:
            return ft.Column(
                [self.page_heading("เช่าเครื่อง", "ทำรายการเช่าให้ลูกค้า"),
                 self.empty_state("ไม่มีเครื่องว่างให้เช่าในขณะนี้")],
                spacing=20,
                expand=True,
            )

        console_field = self.customer_console_field if customer else self.staff_console_field
        name_field = self.customer_name_field if customer else self.staff_name_field
        phone_field = self.customer_phone_field if customer else self.staff_phone_field
        days_field = self.customer_days_field if customer else self.staff_days_field
        estimate = self.customer_estimate if customer else self.staff_estimate
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
                                     *(accessory_rows or [ft.Text("ไม่มีอุปกรณ์เสริมพร้อมให้เช่า",
                                                                   color=MUTED)])],
                                    spacing=8,
                                ),
                                padding=18,
                            ),
                            ft.FilledButton(
                                "ยืนยันการเช่า",
                                icon=ft.Icons.CHECK,
                                on_click=lambda: self.submit_rental(customer),
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
        customer = self.mode == "customer"
        console_field = getattr(self, "customer_console_field" if customer else "staff_console_field", None)
        days_field = getattr(self, "customer_days_field" if customer else "staff_days_field", None)
        estimate = getattr(self, "customer_estimate" if customer else "staff_estimate", None)
        if console_field is None or days_field is None or estimate is None:
            return
        try:
            console_id = int(console_field.value)
            days = int(days_field.value)
            rate = self.rate_by_id[console_id]
        except (TypeError, ValueError, KeyError):
            estimate.value = "ราคาโดยประมาณ: -"
        else:
            accessory_total = 0
            try:
                for accessory_id, selected, quantity in self.rent_accessory_fields:
                    if selected.value:
                        accessory_total += (
                            self.accessory_by_id[accessory_id]["daily_rate"]
                            * int(quantity.value) * days
                        )
            except (TypeError, ValueError):
                estimate.value = "ตรวจสอบจำนวนอุปกรณ์เสริม"
            else:
                estimate.value = f"ราคาโดยประมาณ: {rate * days + accessory_total:,.0f} บาท"
        if estimate.page is not None:
            estimate.update()

    def submit_rental(self, customer):
        console_field = self.customer_console_field if customer else self.staff_console_field
        name_field = self.customer_name_field if customer else self.staff_name_field
        phone_field = self.customer_phone_field if customer else self.staff_phone_field
        days_field = self.customer_days_field if customer else self.staff_days_field
        try:
            console_id = int(console_field.value)
        except (TypeError, ValueError):
            self.show_message("กรุณาเลือกเครื่องก่อน", error=True)
            return
        accessories = [
            {"accessory_id": accessory_id, "quantity": quantity.value}
            for accessory_id, selected, quantity in self.rent_accessory_fields
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
        if customer:
            self.customer_lookup_phone = phone_field.value.strip()
        self.show_message(message)
        self.view_index = 2 if customer else 0
        self.render()

    def customer_rentals_view(self):
        phone_field = ft.TextField(
            label="เบอร์โทร 10 หลัก",
            value=self.customer_lookup_phone,
            width=280,
            keyboard_type=ft.KeyboardType.PHONE,
            on_submit=self.search_customer_rentals,
        )
        self.customer_phone_search_field = phone_field
        rentals = self.load_customer_rentals(self.customer_lookup_phone)
        content = [
            self.page_heading("รายการเช่าของฉัน", "ค้นหาด้วยเบอร์โทรที่ใช้ตอนเช่า", refresh=False),
            self.section(
                ft.Row(
                    [
                        phone_field,
                        ft.FilledButton("ค้นหา", icon=ft.Icons.SEARCH,
                                        on_click=self.search_customer_rentals),
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=18,
            ),
        ]
        if rentals:
            columns = ["รหัสเช่า", "เครื่อง", "อุปกรณ์เสริม", "วันที่เช่า", "กำหนดคืน", "สถานะ"]
            rows = []
            for rental in rentals:
                rows.append(
                    ft.DataRow(
                        selected=self.selected_rental_id == rental["rental_id"],
                        on_select_change=lambda event, rental_id=rental["rental_id"]:
                            self.select_customer_rental(event, rental_id),
                        cells=[
                            ft.DataCell(ft.Text(str(rental["rental_id"]))),
                            ft.DataCell(ft.Text(rental["console_name"])),
                            ft.DataCell(ft.Text(rental.get("accessory_summary") or "-")),
                            ft.DataCell(ft.Text(rental["rent_date"])),
                            ft.DataCell(ft.Text(rental["due_date"])),
                            ft.DataCell(ft.Text(rental["return_status"])),
                        ],
                    )
                )
            content.append(
                self.section(
                    ft.Column(
                        [
                            ft.Text("เลือกรายการเพื่อส่งคำขอคืน", color=MUTED),
                            self.data_table(
                                [ft.DataColumn(ft.Text(label)) for label in columns],
                                rows,
                                selectable=True,
                            ),
                            ft.FilledButton(
                                "แจ้งขอคืนเครื่อง",
                                icon=ft.Icons.ASSIGNMENT_RETURN,
                                on_click=self.request_customer_return,
                            ),
                        ],
                        spacing=16,
                    )
                )
            )
        else:
            content.append(self.empty_state("ไม่พบรายการเช่าของเบอร์โทรนี้" if self.customer_lookup_phone
                                            else "กรอกเบอร์โทรเพื่อค้นหารายการเช่า"))
        return ft.Column(content, spacing=18, scroll=ft.ScrollMode.AUTO, expand=True)

    def load_customer_rentals(self, phone):
        if not phone:
            return []
        rentals = logic.get_rentals_by_phone(phone)
        return [dict(rental, return_status=rental_status(rental)) for rental in rentals]

    def search_customer_rentals(self):
        field = getattr(self, "customer_phone_search_field", None)
        if field is not None:
            self.customer_lookup_phone = field.value.strip()
        self.selected_rental_id = None
        self.render_view()

    def select_customer_rental(self, event, rental_id):
        self.selected_rental_id = rental_id if event.control.selected else None
        self.render_view()

    def request_customer_return(self):
        rental_id = self.selected_rental_id
        if rental_id is None:
            self.show_message("กรุณาเลือกรายการเช่าก่อน", error=True)
            return
        self.confirm(
            "แจ้งขอคืนเครื่อง",
            "ส่งคำขอคืนรายการนี้ใช่ไหม? กรุณานำเครื่องให้พนักงานตรวจรับ",
            lambda: self.finish_customer_return(rental_id),
        )

    def finish_customer_return(self, rental_id):
        ok, message = logic.request_my_return(rental_id, self.customer_lookup_phone)
        self.show_message(message, error=not ok)
        self.render_view()

    def staff_returns_view(self):
        self.rentals = logic.get_all_rentals()
        active = [rental for rental in self.rentals if rental.get("return_date") is None]
        content = [
            self.page_heading("ตรวจรับคืนเครื่อง", "ตรวจเครื่องจริงก่อนกดยืนยันและปล่อยเครื่องว่าง"),
        ]
        if active:
            rows = []
            for rental in active:
                color = BAD if rental["due_date"] < date.today().isoformat() else (
                    GOOD if rental.get("return_requested_at") is not None else INK
                )
                rows.append(
                    ft.DataRow(
                        selected=self.selected_rental_id == rental["rental_id"],
                        on_select_change=lambda event, rental_id=rental["rental_id"]:
                            self.select_staff_rental(event, rental_id),
                        cells=[
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
                                 ("รหัสเช่า", "เครื่อง", "อุปกรณ์เสริม", "ลูกค้า", "เบอร์โทร",
                                  "กำหนดคืน", "สถานะ")],
                                rows,
                                selectable=True,
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
        self.selected_rental_id = rental_id if event.control.selected else None
        self.render_view()

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
                    ft.DataCell(ft.Text(f"{item['daily_rate']:,.0f} บาท")),
                    ft.DataCell(ft.Text(str(item["quantity_total"]))),
                    ft.DataCell(ft.Text(str(item["quantity_available"]))),
                    ft.DataCell(ft.Text("ใช้งาน" if item["active"] else "ปิดใช้งาน")),
                ])
                for item in accessories
            ]
            content.append(self.section(self.data_table(
                [ft.DataColumn(ft.Text(label)) for label in
                 ("รหัส", "อุปกรณ์", "ราคา/วัน", "ทั้งหมด", "พร้อมให้เช่า", "สถานะ")],
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
                        ft.Row([self.new_accessory_rate, self.new_accessory_quantity], spacing=14),
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
            self.new_accessory_rate.value,
            self.new_accessory_quantity.value,
        )
        self.show_message(message, error=not ok)
        if ok:
            self.render_view()

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

        def close_dialog():
            self.page.pop_dialog()

        def submit_pin():
            self.page.pop_dialog()
            if logic.check_staff_pin(pin_field.value or ""):
                self.selected_rental_id = None
                self.mode = "staff"
                self.view_index = 0
                self.render()
            else:
                self.show_message("PIN ไม่ถูกต้อง", error=True)

        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("เข้าสู่โหมดพนักงาน"),
                content=pin_field,
                actions=[
                    ft.TextButton("ยกเลิก", on_click=close_dialog),
                    ft.FilledButton("เข้าสู่ระบบ", on_click=submit_pin),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )

    def enter_customer_mode(self):
        self.mode = "customer"
        self.view_index = 0
        self.selected_rental_id = None
        self.render()

    def show_mode_picker(self):
        self.mode = None
        self.view_index = 0
        self.selected_rental_id = None
        self.render()

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
