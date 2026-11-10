"""Customer-facing web page for checking a rental with its private access code."""
import logging
import os
from datetime import date

import flet as ft

import logic


BG = "#f3f7f4"
SURFACE = "#ffffff"
INK = "#20342c"
MUTED = "#65776e"
BRAND = "#1c5949"
GOOD = "#287a56"
WARN = "#a76216"
BAD = "#b43b3b"


class CustomerRentalPage:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "ตรวจสอบรายการเช่า"
        self.page.theme = ft.Theme(color_scheme_seed=BRAND)
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.bgcolor = BG
        self.page.padding = 0

        self.access_code_field = ft.TextField(
            label="รหัสรายการเช่า",
            hint_text="กรอกรหัส 20 ตัวที่ได้รับจากร้าน",
            max_length=20,
            on_submit=self.lookup_rental,
        )
        self.feedback = ft.Text(color=MUTED)
        self.result = ft.Container()

        self.page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            "ตรวจสอบรายการเช่า",
                            size=28,
                            weight=ft.FontWeight.BOLD,
                            color=INK,
                        ),
                        ft.Text(
                            "กรอกรหัสส่วนตัวที่ได้รับจากร้าน เพื่อดูวันกำหนดคืนและสถานะเครื่อง",
                            color=MUTED,
                        ),
                        self.access_code_field,
                        ft.FilledButton(
                            "ตรวจสอบรายการ",
                            icon=ft.Icons.SEARCH,
                            on_click=self.lookup_rental,
                        ),
                        self.feedback,
                        self.result,
                    ],
                    spacing=16,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                ),
                padding=24,
                expand=True,
            )
        )
        access_code = self.page.query.get("code")
        if access_code:
            self.access_code_field.value = access_code
            self.lookup_rental()

    def lookup_rental(self):
        self.feedback.value = ""
        self.result.content = None
        try:
            rental = logic.get_rental_for_customer_code(
                self.access_code_field.value or "")
        except Exception:
            logging.exception("Customer rental lookup failed")
            self.feedback.value = "ระบบตรวจสอบรายการขัดข้อง กรุณาลองใหม่ภายหลัง"
            self.feedback.color = BAD
            self.page.update()
            return

        if rental is None:
            self.feedback.value = "ไม่พบรายการเช่าจากรหัสนี้ กรุณาตรวจสอบรหัสแล้วลองอีกครั้ง"
            self.feedback.color = BAD
        else:
            self.feedback.color = MUTED
            self.result.content = self.rental_card(rental)
        self.page.update()

    @staticmethod
    def rental_card(rental):
        today = date.today().isoformat()
        if rental["return_date"] is not None:
            status = f"คืนเครื่องแล้ว ({rental['return_date']})"
            status_color = GOOD
        elif rental["return_requested_at"] is not None:
            status = "แจ้งขอคืนแล้ว รอพนักงานตรวจรับ"
            status_color = WARN
        elif rental["due_date"] < today:
            status = "เกินกำหนดคืน"
            status_color = BAD
        elif rental["due_date"] == today:
            status = "ครบกำหนดคืนวันนี้"
            status_color = WARN
        else:
            status = "กำลังเช่า"
            status_color = GOOD

        details = [
            ft.Text(rental["console_name"], size=21, weight=ft.FontWeight.BOLD, color=INK),
            ft.Text(rental["platform"], color=MUTED),
            ft.Row(
                [ft.Text("วันที่เช่า", color=MUTED), ft.Text(rental["rent_date"], color=INK)],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Row(
                [ft.Text("กำหนดคืน", color=MUTED),
                 ft.Text(rental["due_date"], weight=ft.FontWeight.BOLD, color=INK)],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Text(status, color=status_color, weight=ft.FontWeight.BOLD),
        ]
        if rental["accessory_summary"]:
            details.extend([
                ft.Text("อุปกรณ์เสริม", weight=ft.FontWeight.BOLD, color=INK),
                ft.Text(rental["accessory_summary"], color=MUTED),
            ])
        return ft.Container(
            content=ft.Column(details, spacing=12),
            bgcolor=SURFACE,
            padding=20,
            border_radius=12,
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
