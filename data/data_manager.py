import config

class DataManager:
    """
    Orchestrates data sources.
    As per the latest system rules, DataFootball is the exclusive data source.
    """
    @staticmethod
    def get_fixtures(date_str):
        # 1. Buscar do DataFootball (Única API Principal)
        from data.datafootball_api import get_fixtures as df_get_fixtures
        df_fixtures = df_get_fixtures(date_str)
        if df_fixtures:
            return df_fixtures, "DataFootball"
            
        print(f"⚠️ DataFootball retornou vazio para {date_str}. Ignorando dia.")
        return [], None
        
    @staticmethod
    def get_team_stats(team_id, league_id, source="DataFootball", team_name=None):
        """
        O DataFootball provê todas as estatísticas no payload de fixtures (xG, PPG).
        Este método é mantido apenas por retrocompatibilidade para não quebrar testes legados.
        Como as outras APIs foram proibidas, retorna sempre None.
        """
        return None

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

    @staticmethod
    def calculate_synthetic_xga(goals_conceded, matches_played, clean_sheets, league_avg_goals):
        if matches_played == 0:
            return league_avg_goals
            
        raw_avg = goals_conceded / matches_played
        matches_with_goals_conceded = matches_played - clean_sheets
        consistency = matches_with_goals_conceded / matches_played
        
        # Penaliza times que tomam gols em quase todos os jogos (aumenta o xGA)
        multiplier = (consistency + 1) / 2
        xga_bruto = raw_avg * multiplier
        
        sxga = (xga_bruto * 0.85) + (league_avg_goals * 0.15)
        return sxga
