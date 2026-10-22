import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the repository
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(BASE_DIR / '.env')

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '').strip()

# Support multiple admin IDs (comma-separated, e.g. "5636475083,123456789")
admin_ids_raw = os.getenv('TELEGRAM_ADMIN_CHAT_ID', '') or os.getenv('TELEGRAM_ADMIN_IDS', '')
ADMIN_IDS = []
for item in str(admin_ids_raw).split(','):
    item = item.strip()
    if item.isdigit():
        ADMIN_IDS.append(int(item))

# Assets paths
ASSETS_DIR = BASE_DIR / 'bot' / 'assets'
ICONS_DIR = ASSETS_DIR / 'icons'
CHEATSHEET_IMG = ASSETS_DIR / 'icons_cheatsheet.png'

MEDIA_DIR = BASE_DIR / 'media'
MEDIA_BRANDS_DIR = MEDIA_DIR / 'brands'
MEDIA_PHONES_DIR = MEDIA_DIR / 'phones'

os.makedirs(MEDIA_BRANDS_DIR, exist_ok=True)
os.makedirs(MEDIA_PHONES_DIR, exist_ok=True)
