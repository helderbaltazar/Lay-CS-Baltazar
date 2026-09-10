import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import SessionLocal
from database.models_db import Match, Prediction
import datetime

db = SessionLocal()
today_start = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

preds = db.query(Prediction).join(Match).filter(
    Prediction.target_score == "UNDER_0.5_HT",
    Match.date >= str(today_start)
).all()

for p in preds:
    print(f"Match: {p.match.home_team} x {p.match.away_team} | Date: {p.match.date} | Score: {p.power_score}")
