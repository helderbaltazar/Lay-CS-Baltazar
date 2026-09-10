import os
import datetime
import pytz
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models_db import Match, Prediction
from run_real_injection import check_golden_filters

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)
db = Session()

now_br = datetime.datetime.now(pytz.timezone("America/Sao_Paulo"))
day_start = now_br.replace(hour=0, minute=0, second=0, microsecond=0)

# Pega jogos de hoje em diante
matches = db.query(Match).filter(Match.date >= day_start).all()

count = 0
for m in matches:
    for p in m.predictions:
        if "UNDER_" in p.target_score:
            passed = check_golden_filters(m.home_team, m.away_team, p.target_score, p.power_score)
            if not passed:
                p.ai_verdict = 'REPROVADO'
                p.ai_critical_factor = 'Filtro Ouro Telegram: Reprovado no Soma_HT ou Efic_xG'
                count += 1
            else:
                if p.ai_verdict == 'REPROVADO' and 'Filtro Ouro' in str(p.ai_critical_factor):
                    p.ai_verdict = 'APROVADO'
                    p.ai_critical_factor = 'Aprovado na Régua de Ouro'

db.commit()
print(f"Atualizados {count} mercados de Under reprovados nos jogos futuros.")
