from database.db import SessionLocal
from database.models_db import Prediction, Match
db = SessionLocal()
import datetime

# check average prob of 0-1 overall
p_01_all = db.query(Prediction).filter(Prediction.target_score == '0-1').all()
avg_all = sum(p.probability for p in p_01_all) / len(p_01_all)

# check average prob for tomorrow
p_01_tom = db.query(Prediction).join(Match).filter(Match.date >= "2026-09-05", Match.date < "2026-09-06", Prediction.target_score == '0-1').all()
avg_tom = sum(p.probability for p in p_01_tom) / len(p_01_tom)

print(f"Média historica de prob 0-1: {avg_all:.3f}")
print(f"Média de amanhã de prob 0-1: {avg_tom:.3f}")

