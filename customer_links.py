"""Build customer portal links using a configured public URL."""
import os
from urllib.parse import urlencode, urlparse


def configured_customer_web_url():
    configured_url = os.environ.get("CUSTOMER_WEB_URL", "").strip()
    if not configured_url:
        try:
            import db_config
        except ModuleNotFoundError as error:
            if error.name != "db_config":
                raise
        else:
            configured_url = getattr(db_config, "CUSTOMER_WEB_URL", "").strip()

    if configured_url:
        parsed_url = urlparse(configured_url)
        if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
            raise ValueError("CUSTOMER_WEB_URL ต้องเป็น URL แบบ http:// หรือ https://")
        return configured_url.rstrip("/")
    return None


def customer_web_base_url():
    configured_url = configured_customer_web_url()
    if configured_url:
        return configured_url
    raise RuntimeError(
        "ยังไม่มี URL สาธารณะ กรุณาเริ่มแอปด้วย ui_flet.py เพื่อเปิด Cloudflare Tunnel"
    )


def rental_url(access_code):
    query = urlencode({"code": access_code})
    return f"{customer_web_base_url()}/?{query}"
