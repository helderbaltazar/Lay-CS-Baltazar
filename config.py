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
