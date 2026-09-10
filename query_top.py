import config
from database.db import SessionLocal
from database.models_db import TeamStatsCache, Match, Prediction
import datetime
import pytz

db = SessionLocal()
now_br = datetime.datetime.now(pytz.timezone(config.SCHEDULER_TIMEZONE))
tomorrow = (now_br + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

caches = db.query(TeamStatsCache).count()
print(f"Caches na DB: {caches}")

matches = db.query(Match).filter(Match.date >= tomorrow).all()
print(f"Jogos de amanha ({tomorrow}): {len(matches)}")

if matches:
    preds = db.query(Prediction).join(Match).filter(Match.date >= tomorrow).all()
    print(f"Predições geradas: {len(preds)}")
    for p in preds:
        if p.power_score > 90:
            print(f"- {p.match.home_team} vs {p.match.away_team} | Score: {p.power_score:.2f} | 0-1: {p.prob_lay_0_1:.2f}% | 0-2: {p.prob_lay_0_2:.2f}%")
else:
    print("Ainda não gravou os jogos de amanhã.")

db.close()
