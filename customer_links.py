"""Build customer portal links that can be used from the shop's local network or cloud."""
import os
import socket
from urllib.parse import urlencode, urlparse


CUSTOMER_WEB_PORT = 8550


def customer_web_base_url():
    configured_url = os.environ.get("CUSTOMER_WEB_URL", "").strip()
    if not configured_url:
        try:
            import GitHub.projectnew1.db_config as db_config
            configured_url = getattr(db_config, "CUSTOMER_WEB_URL", "").strip()
        except Exception:
            pass

    if configured_url:
        parsed_url = urlparse(configured_url)
        if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
            raise ValueError("CUSTOMER_WEB_URL ต้องเป็น URL แบบ http:// หรือ https://")
        return configured_url.rstrip("/")

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
        connection.connect(("8.8.8.8", 80))
        local_ip = connection.getsockname()[0]
    return f"http://{local_ip}:{CUSTOMER_WEB_PORT}"


def rental_url(access_code):
    query = urlencode({"code": access_code})
    return f"{customer_web_base_url()}/?{query}"
