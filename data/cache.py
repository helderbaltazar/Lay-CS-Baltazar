import json
import os
import time

CACHE_FILE = "cache/team_stats.json"
TTL_SECONDS = 3 * 24 * 60 * 60  # 3 dias

def _load_cache():
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def _save_cache(data):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, 'w') as f:
        json.dump(data, f)

def get(key):
    data = _load_cache()
    if key in data:
        item = data[key]
        if time.time() - item['timestamp'] < TTL_SECONDS:
            return item['value']
    return None

def set(key, value):
    data = _load_cache()
    data[key] = {
        'value': value,
        'timestamp': time.time()
    }
    _save_cache(data)

def invalidate(key):
    data = _load_cache()
    if key in data:
        del data[key]
        _save_cache(data)
