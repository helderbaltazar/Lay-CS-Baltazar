import sys
import os
import time
from datetime import datetime

# Garante que scripts na subpasta vejam os módulos da raiz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import SessionLocal
from database.models_db import Match, Prediction
from data.api_football import get_headers
import requests
import config

def backfill_odds(limit=50):
    db = SessionLocal()
    
    # Busca predições sem match_odd, onde o jogo já terminou
    # Filtramos predições Over/Under 2.5 e Correct Scores alvo para priorizar
    predictions = db.query(Prediction).join(Match).filter(
        Prediction.match_odd == None,
        Match.status.in_(['FT', 'AET', 'PEN'])
    ).limit(limit).all()
    
    if not predictions:
        print("Nenhuma predição aguardando backfill.")
        db.close()
        return

    print(f"Iniciando backfill de {len(predictions)} predições...")
    
    updated = 0
    # Cache local para não chamar a mesma fixture múltiplas vezes
    fixture_odds_cache = {}
    
    for pred in predictions:
        match = db.query(Match).filter(Match.id == pred.match_id).first()
        fixture_id = match.fixture_id
        
        if fixture_id not in fixture_odds_cache:
            url = f"{config.BASE_URL}/odds?fixture={fixture_id}&bookmaker=8" # Bet365
            try:
                resp = requests.get(url, headers=get_headers())
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get('response') and len(data['response']) > 0:
                        bookmakers = data['response'][0].get('bookmakers', [])
                        if bookmakers:
                            markets = bookmakers[0].get('bets', [])
                            fixture_odds_cache[fixture_id] = markets
                        else:
                            fixture_odds_cache[fixture_id] = []
                    else:
                        fixture_odds_cache[fixture_id] = []
                else:
                    fixture_odds_cache[fixture_id] = []
                # Evita estourar rate limit bruscamente (10 req/s da API-Football)
                time.sleep(0.2)
            except Exception as e:
                print(f"Erro ao buscar fixture {fixture_id}: {e}")
                fixture_odds_cache[fixture_id] = []
                
        markets = fixture_odds_cache[fixture_id]
        odd_found = None
        
        target = pred.target_score
        if target == "OVER_2.5":
            for m in markets:
                if m['name'] == 'Goals Over/Under':
                    for v in m['values']:
                        if v['value'] == 'Over 2.5':
                            odd_found = float(v['odd'])
                            break
        elif target == "UNDER_2.5":
            for m in markets:
                if m['name'] == 'Goals Over/Under':
                    for v in m['values']:
                        if v['value'] == 'Under 2.5':
                            odd_found = float(v['odd'])
                            break
        else:
            # Correct Score
            for m in markets:
                if m['name'] == 'Exact Score':
                    for v in m['values']:
                        if v['value'].replace(':', '-') == target:
                            odd_found = float(v['odd'])
                            break
                            
        if odd_found:
            pred.match_odd = odd_found
            # Re-calcula EV retrospectivo (Backtest param)
            pred.ev = (pred.probability * odd_found) - 1
            updated += 1
            print(f"[OK] Fixture {fixture_id} | {target} | Odd: {odd_found}")
        else:
            # Marca como indisponível para não tentar de novo
            pred.match_odd = 1.0 # placeholder
            print(f"[X] Fixture {fixture_id} | {target} (Odd não encontrada)")
            
    db.commit()
    db.close()
    print(f"Backfill finalizado. {updated} predições atualizadas com sucesso.")

if __name__ == "__main__":
    backfill_odds(limit=10) # 10 para rodar rápido na POC
