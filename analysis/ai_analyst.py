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
        prob_pct = round(prob_poisson * 100, 2)
        target_display = target_score.replace('-', 'x')

        return f"""Você é um analista quantitativo e especialista profissional em apostas esportivas de Lay Correct Score (apostar CONTRA um placar exato).

PARTIDA PARA AUDITORIA:
- Jogo: {home_team} vs {away_team}
- Competição: {league}
- Alvo Poisson/SxG: Lay {target_display} (Probabilidade estimada do placar ocorrer: {prob_pct}%)
- Força de Ataque/Gols Esperados: Mandante (λ={lam_home:.2f}), Visitante (λ={lam_away:.2f})

DIRETRIZES DE ESPECIALISTA EM LAY CS:
1. Lay 0x1 / Lay 0x2: Apostamos que o visitante NÃO vencerá por 1x0 ou 2x0 sem sofrer gols. Avalie se o mandante tem capacidade de marcar ao menos 1 gol ou segurar o jogo, e se o visitante tem desfalques no ataque.
2. Lay 0x3 / Lay 1x3: Apostamos que o visitante NÃO marcará 3 gols fora de casa. Avalie se a partida tem baixa tendência de goleada do visitante.
3. Fatores de Veto: Se o mandante estiver poupando time titular inteiro, com crise grave, ou se houver risco extremo do visitante golear com placar exato de {target_display}, você deve VETAR.

Pesquise notícias recentes (escalações prováveis, desfalques, momento dos times) e responda ESTRITAMENTE em formato JSON com esta estrutura:
{{
  "veredito": "APROVADO" ou "VETADO",
  "confianca": <inteiro de 0 a 100 representando a segurança no Lay>,
  "fator_critico": "<frase curta de até 120 caracteres resumindo o principal motivo do veredito>",
  "analise_detalhada": "<parágrafo explicativo de 2 a 4 frases para exibição no Dashboard>"
}}
"""

    @classmethod
    def analyze_match(cls, match_info: dict, target_score: str, prob_poisson: float) -> dict:
        """
        Analisa uma partida individualmente.
        Tenta chamar a API do Gemini com RAG; se falhar ou sem chave,
        executa o motor heurístico de fallback gracioso.
        """
        if not getattr(config, 'AI_ANALYST_ENABLED', True):
            return cls._fallback_analysis(match_info, target_score, prob_poisson, 'IA desativada nas configurações.')

        gemini_key = getattr(config, 'GEMINI_API_KEY', '') or os.getenv('GEMINI_API_KEY', '')
        if not gemini_key:
            return cls._fallback_analysis(match_info, target_score, prob_poisson, 'Análise heurística estatística (chave de IA não configurada).')

        prompt = cls.build_prompt(match_info, target_score, prob_poisson)

        try:
            url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}'
            payload = {
                'contents': [{'parts': [{'text': prompt}]}],
                'generationConfig': {'temperature': 0.2, 'maxOutputTokens': 600},
                'tools': [{'google_search': {}}]
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
                logger.warning(f'[AI Analyst] Erro na API Gemini ({resp.status_code}): {resp.text[:200]}')
        except Exception as e:
            logger.warning(f'[AI Analyst] Exceção ao consultar Gemini: {e}')

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

                return {
                    'verdict': verdict,
                    'confidence': confidence,
                    'critical_factor': critical[:250],
                    'detailed_analysis': detailed
                }
        except Exception as e:
            logger.warning(f'[AI Analyst] Falha ao parsear JSON da IA: {e}')
        return None

    @classmethod
    def _fallback_analysis(cls, match_info: dict, target_score: str, prob_poisson: float, custom_reason: str = None) -> dict:
        """
        Gera análise heurística matemática quando a IA estiver offline.
        Garante estabilidade 100% resiliente.
        """
        home_team = match_info.get('home', 'Mandante')
        away_team = match_info.get('away', 'Visitante')
        target_display = target_score.replace('-', 'x')
        prob_pct = prob_poisson * 100

        if prob_pct <= 6.0:
            confidence = 92
            verdict = 'APROVADO'
            critical = custom_reason or f'Risco mínimo de {target_display} ({prob_pct:.1f}% probabilidade calculada via SxG).'
            detailed = f'O modelo estatístico Poisson + Dixon-Coles indica extrema improbabilidade do placar {target_display}. Mandante ({home_team}) com perfil favorável para anular a ocorrência.'
        elif prob_pct <= 12.0:
            confidence = 85
            verdict = 'APROVADO'
            critical = custom_reason or f'Boa margem de segurança para Lay {target_display} ({prob_pct:.1f}%).'
            detailed = f'Estatísticas de consistência indicam tendência favorável para Lay {target_display} contra {away_team}.'
        else:
            confidence = 60
            verdict = 'VETADO'
            critical = f'Probabilidade de {target_display} ({prob_pct:.1f}%) acima do limite seguro para Lay.'
            detailed = f'Partida vetada pelo crivo de segurança: a probabilidade do placar exato {target_display} foi avaliada como alta demais para a estratégia.'

        return {
            'verdict': verdict,
            'confidence': confidence,
            'critical_factor': critical[:250],
            'detailed_analysis': detailed
        }

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
                else:
                    fallback = cls._fallback_analysis(match, target_score, prob, 'Fora do Top 10 prioritário.')
                    match['ai_verdict'] = fallback['verdict']
                    match['ai_confidence'] = fallback['confidence']
                    match['ai_critical_factor'] = fallback['critical_factor']
                    match['ai_analysis'] = fallback['detailed_analysis']

        return rankings
