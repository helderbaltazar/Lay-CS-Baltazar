from database.db import SessionLocal
from database.models_db import Prediction
db = SessionLocal()

p_01 = db.query(Prediction).filter(Prediction.is_hit.isnot(None), Prediction.target_score == '0-1').order_by(Prediction.power_score.desc()).first()
p_02 = db.query(Prediction).filter(Prediction.is_hit.isnot(None), Prediction.target_score == '0-2').order_by(Prediction.power_score.desc()).first()

if p_01: print(f"Max 0-1 Score: {p_01.power_score:.2f}")
if p_02: print(f"Max 0-2 Score: {p_02.power_score:.2f}")
