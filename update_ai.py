import os

with open('analysis/ai_analyst.py', 'r') as f:
    content = f.read()

# I need to replace get_deep_match_analysis definition.
old_def = """    @classmethod
    def get_deep_match_analysis(cls, home_team: str, away_team: str, league: str) -> dict:
        import os, config, requests, re, json
        import logging
        logger = logging.getLogger(__name__)
        gemini_key = getattr(config, 'GEMINI_API_KEY', '') or os.getenv('GEMINI_API_KEY', '')
        if not gemini_key:
            return {'momentos_gols': 'Indisponível', 'placares_perigosos': 'Indisponível', 'motivacao': 'Indisponível', 'lesoes': 'Indisponível', 'analise_geral': 'IA offline'}
        prompt = f'''Você é um analista especialista em Lay Correct Score. Analise a partida {home_team} x {away_team} pela liga {league}.
Responda APENAS com JSON:
{{
  "momentos_gols": "minutos...",
  "placares_perigosos": "placares...",
  "motivacao": "motivacao...",
  "lesoes": "lesoes...",
  "analise_geral": "resumo..."
}}'''"""

new_def = """    @classmethod
    def get_deep_match_analysis(cls, home_team: str, away_team: str, league: str, fixture_id: int = None) -> dict:
        import os, config, requests, re, json
        import logging
        from data import api_football
        
        logger = logging.getLogger(__name__)
        gemini_key = getattr(config, 'GEMINI_API_KEY', '') or os.getenv('GEMINI_API_KEY', '')
        if not gemini_key:
            return {'momentos_gols': 'Indisponível', 'placares_perigosos': 'Indisponível', 'motivacao': 'Indisponível', 'lesoes': 'Indisponível', 'analise_geral': 'IA offline'}
            
        injuries_text = "Nenhuma informação de lesão disponível em tempo real."
        lineups_text = "Nenhuma escalação disponível em tempo real."
        
        if fixture_id:
            try:
                injuries = api_football.get_fixture_injuries(fixture_id)
                if injuries:
                    inj_list = [f"{i.get('player',{}).get('name')} ({i.get('type')})" for i in injuries]
                    injuries_text = ", ".join(inj_list)
                    
                lineups = api_football.get_fixture_lineups(fixture_id)
                if lineups:
                    lin_list = [f"{l.get('team',{}).get('name')}: {l.get('formation')}" for l in lineups]
                    lineups_text = ", ".join(lin_list)
            except Exception as e:
                logger.error(f"Erro ao buscar dados reais para IA: {e}")

        prompt = f'''Você é um analista especialista em Lay Correct Score. Analise a partida {home_team} x {away_team} pela liga {league}.
        
DADOS EM TEMPO REAL RECEBIDOS DA API OFICIAL:
Lesões Confirmadas: {injuries_text}
Escalações/Formações: {lineups_text}

Considere ABSOLUTAMENTE esses dados reais acima para dar o seu parecer sobre lesões e motivação.

Responda APENAS com JSON:
{{
  "momentos_gols": "minutos...",
  "placares_perigosos": "placares...",
  "motivacao": "motivacao...",
  "lesoes": "lesoes...",
  "analise_geral": "resumo..."
}}'''"""

if old_def in content:
    content = content.replace(old_def, new_def)
    with open('analysis/ai_analyst.py', 'w') as f:
        f.write(content)
    print("Atualizado com sucesso!")
else:
    print("OLD DEF NOT FOUND!")
