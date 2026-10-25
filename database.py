"""database.py - ชั้นข้อมูล (PostgreSQL) ของระบบร้านเช่าเครื่องเกม
กฎ: ไฟล์นี้ทำแค่เก็บ/ดึงข้อมูล ไม่มีกฎของร้าน (ตรวจข้อมูล/คิดราคาอยู่ใน logic.py)
logic.py เรียกฟังก์ชันในไฟล์นี้เท่านั้น

ข้อตกลงกับชั้นบน (ดู README):
  - วันที่คืนเป็น string 'YYYY-MM-DD'  (PostgreSQL คืน date จึงต้องแปลงที่นี่)
  - ตัวเลขเงินคืนเป็น float             (PostgreSQL คืน Decimal จึงต้องแปลงที่นี่)
  - ใช้ %s เป็น placeholder เสมอ ห้ามต่อ string เอง (กัน SQL injection)

ตั้งค่าการเชื่อมต่อใน db_config.py (ห้าม commit) ดูตัวอย่างที่ db_config.example.py
"""
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal

import psycopg2
from psycopg2.extras import RealDictCursor

from db_config import DB_CONFIG

# ใส่เครื่องตัวอย่างให้ตอนสร้างตารางครั้งแรก (ตารางว่างเท่านั้น) ปิดได้ด้วยการตั้งเป็น False
SEED_SAMPLE_CONSOLES = True
SAMPLE_CONSOLES = [
    ("PS5 #1", "PS5", 200),
    ("PS5 #2", "PS5", 200),
    ("Switch #1", "Nintendo Switch", 120),
    ("Xbox Series X #1", "Xbox Series X", 180),
]

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS consoles (
    console_id  SERIAL PRIMARY KEY,
    name        VARCHAR(100)  NOT NULL,
    platform    VARCHAR(50)   NOT NULL,
    daily_rate  NUMERIC(10,2) NOT NULL CHECK (daily_rate > 0),
    status      VARCHAR(20)   NOT NULL DEFAULT 'available'
                CHECK (status IN ('available', 'rented'))
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    phone       VARCHAR(10)  NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS rentals (
    rental_id    SERIAL PRIMARY KEY,
    console_id   INTEGER NOT NULL REFERENCES consoles(console_id),
    customer_id  INTEGER NOT NULL REFERENCES customers(customer_id),
    rent_date    DATE NOT NULL,
    due_date     DATE NOT NULL CHECK (due_date >= rent_date),
    return_date  DATE,
    total_price  NUMERIC(10,2) NOT NULL DEFAULT 0
);
"""

# rental ที่ JOIN แล้ว: มี console_id และ daily_rate ด้วย เพราะ logic.return_console ต้องใช้
RENTAL_SELECT = """
SELECT r.rental_id, r.console_id, c.name AS console_name, c.daily_rate,
       cu.name AS customer_name, cu.phone,
       r.rent_date, r.due_date, r.return_date, r.total_price
FROM rentals r
JOIN consoles  c  ON c.console_id  = r.console_id
JOIN customers cu ON cu.customer_id = r.customer_id
"""

_tables_ready = False


# ---------- ตัวช่วยภายในไฟล์ ----------
def _clean(row):
    """แปลง Decimal -> float และ date -> 'YYYY-MM-DD' ให้ตรงกับที่ชั้นบนต้องการ"""
    if row is None:
        return None
    out = {}
    for key, value in row.items():
        if isinstance(value, Decimal):
            value = float(value)
        elif isinstance(value, (date, datetime)):
            value = value.isoformat()[:10]
        out[key] = value
    return out


def _connect():
    """เปิด connection โดยบังคับให้ฝั่งโปรแกรมคุยเป็น UTF-8 เสมอ
    (กันปัญหาภาษาไทยเมื่อฐานข้อมูลถูกสร้างด้วย encoding อื่น เช่น WIN874 บน Windows ไทย)"""
    return psycopg2.connect(**DB_CONFIG, client_encoding="UTF8")


@contextmanager
def _cursor():
    """เปิด connection -> ให้ cursor -> commit ถ้าสำเร็จ / rollback ถ้า error -> ปิดเสมอ"""
    _ensure_tables()
    conn = _connect()
    try:
        with conn:  # สำเร็จ = commit, error = rollback
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                yield cur
    finally:
        conn.close()


def _ensure_tables():
    """สร้างตาราง (ถ้ายังไม่มี) ครั้งเดียวต่อการเปิดโปรแกรม จึงไม่ต้องมีใครเรียก init_db เอง"""
    global _tables_ready
    if _tables_ready:
        return
    conn = _connect()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(SCHEMA_SQL)
                if SEED_SAMPLE_CONSOLES:
                    cur.execute("SELECT COUNT(*) FROM consoles")
                    if cur.fetchone()[0] == 0:
                        cur.executemany(
                            "INSERT INTO consoles (name, platform, daily_rate) "
                            "VALUES (%s, %s, %s)", SAMPLE_CONSOLES)
    finally:
        conn.close()
    _tables_ready = True


# ---------- ฟังก์ชันตามสัญญา README ----------
def init_db():
    """สร้างตารางถ้ายังไม่มี (เรียกเองได้ แต่ไม่จำเป็น เพราะทุกฟังก์ชันเรียกให้อัตโนมัติ)"""
    _ensure_tables()


def insert_console(name, platform, daily_rate):
    with _cursor() as cur:
        cur.execute(
            "INSERT INTO consoles (name, platform, daily_rate) VALUES (%s, %s, %s) "
            "RETURNING console_id", (name, platform, daily_rate))
        return cur.fetchone()["console_id"]


def fetch_all_consoles():
    with _cursor() as cur:
        cur.execute("SELECT console_id, name, platform, daily_rate, status "
                    "FROM consoles ORDER BY console_id")
        return [_clean(row) for row in cur.fetchall()]


def fetch_console(console_id):
    with _cursor() as cur:
        cur.execute("SELECT console_id, name, platform, daily_rate, status "
                    "FROM consoles WHERE console_id = %s", (console_id,))
        return _clean(cur.fetchone())


def set_console_status(console_id, status):
    with _cursor() as cur:
        cur.execute("UPDATE consoles SET status = %s WHERE console_id = %s",
                    (status, console_id))


def find_or_create_customer(name, phone):
    """ลูกค้าระบุด้วยเบอร์โทร (UNIQUE) ถ้ามีแล้วใช้คนเดิม ไม่มีก็สร้างใหม่"""
    with _cursor() as cur:
        cur.execute(
            "INSERT INTO customers (name, phone) VALUES (%s, %s) "
            "ON CONFLICT (phone) DO UPDATE SET name = customers.name "
            "RETURNING customer_id", (name, phone))
        return cur.fetchone()["customer_id"]


def insert_rental(console_id, customer_id, rent_date, due_date):
    with _cursor() as cur:
        cur.execute(
            "INSERT INTO rentals (console_id, customer_id, rent_date, due_date) "
            "VALUES (%s, %s, %s, %s) RETURNING rental_id",
            (console_id, customer_id, rent_date, due_date))
        return cur.fetchone()["rental_id"]


def fetch_all_rentals():
    with _cursor() as cur:
        cur.execute(RENTAL_SELECT + " ORDER BY r.rental_id DESC")
        return [_clean(row) for row in cur.fetchall()]


def fetch_rental(rental_id):
    with _cursor() as cur:
        cur.execute(RENTAL_SELECT + " WHERE r.rental_id = %s", (rental_id,))
        return _clean(cur.fetchone())


def close_rental(rental_id, return_date, total_price):
    with _cursor() as cur:
        cur.execute(
            "UPDATE rentals SET return_date = %s, total_price = %s WHERE rental_id = %s",
            (return_date, total_price, rental_id))