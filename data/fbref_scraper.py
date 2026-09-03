"""
FBRef Web Scraper - The Ultimate Fallback for Team Stats.
Scrapes standings tables via Pandas read_html when both API-Football 
and Stale DB Cache fail to provide team statistics.
"""
import pandas as pd
import requests
import time
from difflib import get_close_matches

# Mapeamento dos IDs da API-Football para os links das competições no FBRef
# Focado nas principais ligas inicialmente.
FBREF_URLS = {
    71: "https://fbref.com/en/comps/24/Serie-A-Stats", # BR Serie A
    39: "https://fbref.com/en/comps/9/Premier-League-Stats", # EPL
    140: "https://fbref.com/en/comps/12/La-Liga-Stats", # La Liga
    135: "https://fbref.com/en/comps/11/Serie-A-Stats", # Serie A (Italy)
    78: "https://fbref.com/en/comps/20/Bundesliga-Stats", # Bundesliga
    61: "https://fbref.com/en/comps/13/Ligue-1-Stats", # Ligue 1
    94: "https://fbref.com/en/comps/32/Primeira-Liga-Stats", # Portugal
}

def fetch_fbref_standings(league_id):
    """Extrai a tabela de classificação geral de uma liga no FBRef."""
    if league_id not in FBREF_URLS:
        return None
        
    url = FBREF_URLS[league_id]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LayCS-Scraper"
    }
    
    try:
        # Rate limit compliance (FBRef is strict)
        time.sleep(3.1)
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        
        # Pega as tabelas da página. Geralmente a primeira (index 0) é a classificação regular
        tables = pd.read_html(resp.text)
        if not tables:
            return None
            
        df = tables[0]
        # Garantir que as colunas necessárias existem ('Squad', 'MP', 'GF', 'GA')
        if 'Squad' not in df.columns or 'MP' not in df.columns:
            return None
            
        return df
    except Exception as e:
        print(f"Erro ao raspar FBRef para liga {league_id}: {e}")
        return None

def get_team_stats_fallback(team_name, league_id):
    """
    Busca estatísticas do time na tabela do FBRef e converte para
    o formato esperado pelo DataManager (mesmo formato da API-Football).
    """
    df = fetch_fbref_standings(league_id)
    if df is None:
        return None
        
    # Limpar nomes dos times da tabela (tira caracteres extras, espaços, etc)
    squad_names = df['Squad'].astype(str).tolist()
    
    # Fuzzy matching do nome do time vindo da API contra a tabela do FBRef
    matches = get_close_matches(team_name, squad_names, n=1, cutoff=0.5)
    
    if not matches:
        print(f"Time '{team_name}' não encontrado na tabela do FBRef.")
        return None
        
    matched_name = matches[0]
    row = df[df['Squad'] == matched_name].iloc[0]
    
    # Extração de dados da tabela (MP = Matches Played, GF = Goals For, GA = Goals Against)
    # Como o FBRef (tabela principal) só dá o total, assumimos home/away dividido por 2
    mp = int(row.get('MP', 1))
    gf = int(row.get('GF', 1))
    ga = int(row.get('GA', 1))
    
    # Derivando estatísticas estimadas para home/away
    half_mp = max(1, mp // 2)
    half_gf = gf / 2.0
    half_ga = ga / 2.0
    
    # Construindo o dicionário no formato esperado
    stats = {
        "fixtures": {
            "played": {
                "home": half_mp,
                "away": half_mp,
                "total": mp
            }
        },
        "goals": {
            "for": {
                "total": {
                    "home": half_gf,
                    "away": half_gf
                }
            },
            "against": {
                "total": {
                    "home": half_ga,
                    "away": half_ga
                }
            }
        },
        "failed_to_score": {
            "home": 0,  # Dados difíceis de obter apenas com a tabela básica
            "away": 0
        },
        "form": "DDDDD"  # Neutral form since we don't scrape the match logs
    }
    
    print(f"✅ FBRef Fallback aplicado com sucesso para {team_name} ({matched_name})!")
    return stats
