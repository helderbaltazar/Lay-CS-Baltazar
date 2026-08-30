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
    cache_key = f"fixtures_{date_str}"
    cached = cache.get(cache_key, ttl_seconds=86400) # 24 horas de cache para os jogos do dia
    if cached is not None:
        print(f"Lendo jogos de {date_str} do cache...")
        return cached

    url = f"{config.BASE_URL}/fixtures?date={date_str}&timezone={config.SCHEDULER_TIMEZONE}"
    try:
        print(f"Buscando jogos de {date_str} na API...")
        response = requests.get(url, headers=get_headers())
        response.raise_for_status()
        data = response.json()
        
        # Se a API bater limite (429), ela pode retornar 200 com errors
        if data.get('errors') and len(data.get('errors')) > 0:
            print("Erro da API:", data.get('errors'))
            return []
            
        result = filter_main_leagues(data.get('response', []))
        cache.set(cache_key, result)
        return result
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
    
    cached = cache.get(cache_key, ttl_seconds=43200)
    if cached:
        return cached

    seasons_to_try = [2024, 2023, 2022]
    
    for season in seasons_to_try:
        time.sleep(6.1) # Rate limit API Free (10 per minute)
        try:
            stats = fetch_team_stats(team_id, league_id, season)
            if stats:
                cache.set(cache_key, stats)
                return stats
        except Exception as e:
            continue
            
    return None



def get_raw_odds(fixture_id):
    cache_key = f"raw_odds_{fixture_id}"
    cached = cache.get(cache_key, ttl_seconds=43200)
    if cached is not None:
        return cached

    url = f"{config.BASE_URL}/odds?fixture={fixture_id}&bookmaker=8"
    try:
        response = requests.get(url, headers=get_headers())
        data = response.json()
        if not data.get('response'):
            cache.set(cache_key, [])
            return []
            
        bookmakers = data['response'][0].get('bookmakers', [])
        cache.set(cache_key, bookmakers)
        return bookmakers
    except Exception as e:
        print(f"Erro ao buscar odds brutas para fixture {fixture_id}: {e}")
        return []

def get_match_winner_odds(fixture_id):
    bookmakers = get_raw_odds(fixture_id)
    if not bookmakers:
        return None
    markets = bookmakers[0].get('bets', [])
    for m in markets:
        if m['name'] == 'Match Winner' or m['id'] == 1:
            for val in m['values']:
                if val['value'] == 'Home':
                    return float(val['odd'])
    return None

def get_over25_odds(fixture_id):
    bookmakers = get_raw_odds(fixture_id)
    if not bookmakers:
        return None
    markets = bookmakers[0].get('bets', [])
    for m in markets:
        if m['name'] == 'Goals Over/Under' or m['id'] == 5:
            for val in m['values']:
                if val['value'] == 'Over 2.5':
                    return float(val['odd'])
    return None

def get_odds(fixture_id, target_score):

    url = f"{config.BASE_URL}/odds?fixture={fixture_id}&bookmaker=8" # 8 = Bet365
    try:
        response = requests.get(url, headers=get_headers())
        data = response.json()
        if not data.get('response'):
            return None
            
        bookmakers = data['response'][0].get('bookmakers', [])
        if not bookmakers:
            return None
            
        markets = bookmakers[0].get('bets', [])
        for m in markets:
            if m['name'] == 'Exact Score' or m['id'] == 10:
                for val in m['values']:
                    if val['value'] == target_score:
                        return float(val['odd'])
        return None
    except Exception as e:
        print(f"Erro ao buscar odds para fixture {fixture_id}: {e}")
        return None

def get_fixture_injuries(fixture_id):
    cache_key = f"injuries_{fixture_id}"
    cached = cache.get(cache_key, ttl_seconds=86400)
    if cached is not None:
        return cached

    url = f"{config.BASE_URL}/injuries?fixture={fixture_id}"
    try:
        response = requests.get(url, headers=get_headers())
        data = response.json()
        result = data.get('response', [])
        cache.set(cache_key, result)
        return result
    except Exception as e:
        print(f"Erro ao buscar lesoes para fixture {fixture_id}: {e}")
        return []

def get_fixture_lineups(fixture_id):
    cache_key = f"lineups_{fixture_id}"
    cached = cache.get(cache_key, ttl_seconds=86400)
    if cached is not None:
        return cached

    url = f"{config.BASE_URL}/fixtures/lineups?fixture={fixture_id}"
    try:
        response = requests.get(url, headers=get_headers())
        data = response.json()
        result = data.get('response', [])
        cache.set(cache_key, result)
        return result
    except Exception as e:
        print(f"Erro ao buscar lineups para fixture {fixture_id}: {e}")
        return []
