import config
from database.db import SessionLocal
from database.models_db import Prediction

db = SessionLocal()
above_90 = db.query(Prediction).filter(Prediction.is_hit.isnot(None), Prediction.power_score >= 90.0).all()
hits = sum(1 for p in above_90 if p.is_hit)
total = len(above_90)
print(f"Total >= 90: {total}, Hits: {hits}")

almost_90 = db.query(Prediction).filter(Prediction.is_hit.isnot(None), Prediction.power_score >= 89.5).all()
hits2 = sum(1 for p in almost_90 if p.is_hit)
total2 = len(almost_90)
print(f"Total >= 89.5: {total2}, Hits: {hits2}")

db.close()
