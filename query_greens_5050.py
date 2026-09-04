from database.db import SessionLocal
from database.models_db import Prediction, Match

db = SessionLocal()
preds = db.query(Prediction, Match).join(Match).filter(Match.status == "FT", Prediction.power_score != None).all()

def eval_bet(target_score, real_score):
    if not real_score or '-' not in real_score:
        return None
    try:
        hr, ar = map(int, real_score.split('-'))
        th, ta = map(int, target_score.split('-'))
        return "RED" if hr == th and ar == ta else "GREEN"
    except:
        return None

results = {"0-1": {"red_max": 93.89}, "0-2": {"red_max": 93.98}, "0-3": {"red_max": 99.19}, "1-3": {"red_max": 99.30}}

for p, m in preds:
    if p.target_score in results:
        res = eval_bet(p.target_score, m.real_score)
        if res == "GREEN":
            if "greens" not in results[p.target_score]:
                results[p.target_score]["greens"] = []
            if p.power_score > results[p.target_score]["red_max"]:
                results[p.target_score]["greens"].append(p.power_score)

for t in results:
    greens = results[t].get("greens", [])
    print(f"\nMercado: {t}")
    print(f"GREENs acima do maior RED ({results[t]['red_max']}): {len(greens)} jogos.")
    if greens:
        print(f"Maior GREEN alcançado: {max(greens):.2f}")

db.close()
