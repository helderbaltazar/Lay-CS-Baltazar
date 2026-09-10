def get_injury_report(team: str) -> dict:
    """
    Retorna o relatorio de lesoes para um time especifico.
    Args:
        team: Nome do time.
    """
    # Mock data for now
    return {
        "team": team,
        "key_players_injured": False,
        "details": "Nenhum desfalque critico."
    }

def get_weather_condition(stadium: str) -> dict:
    """
    Retorna as condicoes climaticas de um estadio.
    Args:
        stadium: Nome do estadio ou cidade.
    """
    # Mock data for now
    return {
        "stadium": stadium,
        "condition": "Clear",
        "rain_probability_percent": 10
    }
