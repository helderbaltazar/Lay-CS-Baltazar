import requests
import config
from database.db import SessionLocal
from database.models_db import Match, Prediction
from data.api_football import get_headers
import datetime
import pytz

def update_pending_matches():
    print("\\n--- ATUALIZANDO RESULTADOS PENDENTES ---")
    db = SessionLocal()
    pending = db.query(Match).filter(Match.status.notin_(['FT', 'AET', 'PEN', 'CANC', 'PSTP', 'ABD'])).all()
    
    if not pending:
        print("Nenhum jogo pendente de atualização.")
        db.close()
        return

    print(f"{len(pending)} jogos encontrados pendentes.")
    
    # Agrupa por data (YYYY-MM-DD) para fazer apenas 1 request por dia pendente!
    dates_to_fetch = set([m.date.strftime('%Y-%m-%d') for m in pending])
    
    for date_str in dates_to_fetch:
        print(f"Buscando placares da data {date_str} na API (1 Request)...")
        url = f"{config.BASE_URL}/fixtures?date={date_str}&timezone={config.SCHEDULER_TIMEZONE}"
        try:
            resp = requests.get(url, headers=get_headers())
            data = resp.json()
            if data['response']:
                fixtures_dict = {f['fixture']['id']: f for f in data['response']}
                
                # Atualiza todos os jogos dessa data
                matches_in_date = [m for m in pending if m.date.strftime('%Y-%m-%d') == date_str]
                for match in matches_in_date:
                    if match.fixture_id in fixtures_dict:
                        fix = fixtures_dict[match.fixture_id]
                        status = fix['fixture']['status']['short']
                        match.status = status
                        
                        if status in ['FT', 'AET', 'PEN']:
                            goals = fix.get('goals', {})
                            if goals.get('home') is not None and goals.get('away') is not None:
                                real_score = f"{goals['home']}-{goals['away']}"
                                match.real_score = real_score
                                print(f"Atualizado: {match.home_team} {real_score} {match.away_team}")
                                
                                for pred in match.predictions:
                                    pred.is_hit = (real_score != pred.target_score)
                                    if pred.is_hit:
                                        pred.profit_loss = 0.935
                                    else:
                                        pred.profit_loss = -10.0
                        else:
                            print(f"Jogo {match.home_team} x {match.away_team} ainda com status {status}")
        except Exception as e:
            print(f"Erro ao atualizar data {date_str}: {e}")
            
    db.commit()
    db.close()
    print("Atualização concluída.")

if __name__ == "__main__":
    update_pending_matches()
