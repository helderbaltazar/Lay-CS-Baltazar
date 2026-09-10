import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import SessionLocal
from database.models_db import Match, Prediction
import datetime

db = SessionLocal()
tomorrow = datetime.date.today() + datetime.timedelta(days=1)
matches = db.query(Match).filter(Match.date >= str(tomorrow)).all()

# Sort matches by time
matches.sort(key=lambda x: x.date)

print(f"Jogos programados para {tomorrow}:\n")

for m in matches:
    print(f"--- {m.date.strftime('%H:%M')} | {m.home_team} x {m.away_team} ---")
    preds = db.query(Prediction).filter(Prediction.match_id == m.id).all()
    
    # Sort predictions logically
    def sort_key(p):
        if p.target_score.startswith("UNDER"): return "Z" + p.target_score
        return p.target_score
    
    preds.sort(key=sort_key)
    
    if not preds:
        print("  (Sem predições)")
    for p in preds:
        score = p.power_score if p.power_score is not None else 0.0
        print(f"  [{p.target_score:<12}] Power Score: {score:5.1f} (Prob: {p.probability*100:4.1f}%)")
    print("")
