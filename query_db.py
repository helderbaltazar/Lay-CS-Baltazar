from database.db import SessionLocal
from database.models_db import Match, Prediction
from sqlalchemy import func
import datetime

db = SessionLocal()
today_str = "2026-09-07"
matches = db.query(Match).filter(func.date(Match.date) == today_str).all()

print(f"Total jogos encontrados em {today_str}: {len(matches)}")
for m in matches:
    print(f"\n--- {m.home_team} vs {m.away_team} ---")
    for p in m.predictions:
        print(f"  Target: {p.target_score} | Power Score: {p.power_score} | Prob: {p.probability}")
db.close()
