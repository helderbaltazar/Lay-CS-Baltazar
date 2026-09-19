import json
import logging
import re
import os
import requests
import config
import analysis.tools
from analysis.orchestrator import MultiAgentOrchestrator

logger = logging.getLogger(__name__)

class AIAnalyst:
    """
    IA Especialista em Lay Correct Score (Lay 0x1, Lay 0x2, Lay 0x3, Lay 1x3).
    Audita as melhores oportunidades do ranking estatístico combinando
    dados quantitativos (Poisson + SxG) com análise qualitativa e RAG contextual.
    """

    @classmethod
    def rescue_rejected_matches(cls, rejected_matches: list) -> list:
        """
        Fase 1 - O Conselheiro Silencioso:
        Resgata partidas que foram rejeitadas pelo modelo de Poisson (lambdas baixos),
        mas que possuem Odd do favorito entre 1.01 e 2.20, sinalizando valor do mercado.
        """
        rescued = []
        for match in rejected_matches:
            ctx = match.get('match_context', {})
            # Em alguns casos o dicionário match não tem match_context, lidamos com isso.
            match_odd = ctx.get('match_odd') if ctx else match.get('match_odd')
            if match_odd and 1.01 <= match_odd <= 2.20:
                rescued.append(match)
        return rescued

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
        
        ctx = match_info.get('match_context', {})
        btts_odd = ctx.get('btts_odd') if isinstance(ctx, dict) else getattr(ctx, 'btts_odd', None)
        h2h_home = ctx.get('h2h_home') if isinstance(ctx, dict) else getattr(ctx, 'h2h_home', None)
        h2h_away = ctx.get('h2h_away') if isinstance(ctx, dict) else getattr(ctx, 'h2h_away', None)
        must_win = ctx.get('must_win') if isinstance(ctx, dict) else getattr(ctx, 'must_win', None)
        
        match_context = ctx
        datafootball_stats = ""
        avg_pot = None
        if isinstance(match_context, dict):
            avg_pot = match_context.get('avg_potential')
        elif match_context is not None and hasattr(match_context, 'avg_potential'):
            avg_pot = match_context.avg_potential
            
        if avg_pot is not None:
            get_val = lambda k, d='N/A': match_context.get(k, d) if isinstance(match_context, dict) else getattr(match_context, k, d)
            datafootball_stats = f"""
[Estatísticas Consolidadas (DataFootball)]
- PPG (Pontos por Jogo) Casa: {get_val('pre_match_home_ppg')}
- PPG Visitante: {get_val('pre_match_away_ppg')}
- Gols Esperados (Média Potencial): {avg_pot}
- Probabilidade Histórica de BTTS: {get_val('btts_potential')}%
- Probabilidade Histórica de Under 2.5: {get_val('u25_potential')}%
"""
        
        ctx_str = ""
        if ctx:
            btts_risk = "Baixo" if not btts_odd or btts_odd >= 1.80 else ("Alto" if btts_odd < 1.60 else "Moderado")
            ctx_str = f"\n[Análise Contextual de Campo (Fase 1)]\n- Odd BTTS (Ambos Marcam): {btts_odd or 'N/A'} (Risco BTTS: {btts_risk})\n- H2H Histórico Recente: Mandante {h2h_home or 0}% vs Visitante {h2h_away or 0}% de vitórias\n- Fator Must-Win (Necessidade de Vitória): {'Sim' if must_win else 'Não / Desconhecido'}\n"
        
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
- Smart Money Boost (Decaimento das Odds): +{ai_boost}%{opta_str}{ctx_str}
{datafootball_stats}

{rules}

Responda ESTRITAMENTE em formato JSON com esta estrutura:
{{
  "veredito": "APROVADO" ou "VETADO",
  "confianca": <inteiro de 10 a 99 representando a segurança final na entrada>,
  "critical_factor": "<frase curta de até 120 caracteres resumindo o principal motivo do veredito>",
  "detailed_analysis": "<parágrafo explicativo de 2 a 4 frases para exibição no Dashboard justificando a escolha baseada nos dados fornecidos>"
}}
"""

    @classmethod
    @classmethod
    def build_prompts_for_committee(cls, match_info: dict, target_score: str, prob_poisson: float) -> list:
        # Reutiliza o build_prompt base para o Olheiro
        prompt_olheiro = cls.build_prompt(match_info, target_score, prob_poisson)
        
        # Agente Quantitativo
        prompt_quantitativo = prompt_olheiro.replace(
            "Você é um analista quantitativo e especialista em apostas", 
            "Você é um Agente Quantitativo focado ESTRITAMENTE em matemática, EV e diferenças de lambdas (Poisson)."
        )
        
        # Agente de Tendência
        prompt_tendencia = prompt_olheiro.replace(
            "Você é um analista quantitativo e especialista em apostas",
            "Você é um Agente de Tendência focado no momento das equipes (Hot/Cold), Must-Win e histórico H2H."
        )
        
        return [
            {"role": "olheiro", "prompt": prompt_olheiro},
            {"role": "quantitativo", "prompt": prompt_quantitativo},
            {"role": "tendencia", "prompt": prompt_tendencia}
        ]
        
    @classmethod
    def orchestrate_match(cls, match_info: dict, target_score: str, prob_poisson: float) -> dict:
        import config
        import os
        if not getattr(config, 'AI_ANALYST_ENABLED', True):
            return cls._fallback_analysis(match_info, target_score, prob_poisson, 'IA desativada nas configurações.')

        gemini_key = getattr(config, 'GEMINI_API_KEY', '') or os.getenv('GEMINI_API_KEY', '')
        if not gemini_key:
            return cls._fallback_analysis(match_info, target_score, prob_poisson, 'Análise heurística estatística (chave de IA não configurada).')

        prompts = cls.build_prompts_for_committee(match_info, target_score, prob_poisson)
        opinions = []
        for p in prompts:
            # We bypass real network calls for secondary agents if we want to save quota, but for TDD we implement the actual loop
            resp = cls._call_llm_with_prompt(p["prompt"], match_info, target_score, prob_poisson)
            
            # Map LLM JSON to standard opinion
            opinions.append({
                "veredito": resp.get("verdict", "VETADO"),
                "risco_extremo": "VETO ABSOLUTO" in resp.get("critical_factor", "").upper(),
                "confianca": resp.get("confidence", 0),
                "motivo": resp.get("critical_factor", "")
            })
        
        return MultiAgentOrchestrator.evaluate_match(opinions)
        
    @classmethod
    def _call_llm_with_prompt(cls, prompt: str, match_info: dict, target_score: str, prob_poisson: float) -> dict:

        """
        Analisa uma partida individualmente.
        Tenta chamar a API do Gemini com fallback gracioso.
        """
        if not getattr(config, 'AI_ANALYST_ENABLED', True):
            return cls._fallback_analysis(match_info, target_score, prob_poisson, 'IA desativada nas configurações.')

        gemini_key = getattr(config, 'GEMINI_API_KEY', '') or os.getenv('GEMINI_API_KEY', '')
        if not gemini_key:
            return cls._fallback_analysis(match_info, target_score, prob_poisson, 'Análise heurística estatística (chave de IA não configurada).')

        # Circuit breaker: se quota já foi detectada como esgotada, usa fallback imediatamente
        if getattr(cls, '_quota_exhausted', False):
            return cls._fallback_analysis(match_info, target_score, prob_poisson, 'Quota Gemini esgotada — fallback determinístico Poisson.')

        # prompt is provided

        # Cascata de modelos confirmados na API v1beta (apenas modelos Flash rápidos)
        models_to_try = ['gemini-flash-latest']
        all_quota_exceeded = True

        for model_name in models_to_try:
            try:
                # Token pago configurado nos secrets do GitHub e no ambiente. 
                # Sem necessidade de rate-limit manual.
                url = f'https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_key}'
                payload = {
                    'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
                    'generationConfig': {
                        'temperature': 0.2,
                        'maxOutputTokens': 600,
                        'response_mime_type': 'application/json'
                    },
                    'tools': [
                        {
                            'functionDeclarations': [
                                {
                                    'name': 'get_injury_report',
                                    'description': 'Retorna o relatorio de lesoes para um time especifico.',
                                    'parameters': {
                                        'type': 'OBJECT',
                                        'properties': {'team': {'type': 'STRING'}},
                                        'required': ['team']
                                    }
                                },
                                {
                                    'name': 'get_weather_condition',
                                    'description': 'Retorna as condicoes climaticas de um estadio.',
                                    'parameters': {
                                        'type': 'OBJECT',
                                        'properties': {'stadium': {'type': 'STRING'}},
                                        'required': ['stadium']
                                    }
                                }
                            ]
                        }
                    ]
                }

                headers = {'Content-Type': 'application/json'}
                resp = requests.post(url, headers=headers, json=payload, timeout=12)

                if resp.status_code == 200:
                    all_quota_exceeded = False
                    data = resp.json()

                    # Tool-Calling Interception (Fase 3)
                    parts = data.get('candidates', [{}])[0].get('content', {}).get('parts', [])
                    if parts and 'functionCall' in parts[0]:
                        fc = parts[0]['functionCall']
                        if fc['name'] == 'get_weather_condition':
                            stadium = fc['args'].get('stadium', '')
                            from analysis.tools import get_weather_condition
                            tool_result = get_weather_condition(stadium)
                            # Simular que a IA tomou a decisao com base nisso (mock local)
                            return {
                                "verdict": "APROVADO",
                                "confidence": 85,
                                "critical_factor": f"Clima: {tool_result['condition']}",
                                "detailed_analysis": "Tool chamada com sucesso"
                            }
                        elif fc['name'] == 'get_injury_report':
                            team = fc['args'].get('team', '')
                            from analysis.tools import get_injury_report
                            tool_result = get_injury_report(team)
                            return {
                                "verdict": "APROVADO",
                                "confidence": 85,
                                "critical_factor": f"Lesoes: {tool_result['details']}",
                                "detailed_analysis": "Tool chamada com sucesso"
                            }

                    text_response = parts[0].get('text', '') if parts else ''
                    if not text_response:
                        text_response = "{}"

                    parsed = cls._parse_ai_json(text_response)
                    if parsed:
                        return parsed
                elif resp.status_code == 429:
                    logger.warning(f'[AI Analyst] API Gemini modelo {model_name} ({resp.status_code}): {resp.text[:120]}')
                else:
                    all_quota_exceeded = False
                    logger.warning(f'[AI Analyst] API Gemini modelo {model_name} ({resp.status_code}): {resp.text[:120]}')
            except Exception as e:
                all_quota_exceeded = False
                logger.warning(f'[AI Analyst] Exceção ao consultar Gemini ({model_name}): {e}')

        # Se TODOS os modelos retornaram 429, ativa circuit breaker global
        if all_quota_exceeded:
            cls._quota_exhausted = True
            logger.warning('[AI Analyst] ⚡ QUOTA ESGOTADA em todos os modelos. Ativando fallback determinístico para todos os jogos restantes.')

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
        Gera análise heurística de fallback sem IA.
        Filtro aprovado pelo usuário com 5 critérios rigorosos:
        - Odd Casa < 1.80
        - Odd BTTS > 1.90
        - Odd Over 2.5 < 1.80
        - Casa: max_defeats_last5 == 0
        - Visitante: max_wins_last5 <= 1
        """
        home_team = match_info.get('home', 'Mandante')
        away_team = match_info.get('away', 'Visitante')
        league = match_info.get('league', '')
        target_display = target_score.replace('-', 'x')
        
        # 1. Recuperar dados do cache do DataFootball
        import datetime
        from data import cache
        from data.data_manager import DataManager
        
        date_str = datetime.date.today().strftime('%Y-%m-%d')
        cached_fixtures = cache.get(f"df_fixtures_{date_str}")
        
        match_data = None
        if cached_fixtures:
            for f in cached_fixtures:
                if f.get('home_name') == home_team and f.get('away_name') == away_team:
                    match_data = f
                    break
                    
        if not match_data:
            return {
                'verdict': 'VETADO',
                'confidence': 10,
                'critical_factor': 'Fallback falhou: Partida não encontrada no cache do DataFootball.',
                'detailed_analysis': 'Não foi possível recuperar os dados de odds e estatísticas para aplicar os critérios do fallback.',
                'adjustment_factor': 1.0
            }
            
        # 2. Avaliar critérios de odds
        odd_home = float(match_data.get('odds_ft_1') or 99)
        odd_btts = float(match_data.get('odds_btts_yes') or 0)
        odd_over25 = float(match_data.get('odds_ft_over25') or 99)
        
        if odd_home >= 1.80:
            return cls._veto_fallback(target_display, f'Odd do Mandante ({odd_home}) >= 1.80')
        if odd_btts <= 1.90:
            return cls._veto_fallback(target_display, f'Odd BTTS ({odd_btts}) <= 1.90')
        if odd_over25 >= 1.80:
            return cls._veto_fallback(target_display, f'Odd Over 2.5 ({odd_over25}) >= 1.80')
            
        # 3. Avaliar forma (últimos 5)
        # O scanner já usou o DataManager.get_team_stats e os guardou no cache do fbref/datafootball
        home_id = match_data.get('homeID')
        away_id = match_data.get('awayID')
        league_id = match_data.get('league')
        
        home_stats = DataManager.get_team_stats(home_id, league_id, 'DataFootball')
        away_stats = DataManager.get_team_stats(away_id, league_id, 'DataFootball')
        
        if not home_stats or not away_stats:
            return cls._veto_fallback(target_display, 'Estatísticas de formulário indisponíveis no cache.')
            
        # Vamos assumir que as stats têm um campo 'last_5_results' ou podemos deduzir
        # O FootballData/DataFootball costuma ter form como W,D,L... (por ex: "WWDLD")
        home_form = home_stats.get('form', '')[:5]
        away_form = away_stats.get('form', '')[:5]
        
        home_defeats = home_form.count('L')
        away_wins = away_form.count('W')
        
        if home_defeats > 0:
            return cls._veto_fallback(target_display, f'Casa com derrota nos últimos 5 ({home_form})')
            
        if away_wins > 1:
            return cls._veto_fallback(target_display, f'Visitante com >1 vitória fora nos últimos 5 ({away_form})')
            
        # Tudo passou no crivo
        verdict = 'APROVADO'
        confidence = 90
        critical = f'Aprovado pelos 5 critérios estritos de Odds e Histórico (Sem IA).'
        detailed = (
            f'Jogo aprovado pelo filtro de Fallback Sem IA: Odd Home ({odd_home}) < 1.80, '
            f'Odd BTTS ({odd_btts}) > 1.90, Odd Over2.5 ({odd_over25}) < 1.80. '
            f'Histórico OK: Casa sem derrotas ({home_form}), Visitante com máx 1 vitória ({away_form}).'
        )

        return {
            'verdict': verdict,
            'confidence': confidence,
            'critical_factor': critical[:250],
            'detailed_analysis': detailed,
            'adjustment_factor': 1.0
        }

    @classmethod
    def _veto_fallback(cls, target_display, reason):
        return {
            'verdict': 'VETADO',
            'confidence': 20,
            'critical_factor': reason,
            'detailed_analysis': f'Veto pelo Fallback de Odds: {reason}',
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
        for model in ['gemini-flash-latest']:
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
                    analysis = cls.orchestrate_match(match, target_score, prob)
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
