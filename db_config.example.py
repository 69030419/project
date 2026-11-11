# ตัวอย่างการตั้งค่าสำหรับระบบร้านเช่าเครื่องเกม
# ให้คัดลอกไฟล์นี้แล้วเปลี่ยนชื่อเป็น db_config.py พร้อมใส่ค่าจริง
# (ไฟล์ db_config.py จะถูก ignore โดย Git ไม่ให้หลุดขึ้น repo)

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "game_rental",
    "user": "postgres",
    "password": "ใส่รหัสผ่านของ PostgreSQL",
}

# (ไม่บังคับ) หากใช้ URL สาธารณะแบบคงที่ ให้ใส่ URL เช่น Cloudflare Named Tunnel
# หากไม่ใส่ แอปพนักงานจะเปิด Cloudflare Quick Tunnel และใช้ URL ชั่วคราวให้อัตโนมัติ
# CUSTOMER_WEB_URL = "https://your-public-domain.trycloudflare.com"
