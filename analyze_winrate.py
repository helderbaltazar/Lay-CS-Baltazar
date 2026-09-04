import config
from database.db import SessionLocal
from database.models_db import Prediction, Match
from sqlalchemy.orm import joinedload

db = SessionLocal()

# Apenas partidas já encerradas onde is_hit não é nulo
preds = db.query(Prediction).join(Match).filter(Prediction.is_hit.isnot(None), Prediction.power_score.isnot(None)).all()

buckets = {
    ">= 95": {'hits': 0, 'total': 0},
    "90-94": {'hits': 0, 'total': 0},
    "85-89": {'hits': 0, 'total': 0},
    "80-84": {'hits': 0, 'total': 0},
    "< 80": {'hits': 0, 'total': 0},
}

for p in preds:
    # Apenas os mercados "principais" de Lay CS se quisermos, ou todos?
    # Vamos agrupar todos, e depois por mercado se for o caso
    score = p.power_score
    if score >= 95:
        b = ">= 95"
    elif score >= 90:
        b = "90-94"
    elif score >= 85:
        b = "85-89"
    elif score >= 80:
        b = "80-84"
    else:
        b = "< 80"
        
    buckets[b]['total'] += 1
    if p.is_hit:
        buckets[b]['hits'] += 1

print("--- Winrate por Power Score Geral ---")
for k, v in buckets.items():
    if v['total'] > 0:
        wr = (v['hits'] / v['total']) * 100
        print(f"Power Score {k}: {v['hits']}/{v['total']} hits ({wr:.1f}%)")
    else:
        print(f"Power Score {k}: Sem dados")

db.close()
