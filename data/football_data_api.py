import requests
import os
import config

# Football-Data.org API Client
BASE_URL = "https://api.football-data.org/v4"
LEAGUE_MAP = {
    39: "PL",     # Premier League
    140: "PD",    # La Liga
    78: "BL1",    # Bundesliga
    135: "SA",    # Serie A
    61: "FL1",    # Ligue 1
    71: "BSA",    # Brasileirao
    88: "DED",    # Eredivisie
    94: "PPL"     # Primeira Liga
}

def get_headers():
    token = os.getenv("FOOTBALL_DATA_KEY", "")
    return {"X-Auth-Token": token} if token else {}

def get_fixtures(date_str):
    """Fallback fetch for today's fixtures using Football-Data"""
    url = f"{BASE_URL}/matches?dateFrom={date_str}&dateTo={date_str}"
    try:
        resp = requests.get(url, headers=get_headers())
        if resp.status_code == 200:
            return resp.json().get('matches', [])
        return []
    except Exception:
        return []

def get_team_stats(team_id, league_code):
    """Fallback fetch for team stats using Standings"""
    url = f"{BASE_URL}/competitions/{league_code}/standings"
    try:
        resp = requests.get(url, headers=get_headers())
        if resp.status_code == 200:
            standings = resp.json().get('standings', [])
            if standings:
                # Get TOTAL table (usually type='TOTAL')
                table = next((s['table'] for s in standings if s['type'] == 'TOTAL'), [])
                # We would need to map the team_id or name...
                return table
        return []
    except Exception:
        return []
