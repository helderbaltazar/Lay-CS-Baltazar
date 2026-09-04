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

def print_bracket(name, data, min_score, max_score):
    subset = [x for x in data if min_score <= x['score'] < max_score]
    total = len(subset)
    if total == 0:
        print(f"  {name}: Sem jogos")
        return
    greens = len([x for x in subset if x['result'] == 'GREEN'])
    print(f"  {name} (Score {min_score} a {max_score}): {greens}/{total} Greens ({greens/total*100:.1f}%)")

for t in results:
    data = results[t]
    print(f"\n--- Mercado: {t} ---")
    print_bracket("Faixa Ouro", data, 99.0, 100.0)
    print_bracket("Faixa Prata", data, 94.0, 99.0)
    print_bracket("Faixa Bronze", data, 89.0, 94.0)
    print_bracket("Faixa Risco", data, 80.0, 89.0)

db.close()
