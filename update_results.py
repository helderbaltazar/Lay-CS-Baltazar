import requests
import config
from database.db import SessionLocal
from database.models_db import Match, Prediction
from data.api_football import get_headers
import datetime
import pytz


def resolve_prediction(pred, real_score, fixture_data=None):
    """Resolve uma predição com base no tipo de mercado e placar real.
    
    Para Lay CS clássico (0-1, 0-2, etc.): Green se o placar NÃO aconteceu.
    Para UNDER_X.5_HT: Green se total de gols no HT < X.
    """
    target = pred.target_score
    
    # Mercados UNDER do Half-Time
    if target.startswith("UNDER_") and target.endswith("_HT"):
        # Precisamos dos gols do HT para resolver
        ht_goals = None
        if fixture_data:
            score = fixture_data.get('score', {})
            halftime = score.get('halftime', {})
            ht_home = halftime.get('home')
            ht_away = halftime.get('away')
            if ht_home is not None and ht_away is not None:
                ht_goals = ht_home + ht_away
        
        if ht_goals is None:
            # Sem dados de HT, não podemos resolver
            return None, None
        
        # Extrair o threshold do nome do mercado (ex: UNDER_0.5_HT -> 0.5)
        try:
            threshold = float(target.replace("UNDER_", "").replace("_HT", ""))
        except ValueError:
            return None, None
        
        # Lay UNDER = apostamos CONTRA dar under. Green se DEU under (gols < threshold)
        # Na verdade, para Lay CS a lógica é: estamos fazendo LAY no mercado.
        # Lay Under 0.5 HT = apostamos que haverá 1+ gols no HT.
        # Green = Under 0.5 HT NÃO aconteceu (ou seja, houve gols)
        is_hit = ht_goals >= threshold  # Green se Under NÃO bateu
        profit = 0.935 if is_hit else -10.0
        return is_hit, profit
    
    # Mercados Lay Correct Score clássicos (0-1, 0-2, 0-3, 1-3)
    # Green se o placar exato NÃO aconteceu
    is_hit = (real_score != target)
    profit = 0.935 if is_hit else -10.0
    return is_hit, profit


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
            resp = requests.get(url, headers=get_headers(), timeout=30)
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
                                    is_hit, profit = resolve_prediction(pred, real_score, fix)
                                    if is_hit is not None:
                                        pred.is_hit = is_hit
                                        pred.profit_loss = profit
                                    else:
                                        print(f"  ⚠️ Não foi possível resolver {pred.target_score} (dados insuficientes)")
                        else:
                            print(f"Jogo {match.home_team} x {match.away_team} ainda com status {status}")
        except Exception as e:
            print(f"Erro ao atualizar data {date_str}: {e}")
            
    db.commit()
    db.close()
    print("Atualização concluída.")

if __name__ == "__main__":
    update_pending_matches()

