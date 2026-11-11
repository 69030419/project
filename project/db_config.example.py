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

# (ไม่บังคับ) หากต้องการให้ QR Code ชี้ไปยังโดเมนอินเทอร์เน็ตสาธารณะ (เช่น Cloudflare Tunnel หรือ Cloud URL)
# หากไม่ใส่ ระบบจะใช้วง Wi-Fi ภายในร้าน (192.168.x.x) เป็นค่าเริ่มต้น
# CUSTOMER_WEB_URL = "https://your-public-domain.trycloudflare.com"
