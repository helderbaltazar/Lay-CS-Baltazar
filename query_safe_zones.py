from database.db import SessionLocal
from database.models_db import Prediction

db = SessionLocal()

for target in ["0-3", "1-3"]:
    preds = db.query(Prediction).filter(Prediction.is_hit.isnot(None), Prediction.target_score == target).all()
    reds = [p.power_score for p in preds if not p.is_hit]
    min_red = min(reds) if reds else 100
    max_red = max(reds) if reds else 0
    
    # Check games below min_red
    below_min = [p for p in preds if p.power_score < min_red]
    below_min_hits = sum(1 for p in below_min if p.is_hit)
    print(f"{target}: Abaixo de {min_red:.2f} -> {below_min_hits} jogos (Winrate: {below_min_hits/len(below_min)*100 if below_min else 0}%)")

    # Check games above max_red
    above_max = [p for p in preds if p.power_score > max_red]
    above_max_hits = sum(1 for p in above_max if p.is_hit)
    print(f"{target}: Acima de {max_red:.2f} -> {above_max_hits} jogos (Winrate: {above_max_hits/len(above_max)*100 if above_max else 0}%)")
    
    # Are there any "safe gaps" in between?
    reds.sort()
    for i in range(len(reds)-1):
        gap_start = reds[i]
        gap_end = reds[i+1]
        in_gap = [p for p in preds if gap_start < p.power_score < gap_end]
        if len(in_gap) > 10: # Only print significant gaps
            hits = sum(1 for p in in_gap if p.is_hit)
            if hits == len(in_gap):
                print(f"{target}: Gap seguro entre {gap_start:.2f} e {gap_end:.2f} -> {hits} jogos (Winrate: 100%)")

db.close()
