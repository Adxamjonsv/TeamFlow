import hmac
import hashlib
import json
import urllib.parse
from typing import Optional, Dict, Any
from config import settings

def verify_telegram_init_data(init_data_raw: str) -> Optional[Dict[str, Any]]:
    """
    Telegram WebApp initData ni tekshiradi va foydalanuvchi ma'lumotlarini qaytaradi.
    """
    if not init_data_raw:
        return None

    try:
        parsed_data = dict(urllib.parse.parse_qsl(init_data_raw, keep_blank_values=True))
        received_hash = parsed_data.pop("hash", None)
        if not received_hash:
            return None

        # Parametrlarni alifbo tartibida saralash
        data_check_list = [f"{k}={v}" for k, v in sorted(parsed_data.items())]
        data_check_string = "\n".join(data_check_list)

        # secret_key = HMAC_SHA256("WebAppData", bot_token)
        secret_key = hmac.new(b"WebAppData", settings.BOT_TOKEN.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        if calculated_hash != received_hash:
            return None

        # Foydalanuvchi ma'lumotlarini json dan olish
        user_json = parsed_data.get("user")
        if user_json:
            user_data = json.loads(user_json)
            return user_data

        return parsed_data
    except Exception:
        return None

