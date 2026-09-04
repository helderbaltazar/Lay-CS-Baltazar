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

targets = {
    "0-1": {"threshold": 85.0, "matches": []},
    "0-2": {"threshold": 85.0, "matches": []},
    "0-3": {"threshold": 89.4, "matches": []},
    "1-3": {"threshold": 89.4, "matches": []},
}

for p, m in preds:
    if p.target_score in targets:
        if p.power_score is not None and p.power_score >= targets[p.target_score]["threshold"]:
            targets[p.target_score]["matches"].append(
                {"home": m.home_team, "away": m.away_team, "score": p.power_score, "ai": p.ai_confidence, "math": p.probability}
            )

print(f"--- Indicações Principais para {tomorrow} ---")
for t, data in targets.items():
    print(f"\nMercado {t} (Corte >= {data['threshold']}): {len(data['matches'])} aprovados")
    data["matches"].sort(key=lambda x: x['score'], reverse=True)
    if not data["matches"]:
        print("  Nenhuma indicação aprovada.")
    for x in data["matches"][:3]:
        print(f"  ⚽ {x['home']} x {x['away']} -> Score: {x['score']:.2f}")
    if len(data["matches"]) > 3:
        print(f"  ... e mais {len(data['matches']) - 3} jogos.")

db.close()
