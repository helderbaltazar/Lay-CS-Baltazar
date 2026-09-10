import config
from database.db import SessionLocal
from database.models_db import Prediction, Match
import datetime
import pytz

db = SessionLocal()
now_br = datetime.datetime.now(pytz.timezone(config.SCHEDULER_TIMEZONE))
tomorrow = (now_br + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

preds = db.query(Prediction, Match).join(Match).filter(
    Match.date >= tomorrow,
    Match.date < (now_br + datetime.timedelta(days=2)).strftime("%Y-%m-%d")
).all()

for t in ["0-1", "0-2", "0-3", "1-3"]:
    scores = [p.power_score for p, m in preds if p.target_score == t and p.power_score is not None]
    if scores:
        print(f"[{t}] Maior Score de Amanhã: {max(scores):.2f}")
