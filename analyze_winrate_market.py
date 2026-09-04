import config
from database.db import SessionLocal
from database.models_db import Prediction, Match
from collections import defaultdict

db = SessionLocal()
preds = db.query(Prediction).join(Match).filter(Prediction.is_hit.isnot(None), Prediction.power_score.isnot(None)).all()

markets = defaultdict(lambda: {"85-90+": {'h':0, 't':0}, "80-84": {'h':0, 't':0}, "< 80": {'h':0, 't':0}})

for p in preds:
    score = p.power_score
    if score >= 85:
        b = "85-90+"
    elif score >= 80:
        b = "80-84"
    else:
        b = "< 80"
        
    markets[p.target_score][b]['t'] += 1
    if p.is_hit:
        markets[p.target_score][b]['h'] += 1

print("--- Winrate por Mercado e Power Score ---")
for mkt, data in markets.items():
    print(f"\nMercado: {mkt}")
    for b in ["85-90+", "80-84", "< 80"]:
        v = data[b]
        if v['t'] > 0:
            wr = (v['h'] / v['t']) * 100
            print(f"  Score {b}: {v['h']}/{v['t']} ({wr:.1f}%)")

db.close()
