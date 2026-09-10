from update_results import update_pending_matches
from database.db import SessionLocal
from database.models_db import Match, Prediction
import datetime
from sqlalchemy import func

print("Atualizando resultados reais...")
update_pending_matches()

db = SessionLocal()
dates = ["2026-09-04", "2026-09-05", "2026-09-06"]

print("\n=== RESULTADOS DO FIM DE SEMANA (06/09) ===")
for target, threshold in [("0-1", 94.0), ("0-3", 99.2)]:
    print(f"\nMercado: Lay {target} (Min: {threshold})")
    
    preds = db.query(Prediction).join(Match).filter(
        Prediction.target_score == target,
        Prediction.power_score >= threshold,
        func.date(Match.date).in_(dates)
    ).all()
    
    for p in preds:
        m = p.match
        is_green = "✅ GREEN" if p.is_hit else ("⏳ PENDENTE" if p.is_hit is None else "❌ RED")
        print(f"{m.home_team} {m.real_score or '?'} {m.away_team} | Score: {p.power_score:.1f} | {is_green}")

db.close()
