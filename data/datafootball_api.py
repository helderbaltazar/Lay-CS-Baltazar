"""
DataFootball API Client
Fornece fixtures com odds, xG, potenciais e estatísticas de forma consolidada.
"""
import requests
import config
from data import cache
import json

def get_fixtures(date_str):
    cache_key = f"df_fixtures_{date_str}"
    cached = cache.get(cache_key, ttl_seconds=86400)
    if cached is not None:
        return cached

    url = f"{config.DATAFOOTBALL_URL}/matches_day"
    headers = {
        "Authorization": f"Bearer {config.DATAFOOTBALL_TOKEN}"
    }
    params = {
        "date": date_str
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list) and data:
            cache.set(cache_key, data)
            return data
    except Exception as e:
        print(f"⚠️ Erro ao buscar jogos da DataFootball para {date_str}: {e}")
    return []
