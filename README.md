# ระบบร้านเช่าเครื่องเกม (Game Console Rental)

แอปเดสก์ท็อปด้วย Python + Tkinter + PostgreSQL สำหรับร้านให้เช่าเครื่องเกม
(โปรเจกต์วิชาเขียนโปรแกรม + วิชาฐานข้อมูล)

## แบ่งงาน

| ไฟล์ | ผู้รับผิดชอบ | Branch | หน้าที่ |
|------|-------------|--------|---------|
| `ui.py` | Suthinun | `feature/suthinun-ui` | หน้าจอ Tkinter เรียกได้เฉพาะ `logic.py` |
| `logic.py` | Ariyawong | `feature/Ariyawong` | ตรวจสอบข้อมูล คิดราคา/ค่าปรับ เรียกได้เฉพาะ `database.py` |
| `database.py` | Kitthin | `feature/kitthin` | PostgreSQL เก็บ/ดึงข้อมูลอย่างเดียว ไม่มีกฎธุรกิจ |

กฎสำคัญ: **ui → logic → database** (ห้ามข้ามชั้น)

## ติดตั้งและตั้งค่า (ทุกคนทำในเครื่องตัวเอง)

1. ติดตั้ง PostgreSQL และสร้างฐานข้อมูลชื่อ `game_rental`
   ```sql
   CREATE DATABASE game_rental;
   ```
2. ติดตั้งไลบรารี
   ```
   pip install psycopg2-binary ttkbootstrap
   ```
3. สร้างไฟล์ `db_config.py` (คัดลอกจาก `db_config.example.py`) แล้วใส่รหัสผ่านของตัวเอง
   ```python
   DB_CONFIG = {
       "host": "localhost",
       "port": 5432,
       "dbname": "game_rental",
       "user": "postgres",
       "password": "ใส่รหัสผ่านของคุณ",
   }
   ```
4. **ห้าม commit `db_config.py`** เพราะ repo เป็น Public ให้เพิ่มบรรทัดนี้ใน `.gitignore`
   ```
   db_config.py
   ```
   และ commit เฉพาะ `db_config.example.py` (ใส่รหัสผ่านปลอมไว้)

## โครงสร้างฐานข้อมูล

```sql
CREATE TABLE IF NOT EXISTS consoles (
    console_id  SERIAL PRIMARY KEY,
    name        VARCHAR(100)  NOT NULL,                -- เช่น 'PS5 #1'
    platform    VARCHAR(50)   NOT NULL,                -- PS5 / Switch / Xbox ...
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
    return_date  DATE,                                 -- NULL = ยังไม่คืน
    total_price  NUMERIC(10,2) NOT NULL DEFAULT 0
);
```

ความสัมพันธ์: `customers 1 — N rentals N — 1 consoles`

## รูปแบบข้อมูลที่ส่งข้ามไฟล์ (dict)

```python
console = {"console_id": 1, "name": "PS5 #1", "platform": "PS5",
           "daily_rate": 200.0, "status": "available"}

rental = {"rental_id": 1, "console_name": "PS5 #1", "customer_name": "สมชาย",
          "phone": "0812345678", "rent_date": "2026-10-24",
          "due_date": "2026-10-26", "return_date": None, "total_price": 400.0}
```

ข้อตกลงเรื่องชนิดข้อมูล (PostgreSQL คืน `date` และ `Decimal` ซึ่งไม่เหมือนที่ชั้นบนต้องการ):
- `database.py` ต้องแปลงก่อนคืนเสมอ: วันที่เป็น string `YYYY-MM-DD` (`str(value)` หรือ `.isoformat()`) และ `NUMERIC` เป็น `float`
- เวลาส่งค่าเข้า SQL ใช้ placeholder `%s` เสมอ ห้ามต่อ string เอง (กัน SQL injection)

## สัญญาฟังก์ชัน

### `database.py` (Kitthin)
```python
init_db() -> None                                  # สร้างตารางถ้ายังไม่มี
insert_console(name, platform, daily_rate) -> int  # INSERT ... RETURNING console_id
fetch_all_consoles() -> list[dict]                 # คืน console dict
fetch_console(console_id) -> dict | None
set_console_status(console_id, status) -> None     # 'available' | 'rented'
find_or_create_customer(name, phone) -> int        # คืน customer_id
insert_rental(console_id, customer_id, rent_date, due_date) -> int   # RETURNING rental_id
fetch_all_rentals() -> list[dict]                  # คืน rental dict (JOIN แล้ว)
fetch_rental(rental_id) -> dict | None
close_rental(rental_id, return_date, total_price) -> None
```

ทุกฟังก์ชันเปิด connection ผ่าน `psycopg2.connect(**DB_CONFIG)`, `commit()` เมื่อสำเร็จ และปิด connection เสมอ

### `logic.py` (Ariyawong)
```python
validate_rental(console_id, customer_name, phone, days) -> tuple[bool, str]
    # ชื่อไม่ว่าง / เบอร์ 10 หลักตัวเลข / days เป็นจำนวนเต็ม 1-30 / เครื่องต้อง available

add_rental(console_id, customer_name, phone, days) -> tuple[bool, str]
    # validate -> find_or_create_customer -> insert_rental -> set_console_status('rented')

return_console(rental_id) -> tuple[bool, str]
    # คิดราคา = daily_rate * วันที่เช่าจริง (ขั้นต่ำ 1 วัน)
    # เกิน due_date: ค่าปรับ = daily_rate * 0.5 ต่อวันที่เกิน
    # close_rental -> set_console_status('available')

get_all_consoles() -> list[dict]
get_available_consoles() -> list[dict]
get_all_rentals() -> list[dict]
```

ฟังก์ชันที่คืน `(ok, message)`: `ok=False` แปลว่าทำไม่สำเร็จ และ `message` เป็นข้อความภาษาไทยพร้อมแสดงใน `messagebox` ได้ทันที

### `ui.py` (Suthinun)
เรียกเฉพาะฟังก์ชันใน `logic.py` ข้างบน แท็บ: รายการเครื่อง / เช่าเครื่อง / คืนเครื่อง / ประวัติการเช่า

## ขั้นตอนทำงาน (Git)

1. แต่ละคนทำใน branch ของตัวเอง ห้าม push ตรงเข้า `main`
2. ทำเสร็จเปิด Pull Request เข้า `main`
3. ลำดับ merge: `database` → `logic` → `ui`
4. ก่อนเริ่มงานทุกครั้ง `git pull origin main` เข้ามาใน branch ตัวเอง

## รัน

```
python ui.py
```