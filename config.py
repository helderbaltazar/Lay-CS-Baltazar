import os
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY", "")
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
RAPID_API_KEY = os.getenv("RAPID_API_KEY", "")
BASE_URL = "https://v3.football.api-sports.io"
RAPID_API_URL = "https://api-football-v1.p.rapidapi.com/v3"

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

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data_store/database.sqlite3')

DASHBOARD_USERNAME = os.getenv("DASHBOARD_USERNAME", "admin")
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "laycs2026")

# GitHub API Token (para acionar workflow)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# IA Especialista em Lay Correct Score (RAG + Top 10)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
AI_ANALYST_ENABLED = os.getenv("AI_ANALYST_ENABLED", "True").lower() in ("true", "1", "yes")
AI_ANALYST_TOP_N = int(os.getenv("AI_ANALYST_TOP_N", 10))

