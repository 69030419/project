"""customer_web.py - Customer-facing web page for checking rentals with access code."""
import logging
import os
from datetime import date

import flet as ft

import logic


# Palette - Modern Gaming Emerald Dark Theme
BG = "#0c1310"
SURFACE = "#15201b"
SURFACE_CARD = "#1b2a23"
BORDER = "#253b31"
BORDER_LIGHT = "#334f42"
TEXT_MAIN = "#f1f6f3"
TEXT_MUTED = "#93a89e"
TEXT_FAINT = "#64776e"

BRAND_GREEN = "#10b981"
BRAND_GREEN_LIGHT = "#34d399"
BRAND_GREEN_BG = "#064e3b"

INFO_BLUE = "#38bdf8"
INFO_BLUE_BG = "#0c4a6e"

WARN_AMBER = "#fbbf24"
WARN_AMBER_BG = "#78350f"

DANGER_RED = "#f87171"
DANGER_RED_BG = "#7f1d1d"


class CustomerRentalPage:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "ตรวจสอบรายการเช่า | GAME RENTAL"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = BG
        self.page.padding = 16
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.page.scroll = ft.ScrollMode.AUTO

        self.access_code_field = ft.TextField(
            label="รหัสรายการเช่า 20 ตัว",
            hint_text="เช่น YRZ7CTUKRNXYJ4CW5K6V",
            text_align=ft.TextAlign.CENTER,
            capitalization=ft.TextCapitalization.CHARACTERS,
            max_length=20,
            text_size=15,
            border_color=BORDER,
            focused_border_color=BRAND_GREEN,
            cursor_color=BRAND_GREEN,
            bgcolor=SURFACE_CARD,
            border_radius=12,
            on_submit=lambda _: self.lookup_rental(),
        )
        self.feedback = ft.Text(value="", color=DANGER_RED, size=13, text_align=ft.TextAlign.CENTER)
        self.result_container = ft.Container()
        self.search_section = ft.Container()

        self.init_layout()

        # ตรวจสอบรหัสจาก query parameter เช่น ?code=XXXX
        access_code = self.page.query.get("code")
        if access_code:
            self.access_code_field.value = access_code.strip()
            self.lookup_rental(hide_search_box=True)
        else:
            self.show_search_form()

    def init_layout(self):
        self.page.clean()

        # Header bar
        header = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.SPORTS_ESPORTS, color=BRAND_GREEN, size=28),
                            ft.Text("GAME RENTAL", size=22, weight=ft.FontWeight.BOLD,
                                    color=TEXT_MAIN),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    ft.Text(
                        "ระบบตรวจสอบสถานะและใบเสร็จดิจิทัล",
                        size=13,
                        color=TEXT_MUTED,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
            ),
            padding=ft.Padding.only(top=10, bottom=16),
        )

        # Centered main wrapper (max-width 480px on desktop/tablet)
        self.main_box = ft.Container(
            content=ft.Column(
                [
                    header,
                    self.search_section,
                    self.feedback,
                    self.result_container,
                    self.build_footer(),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=14,
            ),
            width=460,
        )

        self.page.add(self.main_box)

    def show_search_form(self):
        self.search_section.content = ft.Container(
            content=ft.Column(
                [
                    ft.Text("กรอกรหัสส่วนตัวเพื่อตรวจสอบรายการ", size=14, color=TEXT_MUTED,
                            text_align=ft.TextAlign.CENTER),
                    self.access_code_field,
                    ft.FilledButton(
                        "ตรวจสอบรายการ",
                        icon=ft.Icons.SEARCH,
                        style=ft.ButtonStyle(
                            bgcolor={ft.ControlState.DEFAULT: BRAND_GREEN,
                                     ft.ControlState.HOVERED: "#059669"},
                            color=TEXT_MAIN,
                            shape=ft.RoundedRectangleBorder(radius=12),
                            padding=ft.Padding.symmetric(vertical=16, horizontal=24),
                        ),
                        width=400,
                        on_click=lambda _: self.lookup_rental(),
                    ),
                ],
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=SURFACE,
            border=ft.Border.all(1, BORDER),
            border_radius=16,
            padding=20,
        )
        self.search_section.visible = True
        self.page.update()

    def lookup_rental(self, hide_search_box=False):
        raw_code = (self.access_code_field.value or "").strip().upper()
        self.feedback.value = ""
        self.result_container.content = None

        if not raw_code:
            self.feedback.value = "กรุณากรอกรหัสรายการเช่า 20 ตัว"
            self.page.update()
            return

        try:
            rental = logic.get_rental_for_customer_code(raw_code)
        except Exception:
            logging.exception("Customer rental lookup failed")
            self.feedback.value = "ระบบตรวจสอบรายการขัดข้อง กรุณาลองใหม่อีกครั้ง"
            self.page.update()
            return

        if rental is None:
            self.feedback.value = "ไม่พบรายการเช่าจากรหัสนี้ กรุณาตรวจสอบรหัสแล้วลองอีกครั้ง"
            self.show_search_form()
            self.page.update()
            return

        if hide_search_box:
            # ซ่อนฟอร์มค้นหาใหญ่ แล้วแสดงเป็นปุ่มกะทัดรัดด้านล่างแทน
            self.search_section.content = ft.TextButton(
                "ค้นหารหัสอื่น / กรอกรหัสใหม่",
                icon=ft.Icons.SEARCH,
                style=ft.ButtonStyle(color=TEXT_MUTED),
                on_click=lambda _: self.show_search_form(),
            )

        self.result_container.content = self.render_rental_ticket(rental, raw_code)
        self.page.update()

    def render_rental_ticket(self, rental, code):
        today = date.today()
        is_returned = rental.get("return_date") is not None
        is_requesting = rental.get("return_requested_at") is not None

        try:
            due_date_obj = date.fromisoformat(rental["due_date"])
            days_left = (due_date_obj - today).days
        except Exception:
            days_left = 0

        # กำหนดสถานะ ไอคอน สี และข้อความ
        if is_returned:
            status_title = "คืนเครื่องเรียบร้อยแล้ว"
            status_desc = f"บันทึกการส่งคืนเมื่อวันที่ {rental['return_date']}"
            badge_text = "รายการเสร็จสมบูรณ์"
            badge_icon = ft.Icons.CHECK_CIRCLE_ROUNDED
            status_color = BRAND_GREEN_LIGHT
            status_bg = "#064e3b44"
            status_border = BRAND_GREEN
        elif is_requesting:
            status_title = "แจ้งขอคืนแล้ว"
            status_desc = "รอพนักงานตรวจรับเครื่องและอุปกรณ์ที่หน้าร้าน"
            badge_text = "รอการตรวจรับ"
            badge_icon = ft.Icons.PENDING_ACTIONS_ROUNDED
            status_color = WARN_AMBER
            status_bg = "#78350f44"
            status_border = WARN_AMBER
        elif days_left < 0:
            status_title = "เกินกำหนดส่งคืน"
            status_desc = f"เกินกำหนดมาแล้ว {abs(days_left)} วัน กรุณานำส่งคืนหน้าร้านโดยเร็ว"
            badge_text = f"เกินกำหนด {abs(days_left)} วัน"
            badge_icon = ft.Icons.WARNING_ROUNDED
            status_color = DANGER_RED
            status_bg = "#7f1d1d44"
            status_border = DANGER_RED
        elif days_left == 0:
            status_title = "ครบกำหนดคืนวันนี้"
            status_desc = "กรุณานำเครื่องส่งคืนหน้าร้านภายในเวลาทำการวันนี้"
            badge_text = "ครบกำหนดวันนี้"
            badge_icon = ft.Icons.NOTIFICATION_IMPORTANT_ROUNDED
            status_color = WARN_AMBER
            status_bg = "#78350f44"
            status_border = WARN_AMBER
        else:
            status_title = "กำลังเช่าใช้งาน"
            status_desc = f"เหลือเวลาใช้งานอีก {days_left} วัน"
            badge_text = "กำลังเช่า"
            badge_icon = ft.Icons.PLAY_CIRCLE_FILLED_ROUNDED
            status_color = INFO_BLUE
            status_bg = "#0c4a6e44"
            status_border = INFO_BLUE

        # 1. Header Banner สถานะ
        status_banner = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(badge_icon, size=48, color=status_color),
                    ft.Text(status_title, size=20, weight=ft.FontWeight.BOLD,
                            color=TEXT_MAIN, text_align=ft.TextAlign.CENTER),
                    ft.Text(status_desc, size=13, color=TEXT_MUTED,
                            text_align=ft.TextAlign.CENTER),
                    ft.Container(
                        content=ft.Text(badge_text, size=12, weight=ft.FontWeight.BOLD,
                                        color=status_color),
                        bgcolor=status_bg,
                        padding=ft.Padding.symmetric(horizontal=12, vertical=4),
                        border_radius=20,
                        border=ft.Border.all(1, status_border),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            bgcolor=SURFACE_CARD,
            padding=ft.Padding.symmetric(vertical=20, horizontal=16),
            border_radius=16,
            border=ft.Border.all(1, BORDER),
        )

        # 2. ข้อมูลเครื่องเกม & แพลตฟอร์ม
        console_section = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text("เครื่องเกม", size=12, color=TEXT_FAINT),
                            ft.Container(
                                content=ft.Text(rental["platform"], size=11,
                                                color=BRAND_GREEN_LIGHT,
                                                weight=ft.FontWeight.BOLD),
                                bgcolor=BRAND_GREEN_BG,
                                padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                                border_radius=6,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Text(rental["console_name"], size=22, weight=ft.FontWeight.BOLD,
                            color=TEXT_MAIN),
                ],
                spacing=6,
            ),
            bgcolor=SURFACE_CARD,
            padding=16,
            border_radius=14,
            border=ft.Border.all(1, BORDER),
        )

        # 3. ข้อมูลวันที่ (Timeline Card)
        date_rows = [
            self.date_item("วันที่เริ่มเช่า", rental["rent_date"], ft.Icons.CALENDAR_MONTH, TEXT_MUTED),
            self.date_item("กำหนดส่งคืน", rental["due_date"], ft.Icons.EVENT,
                           WARN_AMBER if not is_returned and days_left <= 0 else TEXT_MAIN,
                           bold=True),
        ]
        if is_returned:
            date_rows.append(
                self.date_item("วันที่คืนจริง", rental["return_date"], ft.Icons.TASK_ALT,
                               BRAND_GREEN_LIGHT, bold=True)
            )

        timeline_section = ft.Container(
            content=ft.Column(date_rows, spacing=10),
            bgcolor=SURFACE_CARD,
            padding=16,
            border_radius=14,
            border=ft.Border.all(1, BORDER),
        )

        # 4. อุปกรณ์เสริม (ถ้ามี)
        accessories_card = None
        if rental.get("accessory_summary"):
            accessories_card = ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.EXTENSION_OUTLINED, size=16, color=TEXT_MUTED),
                                ft.Text("อุปกรณ์เสริมที่เช่าพร้อมเครื่อง", size=13,
                                        weight=ft.FontWeight.BOLD, color=TEXT_MAIN),
                            ],
                            spacing=6,
                        ),
                        ft.Text(rental["accessory_summary"], size=14, color=TEXT_MUTED),
                    ],
                    spacing=6,
                ),
                bgcolor=SURFACE_CARD,
                padding=16,
                border_radius=14,
                border=ft.Border.all(1, BORDER),
            )

        # 5. สรุปยอดเงิน (เมื่อคืนเครื่องเรียบร้อยแล้ว - ทำเป็น Digital Receipt)
        payment_section = None
        if is_returned and rental.get("total_price") is not None:
            payment_section = ft.Container(
                content=ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text("ยอดชำระสุทธิ (เสร็จสิ้น)", size=12, color=TEXT_MUTED),
                                ft.Text("ใบเสร็จรับเงินดิจิทัล", size=11, color=TEXT_FAINT),
                            ],
                            spacing=2,
                        ),
                        ft.Text(f"฿{rental['total_price']:,.0f}", size=24,
                                weight=ft.FontWeight.BOLD, color=BRAND_GREEN_LIGHT),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                bgcolor="#064e3b33",
                padding=18,
                border_radius=14,
                border=ft.Border.all(1, BRAND_GREEN),
            )

        # 6. รหัสอ้างอิงท้ายบัตร
        masked_code = f"•••• •••• •••• {code[-4:]}" if len(code) >= 4 else code
        reference_info = ft.Container(
            content=ft.Row(
                [
                    ft.Text("รหัสอ้างอิงรายการ", size=11, color=TEXT_FAINT),
                    ft.Text(masked_code, size=12, color=TEXT_MUTED, font_family="monospace"),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.Padding.symmetric(horizontal=6, vertical=4),
        )

        ticket_items = [
            status_banner,
            console_section,
            timeline_section,
        ]
        if accessories_card:
            ticket_items.append(accessories_card)
        if payment_section:
            ticket_items.append(payment_section)
        ticket_items.append(reference_info)

        return ft.Container(
            content=ft.Column(ticket_items, spacing=12),
            bgcolor=SURFACE,
            padding=16,
            border_radius=20,
            border=ft.Border.all(1, BORDER),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=20,
                color="#00000060",
                offset=ft.Offset(0, 10),
            ),
        )

    @staticmethod
    def date_item(label, val, icon, val_color, bold=False):
        return ft.Row(
            [
                ft.Row(
                    [
                        ft.Icon(icon, size=16, color=TEXT_MUTED),
                        ft.Text(label, size=13, color=TEXT_MUTED),
                    ],
                    spacing=6,
                ),
                ft.Text(val or "-", size=14, weight=ft.FontWeight.BOLD if bold else ft.FontWeight.NORMAL,
                        color=val_color),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

    @staticmethod
    def build_footer():
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("หากมีข้อสงสัยหรือต้องการต่ออายุการเช่า กรุณาติดต่อหน้าร้าน",
                            size=11, color=TEXT_FAINT, text_align=ft.TextAlign.CENTER),
                    ft.Text("Game Rental Desk • Powered by Flet & Python",
                            size=10, color=TEXT_FAINT, text_align=ft.TextAlign.CENTER),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=2,
            ),
            padding=ft.Padding.symmetric(vertical=16),
        )


def main(page: ft.Page):
    CustomerRentalPage(page)


if __name__ == "__main__":
    ft.run(
        main,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8550")),
        view=ft.AppView.WEB_BROWSER,
    )
