"""
Odds API Client (the-odds-api.com) — 3º Provedor de Dados (Fallback).

Free tier: 500 requisições/mês.
Fornece: lista de jogos + odds H2H de múltiplas casas de apostas.
Não fornece: estatísticas de time (gols, form, etc).
"""
import os
import requests
import json
from data import cache
from database.db import SessionLocal
from database.models_db import RawDataLog

ODDS_API_KEY = os.getenv("ODDS_API_KEY", "3f796b8085ae317b656fa37ffef532b1")
BASE_URL = "https://api.the-odds-api.com/v4"

# Mapeamento: sport_key da Odds API → league_id da API-Football
SPORT_KEYS = {
    "soccer_brazil_campeonato": 71,  # Corrigido: Serie A
    "soccer_brazil_serie_b": 72,
    "soccer_brazil_cup": 73,
    "soccer_conmebol_copa_libertadores": 13,
    "soccer_conmebol_copa_sudamericana": 11,
    "soccer_uefa_champs_league": 2,
    "soccer_uefa_europa_league": 3,
    "soccer_uefa_europa_conference_league": 848,
    "soccer_epl": 39,
    "soccer_england_efl_cup": 48, # EFL Cup
    "soccer_england_league1": 40, # League 1
    "soccer_england_league2": 41, # League 2
    "soccer_efl_champ": 42, # Championship
    "soccer_spain_la_liga": 140,
    "soccer_spain_segunda_division": 141,
    "soccer_italy_serie_a": 135,
    "soccer_italy_serie_b": 136,
    "soccer_italy_coppa_italia": 137,
    "soccer_germany_bundesliga": 78,
    "soccer_germany_bundesliga2": 79,
    "soccer_germany_liga3": 80,
    "soccer_france_ligue_one": 61,
    "soccer_france_ligue_two": 62,
    "soccer_portugal_primeira_liga": 94,
    "soccer_netherlands_eredivisie": 88,
    "soccer_belgium_first_div": 144,
    "soccer_turkey_super_league": 203,
    "soccer_greece_super_league": 197,
    "soccer_saudi_arabia_pro_league": 307,
    "soccer_argentina_primera_division": 128,
    "soccer_mexico_ligamx": 262,
    "soccer_usa_mls": 253,
    "soccer_japan_j_league": 98,
    "soccer_korea_kleague1": 292,
    "soccer_china_superleague": 169,
    "soccer_denmark_superliga": 119,
    "soccer_norway_eliteserien": 103,
    "soccer_sweden_allsvenskan": 113,
    "soccer_sweden_superettan": 114
}

# Nomes das ligas para tradução
LEAGUE_NAMES = {
    71: "Brasileirão Série A",
    72: "Brasileirão Série B",
    73: "Copa do Brasil",
    39: "Premier League",
    140: "La Liga",
    135: "Serie A",
    78: "Bundesliga",
    61: "Ligue 1",
    94: "Primeira Liga",
    88: "Eredivisie",
    144: "Jupiler Pro League",
    203: "Super Lig",
    307: "Saudi Pro League",
    128: "Liga Profesional",
    262: "Liga MX",
    253: "MLS",
    2: "Champions League",
    3: "Europa League",
    848: "Conference League",
    13: "Copa Libertadores",
    11: "Copa Sudamericana",
}

def get_events(sport_key, regions="eu", markets="h2h"):
    """Busca eventos (jogos) de um esporte/liga específico com odds."""
    url = f"{BASE_URL}/sports/{sport_key}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": regions,
        "markets": markets,
        "dateFormat": "iso",
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        remaining = resp.headers.get("x-requests-remaining", "?")
        print(f"  [Odds API] {sport_key} → {resp.status_code} (cota restante: {remaining})")
        if resp.status_code == 200:
            data = resp.json()
            
            # LOG PARA BACKTEST (RAW)
            try:
                db = SessionLocal()
                log = RawDataLog(source='Odds-API', endpoint=f'sports/{sport_key}/odds', payload=json.dumps(data))
                db.add(log)
                db.commit()
                db.close()
            except Exception as e:
                print(f"Erro ao salvar RawDataLog (Odds API): {e}")
                
            return data
        return []
    except Exception as e:
        print(f"  [Odds API] Erro ao buscar {sport_key}: {e}")
        return []


def get_h2h_odds(sport_key):
    """Extrai odds H2H (1X2) de todos os jogos de uma liga."""
    events = get_events(sport_key)
    results = []
    for ev in events:
        home = ev.get("home_team", "")
        away = ev.get("away_team", "")
        bookmakers = ev.get("bookmakers", [])
        home_odd = away_odd = draw_odd = None
        if bookmakers:
            # Pega o primeiro bookmaker disponível
            markets = bookmakers[0].get("markets", [])
            for mkt in markets:
                if mkt["key"] == "h2h":
                    for outcome in mkt["outcomes"]:
                        if outcome["name"] == home:
                            home_odd = outcome["price"]
                        elif outcome["name"] == away:
                            away_odd = outcome["price"]
                        elif outcome["name"] == "Draw":
                            draw_odd = outcome["price"]
        results.append({
            "home_team": home,
            "away_team": away,
            "home_odd": home_odd,
            "away_odd": away_odd,
            "draw_odd": draw_odd,
            "commence_time": ev.get("commence_time"),
        })
    return results


def get_fixtures(date_str):
    """
    Busca fixtures de TODAS as ligas configuradas para uma data.
    Traduz para o formato API-Football que o sistema já entende.
    
    A Odds API retorna jogos futuros (não por data), então filtramos
    localmente pela data solicitada.
    """
    cache_key = f"odds_fixtures_{date_str}"
    cached = cache.get(cache_key, ttl_seconds=86400)
    if cached is not None:
        print(f"[Odds API] Lendo jogos de {date_str} do cache...")
        return cached

    print(f"[Odds API] Buscando jogos de {date_str} em {len(SPORT_KEYS)} ligas...")
    all_fixtures = []

    for sport_key, league_id in SPORT_KEYS.items():
        events = get_events(sport_key)
        for ev in events:
            commence = ev.get("commence_time", "")
            # Filtra pela data solicitada (formato ISO: 2026-09-03T...)
            if not commence.startswith(date_str):
                continue

            # Extrai odds H2H do primeiro bookmaker
            home_odd = None
            bookmakers = ev.get("bookmakers", [])
            if bookmakers:
                markets = bookmakers[0].get("markets", [])
                for mkt in markets:
                    if mkt["key"] == "h2h":
                        for outcome in mkt["outcomes"]:
                            if outcome["name"] == ev.get("home_team"):
                                home_odd = outcome["price"]

            # Traduz para o formato API-Football
            fixture = {
                "fixture": {
                    "id": hash(ev["id"]) % 10**8,  # ID numérico sintético
                    "date": commence,
                    "status": {"short": "NS"}  # Not Started
                },
                "league": {
                    "id": league_id,
                    "name": LEAGUE_NAMES.get(league_id, ev.get("sport_title", "Unknown"))
                },
                "teams": {
                    "home": {"id": hash(ev["home_team"]) % 10**6, "name": ev["home_team"]},
                    "away": {"id": hash(ev["away_team"]) % 10**6, "name": ev["away_team"]}
                },
                "odds_h2h_home": home_odd  # Bônus: já traz a odd
            }
            all_fixtures.append(fixture)

    if all_fixtures:
        cache.set(cache_key, all_fixtures)
        print(f"[Odds API] ✅ {len(all_fixtures)} jogos encontrados para {date_str}")
    else:
        print(f"[Odds API] Nenhum jogo encontrado para {date_str}")

    return all_fixtures
