"""logic.py - ชั้นตรรกะของระบบร้านเช่าเครื่องเกม
กฎ: ไฟล์นี้เรียกได้เฉพาะ database.py (ห้าม import tkinter / ui)
ui.py เรียกฟังก์ชันในไฟล์นี้เท่านั้น

ฟังก์ชันที่คืน (ok, message): ok=False แปลว่าไม่สำเร็จ และ message เป็นข้อความไทย
ที่ UI เอาไปแสดงใน messagebox ได้ทันที
"""
import functools
import math
from datetime import date, timedelta

import database

# ---------- ค่าที่ร้านกำหนด (แก้ที่นี่ที่เดียว) ----------
MIN_DAYS = 1
MAX_DAYS = 30
PHONE_LENGTH = 10
LATE_FEE_RATE = 0.5      # ค่าปรับต่อวันที่เกินกำหนด = ราคาต่อวัน x ค่านี้
MIN_CHARGE_DAYS = 1      # คิดเงินขั้นต่ำกี่วัน
STAFF_PIN = "1234"


def _safe(func):
    """กันโปรแกรมล่มเมื่อฐานข้อมูลมีปัญหา: คืน (False, ข้อความ) แทนการ crash"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as error:  # noqa: BLE001
            return False, f"เกิดข้อผิดพลาดกับฐานข้อมูล: {error}"
    return wrapper


# ---------- ดึงข้อมูล (ให้ UI แสดงผล) ----------
def get_all_consoles():
    return database.fetch_all_consoles()


def get_available_consoles():
    return [c for c in database.fetch_all_consoles() if c["status"] == "available"]


def get_all_accessories():
    return database.fetch_all_accessories()


def get_maintenance_records(open_only=False):
    return database.fetch_maintenance_records(open_only=open_only)


def get_all_rentals():
    return database.fetch_all_rentals()


def get_rentals_by_phone(phone):
    phone = (phone or "").strip()
    return [rental for rental in database.fetch_all_rentals()
            if rental["phone"] == phone]


@_safe
def request_my_return(rental_id, phone):
    phone = (phone or "").strip()
    if not (phone.isdigit() and len(phone) == PHONE_LENGTH):
        return False, f"เบอร์โทรต้องเป็นตัวเลข {PHONE_LENGTH} หลัก"
    rental = database.fetch_rental(rental_id)
    if rental is None or rental["phone"] != phone:
        return False, "ไม่พบรายการเช่าของเบอร์โทรนี้"
    if rental["return_date"] is not None:
        return False, "รายการนี้คืนเครื่องไปแล้ว"
    if rental["return_requested_at"] is not None:
        return False, "ส่งคำขอคืนรายการนี้ไปแล้ว กรุณานำเครื่องให้พนักงานตรวจรับ"
    if not database.request_rental_return(rental_id):
        return False, "ไม่สามารถส่งคำขอคืนได้ กรุณารีเฟรชรายการแล้วลองอีกครั้ง"
    return True, "ส่งคำขอคืนแล้ว กรุณานำเครื่องให้พนักงานตรวจรับ"


def check_staff_pin(pin):
    return pin == STAFF_PIN


# ---------- ซ่อมบำรุงเครื่อง ----------
@_safe
def report_console_issue(console_id, issue):
    issue = (issue or "").strip()
    if not issue:
        return False, "กรุณาระบุอาการเสีย"
    if database.create_maintenance_record(console_id, issue) is None:
        return False, "เครื่องนี้ไม่มีอยู่ หรือยังไม่ว่างสำหรับแจ้งซ่อม"
    return True, "บันทึกงานซ่อมแล้ว และนำเครื่องออกจากรายการพร้อมให้เช่า"


@_safe
def complete_console_repair(maintenance_id, repair_cost, notes=""):
    try:
        cost = float(repair_cost)
    except (TypeError, ValueError):
        return False, "ค่าซ่อมต้องเป็นตัวเลข"
    if not math.isfinite(cost) or cost < 0:
        return False, "ค่าซ่อมต้องเป็นตัวเลขตั้งแต่ 0 ขึ้นไป"
    if not database.complete_maintenance_record(
            maintenance_id, cost, (notes or "").strip()):
        return False, "ไม่พบงานซ่อม หรือรายการนี้ปิดงานไปแล้ว"
    return True, "บันทึกซ่อมเสร็จแล้ว เครื่องกลับมาพร้อมให้เช่า"


# ---------- เพิ่มอุปกรณ์เสริม ----------
@_safe
def add_accessory(name, platform, daily_rate, quantity_total):
    name = (name or "").strip()
    platform = (platform or "").strip()
    if not name:
        return False, "กรุณากรอกชื่ออุปกรณ์"
    if not platform:
        return False, "กรุณาเลือกแพลตฟอร์มของอุปกรณ์"
    try:
        rate = float(daily_rate)
    except (TypeError, ValueError):
        return False, "ราคาต่อวันต้องเป็นตัวเลข"
    if not math.isfinite(rate) or rate < 0:
        return False, "ราคาต่อวันต้องเป็นตัวเลขตั้งแต่ 0 ขึ้นไป"
    try:
        quantity = int(quantity_total)
    except (TypeError, ValueError):
        return False, "จำนวนอุปกรณ์ต้องเป็นจำนวนเต็ม"
    if quantity <= 0:
        return False, "จำนวนอุปกรณ์ต้องมากกว่า 0"
    if any(item["name"].lower() == name.lower()
           for item in database.fetch_all_accessories()):
        return False, "มีอุปกรณ์ชื่อนี้อยู่แล้ว"
    database.insert_accessory(name, platform, rate, quantity)
    return True, f"เพิ่มอุปกรณ์ {name} เรียบร้อย"


# ---------- เพิ่มเครื่อง ----------
@_safe
def add_console(name, platform, daily_rate):
    """UI ส่งค่ามาเป็น string ทั้งหมด จึงต้องตรวจและแปลงเอง"""
    name = (name or "").strip()
    platform = (platform or "").strip()
    if not name:
        return False, "กรุณากรอกชื่อเครื่อง"
    if not platform:
        return False, "กรุณากรอกแพลตฟอร์ม"
    try:
        rate = float(daily_rate)
    except (TypeError, ValueError):
        return False, "ราคาต่อวันต้องเป็นตัวเลข"
    if not math.isfinite(rate):
        return False, "ราคาต่อวันต้องเป็นตัวเลขปกติ"
    if rate <= 0:
        return False, "ราคาต่อวันต้องมากกว่า 0"
    if any(c["name"].lower() == name.lower() for c in database.fetch_all_consoles()):
        return False, "มีเครื่องชื่อนี้อยู่แล้ว"
    database.insert_console(name, platform, rate)
    return True, f"เพิ่มเครื่อง {name} เรียบร้อย"


# ---------- เช่าเครื่อง ----------
def _normalize_accessories(accessories):
    """รวมรายการอุปกรณ์ซ้ำให้เหลือหนึ่งรายการต่อชนิด และต้องมีจำนวนมากกว่าศูนย์"""
    quantities = {}
    try:
        for item in accessories or []:
            accessory_id = int(item["accessory_id"])
            quantity = int(item["quantity"])
            if quantity <= 0:
                return None
            quantities[accessory_id] = quantities.get(accessory_id, 0) + quantity
    except (KeyError, TypeError, ValueError):
        return None
    return [{"accessory_id": accessory_id, "quantity": quantity}
            for accessory_id, quantity in sorted(quantities.items())]


@_safe
def validate_rental(console_id, customer_name, phone, days, accessories=None):
    customer_name = (customer_name or "").strip()
    phone = (phone or "").strip()
    if not customer_name:
        return False, "กรุณากรอกชื่อลูกค้า"
    if not (phone.isdigit() and len(phone) == PHONE_LENGTH):
        return False, f"เบอร์โทรต้องเป็นตัวเลข {PHONE_LENGTH} หลัก"
    try:
        days = int(days)
    except (TypeError, ValueError):
        return False, "จำนวนวันต้องเป็นจำนวนเต็ม"
    if not MIN_DAYS <= days <= MAX_DAYS:
        return False, f"จำนวนวันต้องอยู่ระหว่าง {MIN_DAYS}-{MAX_DAYS}"
    console = database.fetch_console(console_id)
    if console is None:
        return False, "ไม่พบเครื่องนี้ในระบบ"
    if console["status"] != "available":
        return False, "เครื่องนี้ถูกเช่าอยู่ ยังไม่ว่าง"
    # ตรวจในชั้น logic ด้วย และตรวจสต็อกซ้ำในฐานข้อมูลก่อนบันทึกรายการจริง
    selected_accessories = _normalize_accessories(accessories)
    if selected_accessories is None:
        return False, "จำนวนอุปกรณ์เสริมไม่ถูกต้อง"
    available_accessories = {
        item["accessory_id"]: item for item in database.fetch_all_accessories()
        if item["active"]
    }
    for item in selected_accessories:
        accessory = available_accessories.get(item["accessory_id"])
        if accessory is None:
            return False, "ไม่พบอุปกรณ์เสริมนี้ในระบบ"
        if accessory["platform"] and accessory["platform"] != console["platform"]:
            return False, f"อุปกรณ์ {accessory['name']} ใช้กับเครื่องนี้ไม่ได้"
        if item["quantity"] > accessory["quantity_available"]:
            return False, f"อุปกรณ์ {accessory['name']} มีไม่พอตามจำนวนที่เลือก"
    return True, ""


@_safe
def add_rental(console_id, customer_name, phone, days, accessories=None):
    selected_accessories = _normalize_accessories(accessories)
    if selected_accessories is None:
        return False, "จำนวนอุปกรณ์เสริมไม่ถูกต้อง"
    ok, message = validate_rental(
        console_id, customer_name, phone, days, selected_accessories)
    if not ok:
        return False, message

    customer_name = customer_name.strip()
    phone = phone.strip()
    days = int(days)
    console = database.fetch_console(console_id)
    accessories_by_id = {
        item["accessory_id"]: item for item in database.fetch_all_accessories()
    }
    # คำนวณราคาโดยประมาณจากค่าเช่าต่อวันปัจจุบันของอุปกรณ์ที่เลือก
    accessory_total = sum(
        accessories_by_id[item["accessory_id"]]["daily_rate"] * item["quantity"] * days
        for item in selected_accessories
    )

    today = date.today()
    due = today + timedelta(days=days)
    rental_id = database.create_rental_transaction(
        console_id, customer_name, phone, today.isoformat(), due.isoformat(),
        accessories=selected_accessories)
    if rental_id is None:
        return False, "เครื่องหรืออุปกรณ์เสริมไม่ว่างแล้ว กรุณารีเฟรชรายการแล้วลองอีกครั้ง"

    estimate = console["daily_rate"] * days + accessory_total
    message = (f"เช่า {console['name']} เป็นเวลา {days} วัน เรียบร้อย\n"
               f"กำหนดคืน {due.isoformat()}  ราคาโดยประมาณ {estimate:,.0f} บาท")
    if selected_accessories:
        message += f"\nรวมค่าอุปกรณ์เสริม {accessory_total:,.0f} บาท"
    return True, message


# ---------- คืนเครื่อง ----------
def calculate_total(daily_rate, rent_date, due_date, return_date):
    """คิดราคาทั้งหมด: ค่าเช่าตามวันที่ใช้จริง (ขั้นต่ำ MIN_CHARGE_DAYS) + ค่าปรับเมื่อเกินกำหนด
    คืนค่า (ราคารวม, วันที่ใช้จริง, วันที่เกินกำหนด) แยกเป็นฟังก์ชันเพื่อทดสอบง่าย"""
    used_days = max(MIN_CHARGE_DAYS, (return_date - rent_date).days)
    late_days = max(0, (return_date - due_date).days)
    total = daily_rate * used_days + daily_rate * LATE_FEE_RATE * late_days
    return total, used_days, late_days


@_safe
def return_console(rental_id):
    rental = database.fetch_rental(rental_id)
    if rental is None:
        return False, "ไม่พบรายการเช่านี้"
    if rental["return_date"] is not None:
        return False, "รายการนี้คืนเครื่องไปแล้ว"

    today = date.today()
    # คิดค่าปรับจากค่าเช่าต่อวันรวมของเครื่องและอุปกรณ์เสริม
    total, used_days, late_days = calculate_total(
        rental["daily_rate"] + rental["accessory_daily_rate"],
        date.fromisoformat(rental["rent_date"]),
        date.fromisoformat(rental["due_date"]),
        today,
    )
    if not database.complete_rental_return(
            rental_id, rental["console_id"], today.isoformat(), total):
        return False, "รายการนี้ถูกคืนไปแล้ว หรือสถานะเครื่องไม่ถูกต้อง"

    message = f"คืน {rental['console_name']} เรียบร้อย\nใช้งาน {used_days} วัน"
    if late_days:
        message += f" (เกินกำหนด {late_days} วัน มีค่าปรับ)"
    message += f"\nราคารวม {total:,.0f} บาท"
    return True, message
