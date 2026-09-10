import json
import logging
import re
import os
import requests
import config

logger = logging.getLogger(__name__)

class AIAnalyst:
    """
    IA Especialista em Lay Correct Score (Lay 0x1, Lay 0x2, Lay 0x3, Lay 1x3).
    Audita as melhores oportunidades do ranking estatístico combinando
    dados quantitativos (Poisson + SxG) com análise qualitativa e RAG contextual.
    """

    @classmethod
    def build_prompt(cls, match_info: dict, target_score: str, prob_poisson: float) -> str:
        home_team = match_info.get('home', 'Mandante')
        away_team = match_info.get('away', 'Visitante')
        league = match_info.get('league', 'Liga')
        lam_home = match_info.get('lambda_home', 1.0)
        lam_away = match_info.get('lambda_away', 1.0)
        market_odd = match_info.get('match_odd', 'N/A')
        ai_boost = match_info.get('ai_confidence_boost', 0)
        prob_pct = round(prob_poisson * 100, 2)
        
        from analysis.opta import get_team_opta_data
        h_opta = get_team_opta_data(home_team)
        a_opta = get_team_opta_data(away_team)
        
        opta_str = ""
        if h_opta and a_opta:
            opta_str = f"\n[Opta Power Rankings Globais]\n- {home_team}: Rating {h_opta['rating']:.1f} (Rank Global: {h_opta['global_rank']} | Rank Doméstico: {h_opta.get('domestic_rank', '?')} na {h_opta.get('league', '?')})\n- {away_team}: Rating {a_opta['rating']:.1f} (Rank Global: {a_opta['global_rank']} | Rank Doméstico: {a_opta.get('domestic_rank', '?')} na {a_opta.get('league', '?')})\n-> Dica Opta: Quanto maior o rating (0-100), mais forte e favorita é a equipe. Use o Rating absoluto para comparar a força real entre eles, independente do continente.\n"
        
        is_lay_cs = target_score in ["0-1", "0-2", "0-3", "1-3"]
        
        if is_lay_cs:
            target_display = "Lay " + target_score.replace('-', 'x')
            role = "especialista em apostas esportivas de Lay Correct Score (apostar CONTRA um placar exato)"
            rules = f"""DIRETRIZES DE ESPECIALISTA EM LAY CS:
1. Lay 0x1 / Lay 0x2: Avalie se o mandante tem capacidade de marcar ao menos 1 gol ou segurar o jogo.
2. Lay 0x3 / Lay 1x3: Avalie se a partida tem baixa tendência de goleada do visitante.
3. Grau de Confiança base: ~{100 - prob_pct:.1f}%. Refine para cima ou para baixo de acordo com odd ({market_odd}), mando de campo e momento.
4. Fatores de Veto: Se o risco do visitante vencer pelo exato placar de {target_score.replace('-', 'x')} for alto, você deve VETAR."""
        else:
            target_display = target_score
            role = "especialista quantitativo em apostas esportivas (Mercados de Over/Under/Match Odds)"
            rules = f"""DIRETRIZES DE ESPECIALISTA EM {target_score}:
1. Você deve analisar a viabilidade do mercado {target_score} baseado na força de ataque/defesa de ambos.
2. Grau de Confiança base: ~{prob_pct:.1f}%. Refine considerando se as Odds (ex: {market_odd}) e as tendências de mercado indicam valor real.
3. Considere que a matemática indicou {prob_pct}% de chance de ocorrência. Analise friamente as estatísticas (λ={lam_home:.2f} vs λ={lam_away:.2f}).
4. Veto: Vete a aposta caso os lambdas e a cotação não justifiquem a entrada."""

        return f"""Você é um analista quantitativo e {role}.

PARTIDA PARA AUDITORIA:
- Jogo: {home_team} vs {away_team}
- Competição: {league}
- Mercado: {target_display} (Probabilidade estimada: {prob_pct}%)
- Força de Ataque (λ): Mandante (λ={lam_home:.2f}), Visitante (λ={lam_away:.2f})
- Match Odd Mandante (1x2): {market_odd}
- Smart Money Boost (Decaimento das Odds): +{ai_boost}%{opta_str}

{rules}

Responda ESTRITAMENTE em formato JSON com esta estrutura:
{{
  "veredito": "APROVADO" ou "VETADO",
  "confianca": <inteiro de 10 a 99 representando a segurança final na entrada>,
  "fator_critico": "<frase curta de até 120 caracteres resumindo o principal motivo do veredito>",
  "analise_detalhada": "<parágrafo explicativo de 2 a 4 frases para exibição no Dashboard justificando a escolha baseada nos dados fornecidos>"
}}
"""

    @classmethod
    def analyze_match(cls, match_info: dict, target_score: str, prob_poisson: float) -> dict:
        """
        Analisa uma partida individualmente.
        Tenta chamar a API do Gemini com fallback gracioso.
        """
        if not getattr(config, 'AI_ANALYST_ENABLED', True):
            return cls._fallback_analysis(match_info, target_score, prob_poisson, 'IA desativada nas configurações.')

        gemini_key = getattr(config, 'GEMINI_API_KEY', '') or os.getenv('GEMINI_API_KEY', '')
        if not gemini_key:
            return cls._fallback_analysis(match_info, target_score, prob_poisson, 'Análise heurística estatística (chave de IA não configurada).')

        prompt = cls.build_prompt(match_info, target_score, prob_poisson)

        # Cascata de modelos confirmados na API v1beta
        models_to_try = ['gemini-flash-latest', 'gemini-flash-lite-latest']
        
        for model_name in models_to_try:
            try:
                url = f'https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_key}'
                payload = {
                    'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
                    'generationConfig': {
                        'temperature': 0.2,
                        'maxOutputTokens': 600,
                        'response_mime_type': 'application/json'
                    }
                }
                
                headers = {'Content-Type': 'application/json'}
                resp = requests.post(url, headers=headers, json=payload, timeout=12)
                
                if resp.status_code == 200:
                    data = resp.json()
                    text_response = data['candidates'][0]['content']['parts'][0]['text']
                    parsed = cls._parse_ai_json(text_response)
                    if parsed:
                        return parsed
                else:
                    logger.warning(f'[AI Analyst] API Gemini modelo {model_name} ({resp.status_code}): {resp.text[:120]}')
            except Exception as e:
                logger.warning(f'[AI Analyst] Exceção ao consultar Gemini ({model_name}): {e}')

        return cls._fallback_analysis(match_info, target_score, prob_poisson)

    @classmethod
    def _parse_ai_json(cls, text: str) -> dict:
        """Extrai e valida o JSON da resposta da IA."""
        try:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                verdict = str(data.get('veredito', 'APROVADO')).strip().upper()
                if 'VET' in verdict:
                    verdict = 'VETADO'
                else:
                    verdict = 'APROVADO'
                
                confidence = int(data.get('confianca', 80))
                confidence = max(0, min(100, confidence))
                
                critical = str(data.get('fator_critico', '')).strip()
                if not critical:
                    critical = 'Alinhamento estatístico favorável ao Lay.'
                    
                detailed = str(data.get('analise_detalhada', '')).strip()
                if not detailed:
                    detailed = f'Partida auditada com veredito {verdict}. Segurança estimada em {confidence}%.'
                    
                adjustment_factor = float(data.get('fator_ajuste', 1.0))

                return {
                    'verdict': verdict,
                    'confidence': confidence,
                    'critical_factor': critical[:250],
                    'detailed_analysis': detailed,
                    'adjustment_factor': adjustment_factor
                }
        except Exception as e:
            logger.warning(f'[AI Analyst] Falha ao parsear JSON da IA: {e}')
        return None

    @classmethod
    def _fallback_analysis(cls, match_info: dict, target_score: str, prob_poisson: float, custom_reason: str = None) -> dict:
        """
        Gera análise estatística contínua e precisa quando a IA estiver offline ou em limite de cota.
        O grau de confiança no Lay varia proporcionalmente à segurança estatística de cada jogo.
        """
        home_team = match_info.get('home', 'Mandante')
        away_team = match_info.get('away', 'Visitante')
        target_display = target_score.replace('-', 'x')
        prob_pct = prob_poisson * 100
        
        # Confiança matemática exata no Lay = probabilidade de NÃO ocorrer o placar
        calculated_conf = round(100.0 - prob_pct, 1)
        calculated_conf_int = int(round(calculated_conf))
        confidence = max(10, min(99, calculated_conf_int))

        # Crivo de segurança: Se a probabilidade do placar for <= 12% (Confiança >= 88%), é Aprovado
        if prob_pct <= 12.0:
            verdict = 'APROVADO'
            critical = custom_reason or f'Risco de apenas {prob_pct:.1f}% para {target_display} (Segurança de {calculated_conf:.1f}% no Lay).'
            detailed = (
                f'O modelo estatístico Poisson + Dixon-Coles indica {calculated_conf:.1f}% de probabilidade do placar {target_display} NÃO ocorrer. '
                f'Mandante ({home_team}) com métricas favoráveis para anular o placar {target_display} contra {away_team}.'
            )
        else:
            verdict = 'VETADO'
            critical = f'Probabilidade de {target_display} ({prob_pct:.1f}%) acima do limite seguro para Lay.'
            detailed = (
                f'Partida vetada pelo crivo de segurança: o placar exato {target_display} possui {prob_pct:.1f}% de chance calculada, '
                f'resultando em confiança de {calculated_conf:.1f}%, abaixo do patamar mínimo de 88% para Lay CS.'
            )

        return {
            'verdict': verdict,
            'confidence': confidence,
            'critical_factor': critical[:250],
            'detailed_analysis': detailed,
            'adjustment_factor': 1.0
        }


    @classmethod
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
}}'''
        for model in ['gemini-flash-latest', 'gemini-flash-lite-latest']:
            try:
                url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}'
                payload = {'contents': [{'role': 'user', 'parts': [{'text': prompt}]}], 'generationConfig': {'temperature': 0.3}}
                resp = requests.post(url, headers={'Content-Type': 'application/json'}, json=payload, timeout=12)
                if resp.status_code == 200:
                    text_response = resp.json()['candidates'][0]['content']['parts'][0]['text']
                    match = re.search(r'\{.*\}', text_response, re.DOTALL)
                    if match:
                        return json.loads(match.group(0))
            except:
                pass
        return {'momentos_gols': 'Erro', 'placares_perigosos': 'Erro', 'motivacao': 'Erro', 'lesoes': 'Erro', 'analise_geral': 'Erro ao consultar IA'}

    @classmethod
    def analyze_top_rankings(cls, rankings: dict, top_n: int = None) -> dict:
        """
        Audita os top N jogos de cada target score nos rankings gerados pelo scanner.
        Enriquece cada item com os campos da IA.
        """
        if top_n is None:
            top_n = getattr(config, 'AI_ANALYST_TOP_N', 10)

        for target_score, matches in rankings.items():
            for i, match in enumerate(matches):
                prob = match.get('probability', 0.10)
                if i < top_n:
                    analysis = cls.analyze_match(match, target_score, prob)
                    match['ai_verdict'] = analysis['verdict']
                    match['ai_confidence'] = analysis['confidence']
                    match['ai_critical_factor'] = analysis['critical_factor']
                    match['ai_analysis'] = analysis['detailed_analysis']
                    match['ai_adjustment_factor'] = analysis.get('adjustment_factor', 1.0)
                else:
                    fallback = cls._fallback_analysis(match, target_score, prob, 'Fora do Top 10 prioritário.')
                    match['ai_verdict'] = fallback['verdict']
                    match['ai_confidence'] = fallback['confidence']
                    match['ai_critical_factor'] = fallback['critical_factor']
                    match['ai_analysis'] = fallback['detailed_analysis']
                    match['ai_adjustment_factor'] = fallback.get('adjustment_factor', 1.0)

        return rankings
