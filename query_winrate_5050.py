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

results = {"0-1": [], "0-2": [], "0-3": [], "1-3": []}

for p, m in preds:
    if p.target_score in results:
        res = eval_bet(p.target_score, m.real_score)
        if res:
            results[p.target_score].append({"score": p.power_score, "result": res})

for t in results:
    data = results[t]
    print(f"\n--- Mercado: {t} ---")
    
    # Calculate REDs
    reds = [x for x in data if x['result'] == 'RED']
    if reds:
        print(f"Total de REDs históricos: {len(reds)}")
        print("Scores dos REDs:")
        reds.sort(key=lambda x: x['score'], reverse=True)
        for r in reds:
            print(f"  RED com Score: {r['score']:.2f}")
    else:
        print("0 REDs históricos.")

db.close()
