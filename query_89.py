from database.db import SessionLocal
from database.models_db import Prediction
db = SessionLocal()

above_89 = db.query(Prediction).filter(Prediction.is_hit.isnot(None), Prediction.power_score >= 89.0).all()
hits = sum(1 for p in above_89 if p.is_hit)
total = len(above_89)
if total > 0:
    print(f"Total >= 89.0: {total}, Hits: {hits}, Winrate: {hits/total*100:.1f}%")
else:
    print("0")
db.close()
