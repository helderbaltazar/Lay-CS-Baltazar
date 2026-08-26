import requests
import time
from data.league_config import MAIN_LEAGUES, DOMESTIC_LEAGUE_MAP
from data import cache
import config

def get_headers():
    return {
        'x-apisports-key': config.API_KEY
    }

def get_fixtures(date_str):
    url = f"{config.BASE_URL}/fixtures?date={date_str}&timezone={config.SCHEDULER_TIMEZONE}"
    try:
        response = requests.get(url, headers=get_headers())
        response.raise_for_status()
        data = response.json()
        return filter_main_leagues(data.get('response', []))
    except Exception as e:
        print(f"Error fetching fixtures: {e}")
        return []

def filter_main_leagues(fixtures):
    filtered = []
    for f in fixtures:
        league_id = f['league']['id']
        if league_id in MAIN_LEAGUES:
            filtered.append(f)
    return filtered

def get_team_domestic_league(team_id, current_league_id):
    if team_id in DOMESTIC_LEAGUE_MAP:
        return DOMESTIC_LEAGUE_MAP[team_id]
    return current_league_id

def fetch_team_stats(team_id, league_id, season):
    url = f"{config.BASE_URL}/teams/statistics?league={league_id}&season={season}&team={team_id}"
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()
    data = response.json()
    if data.get('results') == 0 or not data.get('response'):
        return None
    return data['response']

def get_team_stats(team_id, competition_id):
    league_id = get_team_domestic_league(team_id, competition_id)
    cache_key = f"stats_{team_id}_{league_id}"
    
    cached = cache.get(cache_key)
    if cached:
        return cached

    seasons_to_try = [2024, 2023, 2022]
    
    for season in seasons_to_try:
        time.sleep(0.3) # Rate limit API Free
        try:
            stats = fetch_team_stats(team_id, league_id, season)
            if stats:
                cache.set(cache_key, stats)
                return stats
        except Exception as e:
            continue
            
    return None
