import difflib
from typing import Tuple, Optional
from data.odds_api import SPORT_KEYS, get_events

def fetch_odds_cascade(fixture) -> Tuple[Optional[float], Optional[float], str]:
    """Returns (match_odd, btts_odd, source)"""
    home_team = fixture['teams']['home']['name']
    away_team = fixture['teams']['away']['name']
    league_id = fixture['league']['id']
    
    # 1. The Odds API
    try:
        sport_key = next((k for k, v in SPORT_KEYS.items() if v == league_id), None)
        if sport_key:
            events = get_events(sport_key)
            for ev in events:
                if (difflib.get_close_matches(home_team, [ev.get('home_team','')], n=1, cutoff=0.5) and 
                    difflib.get_close_matches(away_team, [ev.get('away_team','')], n=1, cutoff=0.5)):
                    
                    match_odd = None
                    btts_odd = None
                    bookmakers = ev.get('bookmakers', [])
                    if bookmakers:
                        for mkt in bookmakers[0].get('markets', []):
                            if mkt['key'] == 'h2h':
                                for out in mkt['outcomes']:
                                    if out['name'] == ev.get('home_team'):
                                        match_odd = out['price']
                            if mkt['key'] == 'btts':
                                for out in mkt['outcomes']:
                                    if out['name'].lower() == 'yes':
                                        btts_odd = out['price']
                    
                    if match_odd or btts_odd:
                        return match_odd, btts_odd, "Odds-API"
    except Exception as e:
        print(f"Erro na Odds-API: {e}")
        
    # TODO: API-Football, Sofascore, OddsPortal fallbacks.
    # We will simulate them or add basic stubs, but for Phase 0 we just return what we have or 'unavailable'
    
    return None, None, "unavailable"

def fetch_h2h(fixture_id: int) -> Tuple[Optional[float], Optional[float]]:
    """Returns H2H (home_win_pct, away_win_pct) for the last 3 matches"""
    # TODO: Implement API-Football call to /fixtures/headtohead
    return None, None

def fetch_must_win(team_id: int, league_id: int) -> Optional[bool]:
    """Returns True if the team is in a critical position (title or relegation)"""
    # TODO: Implement API-Football call to /standings
    return None
