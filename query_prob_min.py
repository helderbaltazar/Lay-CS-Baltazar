from database.db import SessionLocal
from database.models_db import Prediction, Match
db = SessionLocal()
p_01_tom = db.query(Prediction).join(Match).filter(Match.date >= "2026-09-05", Match.date < "2026-09-06", Prediction.target_score == '0-1').all()
min_prob = min(p.probability for p in p_01_tom)
print(f"Min prob tomorrow for 0-1: {min_prob:.3f}")
