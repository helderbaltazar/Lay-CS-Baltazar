import json
import time
from playwright.sync_api import sync_playwright

LEAGUE_MAPPING = {
    39: "EPL",
    140: "La_liga",
    78: "Bundesliga",
    135: "Serie_A",
    61: "Ligue_1"
}

def fetch_understat_xg(league_id, season="2026"):
    """
    Usa Playwright para buscar dados de xG/xGA da liga no Understat.
    Retorna dicionário: { "nome_do_time": {"xG_home": float, "xGA_home": float, "xG_away": float, ...} }
    """
    if league_id not in LEAGUE_MAPPING:
        return None
        
    understat_league = LEAGUE_MAPPING[league_id]
    result_data = None
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        def handle_response(response):
            nonlocal result_data
            if f"getLeagueData/{understat_league}/{season}" in response.url and response.status == 200:
                try:
                    result_data = response.json()
                except:
                    pass

        page.on("response", handle_response)
        
        try:
            page.goto(f"https://understat.com/league/{understat_league}/{season}", timeout=30000)
            page.wait_for_timeout(3500)
        except Exception as e:
            print(f"Erro no Understat Playwright para {understat_league}: {e}")
            
        browser.close()
        
    if not result_data or 'teams' not in result_data:
        return None
        
    teams_stats = {}
    for t_id, t_data in result_data['teams'].items():
        team_name = t_data.get('title')
        history = t_data.get('history', [])
        
        home_xg, home_xga, home_matches = 0, 0, 0
        away_xg, away_xga, away_matches = 0, 0, 0
        
        for match in history:
            xg = float(match.get('xG', 0))
            xga = float(match.get('xGA', 0))
            if match.get('h_a') == 'h':
                home_xg += xg
                home_xga += xga
                home_matches += 1
            else:
                away_xg += xg
                away_xga += xga
                away_matches += 1
                
        teams_stats[team_name] = {
            "xG_home_avg": (home_xg / home_matches) if home_matches else 0,
            "xGA_home_avg": (home_xga / home_matches) if home_matches else 0,
            "xG_away_avg": (away_xg / away_matches) if away_matches else 0,
            "xGA_away_avg": (away_xga / away_matches) if away_matches else 0,
            "matches_home": home_matches,
            "matches_away": away_matches
        }
        
    return teams_stats
