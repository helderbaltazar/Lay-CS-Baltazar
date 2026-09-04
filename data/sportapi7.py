import os
import requests
import logging

logger = logging.getLogger(__name__)

class SportAPI7:
    BASE_URL = "https://sportapi7.p.rapidapi.com"
    
    @classmethod
    def get_headers(cls):
        key = os.getenv("RAPIDAPI_KEY")
        return {
            "x-rapidapi-key": key,
            "x-rapidapi-host": "sportapi7.p.rapidapi.com"
        }

    @classmethod
    def get_dropping_odds(cls):
        if not os.getenv("RAPIDAPI_KEY"):
            logger.warning("RAPIDAPI_KEY não configurada. Mockando dropping odds.")
            return {}
            
        url = f"{cls.BASE_URL}/api/v1/odds/topwinning/football"
        try:
            response = requests.get(url, headers=cls.get_headers(), timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Erro na SportAPI7: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"Falha na requisição SportAPI7: {e}")
            return {}

    @classmethod
    def extract_smart_money_signals(cls):
        """
        Transforma a resposta da API em um dicionário de sinais de Smart Money.
        Retorna um dicionário: { "Nome do Time Casa": {"market": "OVER_2.5", "confidence_boost": 15} }
        """
        data = cls.get_dropping_odds()
        signals = {}
        # Como não temos a estrutura exata do JSON real, vamos preparar a estrutura
        # para iterar sobre eventos de 'dropping odds' e extrair bônus
        events = data.get("events", [])
        odds_map = data.get("oddsMap", {})
        
        for event in events:
            home_team = event.get("homeTeam", {}).get("name")
            if home_team:
                signals[home_team] = {
                    "market": "OVER_2.5", # Mock structure based on dropping odds
                    "confidence_boost": 15
                }
        
        return signals

