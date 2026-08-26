import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY", "")
BASE_URL = "https://v3.football.api-sports.io"

TARGET_SCORES = ["0-1", "0-2", "0-3", "1-3"]
DIXON_COLES_RHO = -0.10
MAX_GOALS = 7

PORT = int(os.getenv("PORT", 5000))
SCHEDULER_TIMEZONE = "America/Sao_Paulo"

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
BANKROLL = float(os.getenv('BANKROLL', '1000.0'))
MAX_LIABILITY = float(os.getenv('MAX_LIABILITY', '2.0')) # Em %

LAYBACK_EMAIL = os.getenv('LAYBACK_EMAIL', '')
LAYBACK_PASSWORD = os.getenv('LAYBACK_PASSWORD', '')
