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
    "0-1": [],
    "0-2": [],
    "0-3": [],
    "1-3": []
}

for p, m in preds:
    if p.target_score in targets and p.power_score is not None:
        targets[p.target_score].append({"home": m.home_team, "away": m.away_team, "score": p.power_score, "ai_verdict": p.ai_verdict})

with open("/Users/macgeint/.gemini/antigravity/brain/c2828760-7303-4e18-9dd3-5080f064b14a/jogos_amanha.md", "w") as f:
    f.write(f"# Grade de Jogos - {tomorrow}\n\n")
    f.write("Abaixo estão todos os jogos escaneados para amanhã com seus respectivos Power Scores.\n\n")
    
    for t in ["0-1", "0-2", "0-3", "1-3"]:
        f.write(f"## Mercado Lay {t}\n\n")
        f.write("| Mandante | Visitante | Power Score | Status IA |\n")
        f.write("|----------|-----------|-------------|-----------|\n")
        
        matches = targets[t]
        matches.sort(key=lambda x: x['score'], reverse=True)
        
        for m in matches:
            emoji = "✅" if m['ai_verdict'] == "APROVADO" else "❌"
            f.write(f"| {m['home']} | {m['away']} | **{m['score']:.2f}** | {emoji} {m['ai_verdict']} |\n")
        f.write("\n")

db.close()
