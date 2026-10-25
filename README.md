# ระบบร้านเช่าเครื่องเกม (Game Console Rental)

แอปเดสก์ท็อปด้วย Python + Tkinter (ttkbootstrap) + PostgreSQL สำหรับร้านให้เช่าเครื่องเกม
(โปรเจกต์วิชาเขียนโปรแกรม + วิชาฐานข้อมูล)

แอปมี 2 โหมดในโปรแกรมเดียว ใช้ฐานข้อมูลและ `logic.py` ชุดเดียวกัน:

| โหมด | ใช้โดย | ทำอะไรได้ |
|------|--------|-----------|
| **ลูกค้า** | ลูกค้าที่หน้าร้าน | ดูเครื่องว่าง / เช่าเครื่อง / ดูและคืนเครื่องของตัวเอง (ยืนยันตัวด้วยเบอร์โทร) |
| **พนักงาน** | พนักงานร้าน (ใส่ PIN) | ดูทุกเครื่อง / เช่า / คืน / ประวัติทั้งหมด / เพิ่มเครื่อง |

> สถานะ: โหมดพนักงาน (5 แท็บ) ใช้งานได้แล้ว
> โหมดลูกค้า และฟังก์ชันที่มีเครื่องหมาย 🆕 ด้านล่าง **อยู่ระหว่างตกลงกันในกลุ่ม** ยังไม่ต้องเขียนจนกว่าจะยืนยัน

## แบ่งงาน

| ไฟล์ | ผู้รับผิดชอบ | Branch | หน้าที่ |
|------|-------------|--------|---------|
| `ui.py` | Suthinun | `feature/suthinun-ui` | หน้าจอ Tkinter เรียกได้เฉพาะ `logic.py` |
| `logic.py` | Ariyawong | `feature/Ariyawong` | ตรวจสอบข้อมูล คิดราคา/ค่าปรับ เรียกได้เฉพาะ `database.py` |
| `database.py` | Kitthin | `feature/kitthin` | PostgreSQL เก็บ/ดึงข้อมูลอย่างเดียว ไม่มีกฎธุรกิจ |

กฎสำคัญ: **ui → logic → database** (ห้ามข้ามชั้น)

## ติดตั้งและตั้งค่า (ทุกคนทำในเครื่องตัวเอง)

1. ติดตั้ง PostgreSQL (มาพร้อม pgAdmin 4) แล้วสร้างฐานข้อมูลชื่อ `game_rental`
   ```sql
   CREATE DATABASE game_rental;
   ```
   หรือสร้างใน pgAdmin: คลิกขวา Databases → Create → Database...
2. ติดตั้งไลบรารี (ลงใน `.venv` ถ้าใช้)
   ```
   pip install psycopg2-binary ttkbootstrap
   ```
3. สร้างไฟล์ `db_config.py` ในโฟลเดอร์โปรเจกต์ (ไฟล์ใหม่ ไม่มีใน repo) วางโค้ดนี้แล้วแก้รหัสผ่านเป็นของ PostgreSQL ในเครื่องตัวเอง
   ```python
   DB_CONFIG = {
       "host": "localhost",
       "port": 5432,
       "dbname": "game_rental",
       "user": "postgres",
       "password": "ใส่รหัสผ่านของคุณ",
   }
   ```
4. **ห้าม commit `db_config.py`** (มีรหัสผ่าน และ repo เป็น Public) ไฟล์ `.gitignore` กันไว้แล้ว
5. รันแอป ตารางและเครื่องตัวอย่าง 4 เครื่องจะถูกสร้างให้อัตโนมัติครั้งแรก ไม่ต้องรัน SQL เอง

### หมายเหตุสำหรับ macOS
- ใช้ `python3` และ `pip3` แทน `python` / `pip`
- PostgreSQL ที่ลงด้วย Postgres.app หรือ Homebrew มักไม่มีรหัสผ่าน และ user คือชื่อบัญชีเครื่อง ให้แก้ `"user"` เป็นชื่อนั้น และตั้ง `"password": ""`
- ถ้า Tkinter ขึ้น `No module named '_tkinter'` ให้ติดตั้ง Python จาก python.org หรือ `brew install python-tk`
- ฟอนต์ Leelawadee UI ไม่มีบน Mac ระบบจะใช้ฟอนต์อื่นแทน

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
(ลูกค้า 1 คนเช่าได้หลายครั้ง เครื่อง 1 เครื่องถูกเช่าได้หลายครั้ง) ลูกค้าระบุด้วยเบอร์โทร (UNIQUE)

## รูปแบบข้อมูลที่ส่งข้ามไฟล์ (dict)

```python
console = {"console_id": 1, "name": "PS5 #1", "platform": "PS5",
           "daily_rate": 200.0, "status": "available"}

rental = {"rental_id": 1, "console_id": 1, "console_name": "PS5 #1",
          "daily_rate": 200.0, "customer_name": "สมชาย",
          "phone": "0812345678", "rent_date": "2026-10-24",
          "due_date": "2026-10-26", "return_date": None, "total_price": 400.0}
```

`console_id` และ `daily_rate` ของ rental ต้องมีเสมอ (JOIN จากตาราง consoles) เพราะ
`logic.return_console` ต้องใช้คิดราคาและเปลี่ยนสถานะเครื่อง ส่วน UI ไม่ได้ใช้สองคีย์นี้

ข้อตกลงเรื่องชนิดข้อมูล (PostgreSQL คืน `date` และ `Decimal` ซึ่งไม่เหมือนที่ชั้นบนต้องการ):
- `database.py` ต้องแปลงก่อนคืนเสมอ: วันที่เป็น string `YYYY-MM-DD` และ `NUMERIC` เป็น `float`
- วันที่ใช้รูปแบบ `YYYY-MM-DD` เสมอ
- เวลาส่งค่าเข้า SQL ใช้ placeholder `%s` เสมอ ห้ามต่อ string เอง (กัน SQL injection)

## สัญญาฟังก์ชัน

### `database.py` (Kitthin)
```python
init_db() -> None                                  # สร้างตารางถ้ายังไม่มี (เรียกอัตโนมัติอยู่แล้ว)
insert_console(name, platform, daily_rate) -> int  # INSERT ... RETURNING console_id
fetch_all_consoles() -> list[dict]
fetch_console(console_id) -> dict | None
set_console_status(console_id, status) -> None     # 'available' | 'rented'
find_or_create_customer(name, phone) -> int        # คืน customer_id
insert_rental(console_id, customer_id, rent_date, due_date) -> int   # RETURNING rental_id
fetch_all_rentals() -> list[dict]                  # rental dict (JOIN แล้ว)
fetch_rental(rental_id) -> dict | None
close_rental(rental_id, return_date, total_price) -> None
```

ทุกฟังก์ชันเปิด connection ผ่าน `psycopg2` ด้วยค่าใน `db_config.py`, `commit()` เมื่อสำเร็จ และปิด connection เสมอ
การเพิ่มโหมดลูกค้า **ไม่ต้องแก้ `database.py`** (กรองตามเบอร์ในชั้น logic)

### `logic.py` (Ariyawong)
ฟังก์ชันที่คืน `(ok, message)`: `ok=False` แปลว่าทำไม่สำเร็จ และ `message` เป็นข้อความภาษาไทยพร้อมแสดงใน `messagebox` ได้ทันที
UI ส่งค่าที่ผู้ใช้กรอกมาเป็น string (เช่น `days="2"`, `daily_rate="200"`) logic ต้องแปลงและตรวจเอง

```python
# ---- มีแล้ว ----
get_all_consoles() -> list[dict]
get_available_consoles() -> list[dict]
get_all_rentals() -> list[dict]

add_console(name, platform, daily_rate) -> tuple[bool, str]
    # ชื่อ/แพลตฟอร์มไม่ว่าง / ราคา > 0 / ชื่อเครื่องห้ามซ้ำ -> insert_console

validate_rental(console_id, customer_name, phone, days) -> tuple[bool, str]
    # ชื่อไม่ว่าง / เบอร์ 10 หลักตัวเลข / days เป็นจำนวนเต็ม 1-30 / เครื่องต้อง available

add_rental(console_id, customer_name, phone, days) -> tuple[bool, str]
    # validate -> find_or_create_customer -> insert_rental -> set_console_status('rented')

return_console(rental_id) -> tuple[bool, str]
    # คิดราคา = daily_rate * วันที่เช่าจริง (ขั้นต่ำ 1 วัน)
    # เกิน due_date: ค่าปรับ = daily_rate * 0.5 ต่อวันที่เกิน
    # close_rental -> set_console_status('available')

# ---- 🆕 สำหรับโหมดลูกค้า/พนักงาน (รอตกลง) ----
get_rentals_by_phone(phone) -> list[dict]
    # เรียก database.fetch_all_rentals() แล้วกรองเฉพาะ phone นี้ (ไม่ต้องแก้ database.py)

return_my_console(rental_id, phone) -> tuple[bool, str]
    # เช็กว่า rental นี้เป็นของ phone นี้จริงและยังไม่คืน แล้วเรียกตรรกะเดียวกับ return_console

check_staff_pin(pin) -> bool
    # เทียบกับค่า STAFF_PIN ที่ตั้งไว้บนหัวไฟล์ (ไม่ใช่ความปลอดภัยจริง แค่กันลูกค้าเข้าโหมดพนักงาน)
```

ค่าที่ร้านกำหนด (แก้ที่หัวไฟล์ `logic.py` ที่เดียว): เช่า 1-30 วัน, เบอร์โทร 10 หลัก,
ค่าปรับเกินกำหนด = ครึ่งหนึ่งของราคา/วัน, ขั้นต่ำคิดเงิน 1 วัน

### `ui.py` (Suthinun)
เรียกเฉพาะฟังก์ชันใน `logic.py` ข้างบน

- **โหมดพนักงาน** (มีแล้ว): รายการเครื่อง / เช่าเครื่อง / คืนเครื่อง / ประวัติการเช่า / เพิ่มเครื่อง
- **🆕 หน้าเลือกโหมด** ตอนเปิดแอป: ปุ่ม "ลูกค้า" และ "พนักงาน" (ใส่ PIN ก่อนเข้า)
- **🆕 โหมดลูกค้า**: เครื่องที่ว่าง / เช่าเครื่อง / การเช่าของฉัน (กรอกเบอร์ เห็นเฉพาะของตัวเอง และกดคืนได้)

ข้อจำกัดที่รู้อยู่: ยืนยันตัวลูกค้าด้วยเบอร์โทรอย่างเดียว ใครรู้เบอร์คนอื่นก็ดูรายการเช่าของเขาได้
(ยอมรับได้สำหรับงานวิชา ถ้าต้องการปลอดภัยขึ้นค่อยเพิ่มรหัสผ่านลูกค้าทีหลัง)

## ขั้นตอนทำงาน (Git)

1. แต่ละคนทำใน branch ของตัวเอง ห้าม push ตรงเข้า `main`
2. ทำเสร็จเปิด Pull Request เข้า `main`
3. ลำดับ merge: `database` → `logic` → `ui`
4. ก่อนเริ่มงานทุกครั้ง `git pull origin main` เข้ามาใน branch ตัวเอง
5. `git add` ให้ระบุชื่อไฟล์ ไม่ใช้ `git add .` และเช็ก `git status` ก่อน commit ทุกครั้ง
6. ห้าม commit: `db_config.py`, `.venv/`, `__pycache__/`

## รัน

```
python ui.py        # macOS ใช้ python3 ui.py
```