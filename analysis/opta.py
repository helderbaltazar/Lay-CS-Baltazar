import json
import os
import difflib

OPTA_CACHE_FILE = "data_store/opta_rankings.json"
_opta_cache = None

def get_opta_cache():
    global _opta_cache
    if _opta_cache is not None:
        return _opta_cache
        
    if os.path.exists(OPTA_CACHE_FILE):
        with open(OPTA_CACHE_FILE, 'r', encoding='utf-8') as f:
            _opta_cache = json.load(f)
    else:
        _opta_cache = {}
        
    return _opta_cache

def get_team_opta_data(team_name):
    """
    Retorna {name, rating, global_rank} ou None.
    Faz um fuzzy match para lidar com "Atlético Mineiro" vs "Atletico Mineiro" etc.
    """
    cache = get_opta_cache()
    if not cache:
        return None
        
    # 1. Match Exato
    if team_name in cache:
        return cache[team_name]
        
    # 2. Match Fuzzy com limite de corte 0.8
    # Muitas vezes o time na API está como "Cruzeiro" e na Opta como "Cruzeiro" (bateu)
    # Mas se for "Athletico-PR" e na opta "Athletico Paranaense"
    all_names = list(cache.keys())
    matches = difflib.get_close_matches(team_name, all_names, n=1, cutoff=0.8)
    
    if matches:
        return cache[matches[0]]
        
    # 3. Se ainda nao achou, tenta limpar acentos/sufixos
    import unicodedata
    def clean_name(n):
        n = unicodedata.normalize('NFKD', n).encode('ASCII', 'ignore').decode('utf-8')
        return n.lower().replace('-', ' ').replace('fc', '').strip()
        
    clean_target = clean_name(team_name)
    for opta_name in all_names:
        if clean_name(opta_name) == clean_target:
            return cache[opta_name]
            
    # Fuzzy no nome limpo
    clean_all = {clean_name(k): k for k in all_names}
    clean_matches = difflib.get_close_matches(clean_target, list(clean_all.keys()), n=1, cutoff=0.8)
    if clean_matches:
        real_opta_name = clean_all[clean_matches[0]]
        return cache[real_opta_name]
        
    return None
