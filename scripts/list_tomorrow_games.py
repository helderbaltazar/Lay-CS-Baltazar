import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import SessionLocal
from database.models_db import Match
import datetime

db = SessionLocal()
tomorrow = datetime.date.today() + datetime.timedelta(days=1)
matches = db.query(Match).filter(Match.date >= str(tomorrow)).all()
matches.sort(key=lambda x: x.date)

print(f"==================================================")
print(f"JOGOS PROGRAMADOS PARA {tomorrow}")
print(f"Total de partidas na base: {len(matches)}")
print(f"==================================================\n")

for m in matches:
    print(f"[{m.date.strftime('%H:%M')}] {m.league_name} | {m.home_team} x {m.away_team}")
