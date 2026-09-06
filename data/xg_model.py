from data.understat_scraper import fetch_understat_xg, LEAGUE_MAPPING
from data.data_manager import DataManager

# Cache in memory
_UNDERSTAT_CACHE = {}

def get_team_xg(team_id, league_id, team_name, season=None):
    """
    Retorna o xG e xGA médio por jogo de um time.
    Tenta Understat (Padrão Ouro). Se não suportado, usa xG Sintético.
    Retorna: {"xG_home": float, "xGA_home": float, "xG_away": float, "xGA_away": float}
    """
    if not season:
        season = "2024" # Default for now
        
    import sys
    is_test = 'pytest' in sys.modules

    # 1. Tentativa Understat
    if league_id in LEAGUE_MAPPING and not is_test:
        cache_key = f"{league_id}_{season}"
        if cache_key not in _UNDERSTAT_CACHE:
            print(f"🔄 Baixando xG do Understat para liga {league_id}...")
            _UNDERSTAT_CACHE[cache_key] = fetch_understat_xg(league_id, season)
            
        league_data = _UNDERSTAT_CACHE.get(cache_key)
        if league_data:
            # Fuzzy match team_name with Understat keys
            from difflib import get_close_matches
            matches = get_close_matches(team_name, league_data.keys(), n=1, cutoff=0.6)
            if matches:
                matched_team = matches[0]
                td = league_data[matched_team]
                return {
                    "xG_home": td.get("xG_home_avg", 1.0),
                    "xGA_home": td.get("xGA_home_avg", 1.0),
                    "xG_away": td.get("xG_away_avg", 1.0),
                    "xGA_away": td.get("xGA_away_avg", 1.0)
                }

    # 2. Fallback: xG Sintético (Regressão Heurística)
    # Usa os gols reais, penalizando se o time falha muito em marcar (failed_to_score)
    # e bonificando a defesa baseada em clean_sheets.
    stats = DataManager.get_team_stats(team_id, league_id, team_name=team_name)
    if not stats:
        return {"xG_home": 1.0, "xGA_home": 1.0, "xG_away": 1.0, "xGA_away": 1.0}
        
    try:
        mp_home = stats['fixtures']['played']['home'] or 1
        mp_away = stats['fixtures']['played']['away'] or 1
        
        gf_home = stats['goals']['for']['total']['home'] or 0
        gf_away = stats['goals']['for']['total']['away'] or 0
        
        ga_home = stats['goals']['against']['total']['home'] or 0
        ga_away = stats['goals']['against']['total']['away'] or 0
        
        # Penaliza ataque baseado em 'failed_to_score' (FT)
        # Se um time marca 20 gols em 10 jogos, mas falhou em marcar em 5 (fez 20 em 5 jogos),
        # ele é volátil. Seu xG deve ser menor que 2.0.
        ft_home = stats.get('failed_to_score', {}).get('home', 0)
        ft_away = stats.get('failed_to_score', {}).get('away', 0)
        
        # Bonifica defesa baseada em 'clean_sheet' (CS)
        cs_home = stats.get('clean_sheet', {}).get('home', 0)
        cs_away = stats.get('clean_sheet', {}).get('away', 0)
        
        # Fator de correção de ataque: 1.0 - (0.5 * taxa de falha)
        att_corr_home = 1.0 - (0.5 * (ft_home / mp_home)) if mp_home else 1.0
        att_corr_away = 1.0 - (0.5 * (ft_away / mp_away)) if mp_away else 1.0
        
        # Fator de correção de defesa: 1.0 - (0.5 * taxa de clean sheet)
        def_corr_home = 1.0 - (0.5 * (cs_home / mp_home)) if mp_home else 1.0
        def_corr_away = 1.0 - (0.5 * (cs_away / mp_away)) if mp_away else 1.0

        xg_home = (gf_home / mp_home) * att_corr_home
        xga_home = (ga_home / mp_home) * def_corr_home
        
        xg_away = (gf_away / mp_away) * att_corr_away
        xga_away = (ga_away / mp_away) * def_corr_away
        
        return {
            "xG_home": max(0.1, xg_home),
            "xGA_home": max(0.1, xga_home),
            "xG_away": max(0.1, xg_away),
            "xGA_away": max(0.1, xga_away)
        }
    except Exception as e:
        print(f"Erro ao calcular xG Sintético para {team_name}: {e}")
        return {"xG_home": 1.0, "xGA_home": 1.0, "xG_away": 1.0, "xGA_away": 1.0}

