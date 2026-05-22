import sys
from pathlib import Path

# BASE_DIR = thư mục gốc chứa main.py (tự động, không hardcode)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Thư mục
DATA_DIR = BASE_DIR / 'data'
ASSETS_DIR = BASE_DIR / 'assets'
WEBSITES_DIR = BASE_DIR / 'websites'

# File dữ liệu
CACHES_FILE = DATA_DIR / 'caches.json'
CONFIGS_FILE = DATA_DIR / 'configs.json'
SETTINGS_FILE = DATA_DIR / 'settings.json'
TOKENS_FILE = DATA_DIR / 'tokens.txt'

# Assets chung
MESSAGES_FILE = ASSETS_DIR / 'messages.txt'
NOTIFICATION_AUDIO = ASSETS_DIR / 'notification.mp3'
LOGO_PATH = ASSETS_DIR / 'logo.png'

# Tên hiển thị
APP_NAME = 'Phamdat Selfbot'