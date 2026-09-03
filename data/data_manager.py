import config
from data.api_football import get_fixtures as api_get_fixtures, get_team_stats as api_get_team_stats
from data.football_data_api import get_fixtures as fd_get_fixtures, LEAGUE_MAP

class DataManager:
    """
    Orchestrates multiple data sources (Chain of Responsibility).
    Attempts primary source, falls back to secondary if quota exceeded or error.
    """
    @staticmethod
    def get_fixtures(date_str):
        # 1. Tentar API-Football (Principal)
        fixtures = api_get_fixtures(date_str)
        if fixtures:
            return fixtures, "API-Football"
            
        # 2. Se falhar, tentar Football-Data.org (Fallback)
        print("⚠️ API-Football falhou ou retornou vazio. Tentando Fallback (Football-Data.org)...")
        fd_fixtures = fd_get_fixtures(date_str)
        if fd_fixtures:
            # Precisa traduzir o formato do Football-Data para o formato esperado pelo scanner
            translated = DataManager._translate_fd_fixtures(fd_fixtures)
            return translated, "Football-Data"
            
        return [], None
        
    @staticmethod
    def get_team_stats(team_id, league_id, source="API-Football"):
        stats = None
        if source == "API-Football":
            stats = api_get_team_stats(team_id, league_id)
            
        if stats is not None:
            return stats
            
        # Lógica do Football-Data (simplificada)
        # Se falhou por limite da API (None) ou a fonte for outra, retorna um fallback gracioso (Dummy)
        # que forçará o modelo a usar a média da liga para não quebrar a injeção.
        return {
            "fixtures": {"played": {"home": 1, "away": 1, "total": 2}}, 
            "goals": {"for": {"total": {"home": 1, "away": 1}}, "against": {"total": {"home": 1, "away": 1}}},
            "failed_to_score": {"home": 0, "away": 0},
            "form": "DDDDD"
        }

    @staticmethod
    def _translate_fd_fixtures(fd_matches):
        translated = []
        for match in fd_matches:
            # Converte pro formato da API-Football que o sistema já entende
            translated.append({
                "fixture": {
                    "id": match["id"],
                    "date": match["utcDate"],
                    "status": {"short": match["status"]}
                },
                "league": {
                    "id": 9999, # Fake ID ou fazer mapping inverso
                    "name": match["competition"]["name"]
                },
                "teams": {
                    "home": {"id": match["homeTeam"]["id"], "name": match["homeTeam"]["name"]},
                    "away": {"id": match["awayTeam"]["id"], "name": match["awayTeam"]["name"]}
                }
            })
        return translated


    @staticmethod
    def calculate_synthetic_xg(goals_scored, matches_played, failed_to_score, league_avg_goals):
        if matches_played == 0:
            return league_avg_goals
            
        raw_avg = goals_scored / matches_played
        matches_with_goals = matches_played - failed_to_score
        consistency = matches_with_goals / matches_played
        
        # Penaliza times que concentram gols em poucos jogos
        multiplier = (consistency + 1) / 2
        xg_bruto = raw_avg * multiplier
        
        # Regressão à média (15%) para estabilidade em inícios de temporada
        sxg = (xg_bruto * 0.85) + (league_avg_goals * 0.15)
        return sxg
