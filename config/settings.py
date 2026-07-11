import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Безопасное чтение списка ID пользователей
raw_admin_ids = os.getenv("ADMIN_ID", "0").split(",")
ADMIN_IDS = [int(x.strip()) for x in raw_admin_ids if x.strip() and x.strip() != "0"]

# Чтение ID семейного чата
raw_chat_id = os.getenv("FAMILY_CHAT_ID")
FAMILY_CHAT_ID = int(raw_chat_id.strip()) if raw_chat_id else None

# Настройки Авито
TARGET_AVITO_URL = os.getenv("TARGET_AVITO_URL")
AVITO_CHECK_INTERVAL = int(os.getenv("AVITO_CHECK_INTERVAL", "900"))

# Настройки Циан
TARGET_CYAN_URL = os.getenv("TARGET_CYAN_URL")
CYAN_CHECK_INTERVAL = int(os.getenv("CYAN_CHECK_INTERVAL", "900"))

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/flat_pulse.db")
