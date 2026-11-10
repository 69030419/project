# ตัวอย่างการตั้งค่าฐานข้อมูล PostgreSQL ในเครื่อง
# ให้คัดลอกไฟล์นี้แล้วเปลี่ยนชื่อเป็น db_config.py พร้อมใส่รหัสผ่านจริง
# (ไฟล์ db_config.py จะถูก ignore โดย Git ไม่ให้หลุดขึ้น repo)

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "game_rental",
    "user": "postgres",
    "password": "ใส่รหัสผ่านของ PostgreSQL",
}
