from database.db import SessionLocal
from database.models_db import Match, Prediction
import datetime
from run_real_injection import check_golden_filters

db = SessionLocal()
now = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
tomorrow = now + datetime.timedelta(days=2)

matches = db.query(Match).join(Prediction).filter(
    Match.date >= now, Match.date <= tomorrow,
    Prediction.ai_verdict == 'APROVADO'
).all()

print("📋 RELATÓRIO DE AUDITORIA: MOTIVO DAS EXCLUSÕES DE HOJE (10/09)")
for m in matches:
    if m.date.strftime("%Y-%m-%d") != "2026-09-10": continue
    print(f"\n⚽ {m.home_team} x {m.away_team} ({m.date.strftime('%H:%M')})")
    for p in m.predictions:
        if p.ai_verdict != 'APROVADO': continue
        if "UNDER" in p.target_score:
            passed = check_golden_filters(m.home_team, m.away_team, p.target_score, p.power_score)
            status = "✅ INJETADO" if passed else "❌ VETADO (Filtro de Ouro Estatístico)"
            print(f"   -> {p.target_score}: {status}")
        else:
            if p.match_odd and p.match_odd > 2.0:
                print(f"   -> {p.target_score}: ❌ VETADO (Odd do favorito > 2.0)")
            elif p.power_score < 94.0:
                print(f"   -> {p.target_score}: ❌ VETADO (Score {p.power_score:.1f} < 94.0 Mínimo)")
            else:
                print(f"   -> {p.target_score}: ✅ INJETADO")

db.close()
