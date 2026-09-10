import config
from database.db import SessionLocal
from database.models_db import Match, Prediction
from data.odds_api import SPORT_KEYS, get_events
import json
from difflib import get_close_matches
import time

def fetch_and_update_odds():
    db = SessionLocal()
    print("Buscando dados na Odds-API...")
    
    odds_map = {} # chave: league_id, valor: lista de evs
    for sport_key, league_id in SPORT_KEYS.items():
        events = get_events(sport_key)
        for ev in events:
            home = ev.get('home_team', '')
            away = ev.get('away_team', '')
            bookmakers = ev.get('bookmakers', [])
            home_odd = away_odd = draw_odd = None
            if bookmakers:
                markets = bookmakers[0].get('markets', [])
                for mkt in markets:
                    if mkt['key'] == 'h2h':
                        for out in mkt['outcomes']:
                            if out['name'] == home: home_odd = out['price']
                            elif out['name'] == away: away_odd = out['price']
                            elif out['name'] == 'Draw': draw_odd = out['price']
            
            if league_id not in odds_map:
                odds_map[league_id] = []
                
            odds_map[league_id].append({
                'home': home,
                'away': away,
                'home_odd': home_odd,
                'away_odd': away_odd,
                'draw_odd': draw_odd,
                'commence_time': ev.get('commence_time')
            })
            
    print("Processando matches no banco de dados...")
    # Matches with no valid home odd
    matches = db.query(Match).all()
    updated = 0
    
    for m in matches:
        if m.league_name: # might need to map league_id but let's just do fuzzy match globally or per league
            # Actually, to make it robust, let's just match by home and away team
            pass
            
        found = False
        for lid, evs in odds_map.items():
            for ev in evs:
                # Fuzzy match names
                home_match = get_close_matches(m.home_team, [ev['home']], n=1, cutoff=0.6)
                away_match = get_close_matches(m.away_team, [ev['away']], n=1, cutoff=0.6)
                if home_match and away_match:
                    odds_dict = {'1': ev['home_odd'], 'X': ev['draw_odd'], '2': ev['away_odd']}
                    m.odds_data = json.dumps(odds_dict)
                    
                    # Update predictions
                    for p in m.predictions:
                        p.match_odd = ev['home_odd']
                        
                    found = True
                    updated += 1
                    break
            if found:
                break
                
    db.commit()
    db.close()
    print(f"✅ Odds atualizadas para {updated} jogos via Odds-API!")

if __name__ == "__main__":
    fetch_and_update_odds()
