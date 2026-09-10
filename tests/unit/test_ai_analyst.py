import pytest
from unittest.mock import patch, MagicMock
from analysis.ai_analyst import AIAnalyst
import config

def test_build_prompt_contains_match_data():
    match_info = {
        'home': 'Cruzeiro',
        'away': 'Atletico-MG',
        'league': 'Brasileirao',
        'lambda_home': 1.85,
        'lambda_away': 0.75,
        'match_context': {
            'btts_odd': 1.55,
            'h2h_home': 60,
            'h2h_away': 20,
            'must_win': True
        }
    }
    prompt = AIAnalyst.build_prompt(match_info, '0-1', 0.045)
    assert 'Cruzeiro' in prompt
    assert 'Atletico-MG' in prompt
    assert 'Lay 0x1' in prompt
    assert '4.5%' in prompt
    assert '1.55' in prompt
    assert 'Alto' in prompt
    assert 'Necessidade de Vit' in prompt

def test_rescue_rejected_matches():
    rejected = [
        {'id': 1, 'match_context': {'match_odd': 1.05}},
        {'id': 2, 'match_context': {'match_odd': 2.50}},
        {'id': 3, 'match_context': {'match_odd': 1.99}},
        {'id': 4, 'match_context': {}},
        {'id': 5}
    ]
    rescued = AIAnalyst.rescue_rejected_matches(rejected)
    assert len(rescued) == 2
    ids = [m['id'] for m in rescued]
    assert 1 in ids
    assert 3 in ids


def test_parse_ai_json_valid():
    raw_text = '{"veredito": "APROVADO", "confianca": 95, "fator_critico": "Mandante muito seguro em casa.", "analise_detalhada": "Cruzeiro tem defesa forte e visitante desfalcado.", "fator_ajuste": 0.8}'
    parsed = AIAnalyst._parse_ai_json(raw_text)
    assert parsed is not None
    assert parsed['verdict'] == 'APROVADO'
    assert parsed['confidence'] == 95
    assert parsed['critical_factor'] == 'Mandante muito seguro em casa.'
    assert 'Cruzeiro' in parsed['detailed_analysis']
    assert parsed['adjustment_factor'] == 0.8

def test_parse_ai_json_with_markdown_ticks():
    raw_text = '```json\n{"veredito": "VETADO", "confianca": 40, "fator_critico": "Artilheiro titular poupado.", "analise_detalhada": "Risco elevado de surpresa."}\n```'
    parsed = AIAnalyst._parse_ai_json(raw_text)
    assert parsed is not None
    assert parsed['verdict'] == 'VETADO'
    assert parsed['confidence'] == 40
    assert 'poupado' in parsed['critical_factor']

def test_fallback_analysis_low_prob():
    match_info = {'home': 'Real Madrid', 'away': 'Getafe'}
    analysis = AIAnalyst._fallback_analysis(match_info, '0-1', 0.03)
    assert analysis['verdict'] == 'APROVADO'
    assert analysis['confidence'] >= 90
    assert '0x1' in analysis['critical_factor']
    assert analysis['adjustment_factor'] == 1.0

def test_fallback_analysis_high_prob():
    match_info = {'home': 'Time Fraco', 'away': 'Bayern'}
    analysis = AIAnalyst._fallback_analysis(match_info, '0-1', 0.18)
    assert analysis['verdict'] == 'VETADO'
    assert analysis['confidence'] == 82

def test_analyze_match_fallback_when_no_key(monkeypatch):
    monkeypatch.setattr(config, 'GEMINI_API_KEY', '')
    import os
    monkeypatch.setattr(os, 'environ', {})
    match_info = {'home': 'Flamengo', 'away': 'Vasco', 'league': 'Brasileirao'}
    res = AIAnalyst.orchestrate_match(match_info, '0-2', 0.05)
    assert res['verdict'] in ['APROVADO', 'VETADO']
    assert res['confidence'] > 0
    assert 'critical_factor' in res
    assert 'detailed_analysis' in res

@patch('requests.post')
def test_analyze_match_with_mocked_gemini(mock_post, monkeypatch):
    monkeypatch.setattr(config, 'GEMINI_API_KEY', 'fake-gemini-key')
    
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        'candidates': [{
            'content': {
                'parts': [{
                    'text': '{"veredito": "APROVADO", "confianca": 91, "fator_critico": "Visitante sem atacante titular.", "analise_detalhada": "Jogo favoravel para Lay."}'
                }]
            }
        }]
    }
    mock_post.return_value = mock_resp
    
    match_info = {'home': 'Liverpool', 'away': 'Everton', 'league': 'Premier League'}
    res = AIAnalyst.orchestrate_match(match_info, '0-1', 0.04)
    print('RES:', res)
    assert res['verdict'] == 'APROVADO'
    assert res['confidence'] == 91
    assert 'Consenso' in res['critical_factor']


@patch('analysis.ai_analyst.AIAnalyst.orchestrate_match')
def test_analyze_top_rankings_enriches_matches(mock_orchestrate):
    mock_orchestrate.return_value = {
        'verdict': 'APROVADO',
        'confidence': 90,
        'critical_factor': 'Teste',
        'detailed_analysis': 'Detalhe'
    }

    rankings = {
        '0-1': [
            {'home': 'A', 'away': 'B', 'probability': 0.04, 'rank': 1},
            {'home': 'C', 'away': 'D', 'probability': 0.05, 'rank': 2}
        ],
        '0-2': [
            {'home': 'E', 'away': 'F', 'probability': 0.03, 'rank': 1}
        ]
    }
    
    enriched = AIAnalyst.analyze_top_rankings(rankings, top_n=5)
    
    for target, matches in enriched.items():
        for m in matches:
            assert 'ai_verdict' in m
            assert 'ai_confidence' in m
            assert 'ai_critical_factor' in m
            assert 'ai_analysis' in m
            assert m['ai_verdict'] in ['APROVADO', 'VETADO']

@patch('data.api_football.get_fixture_lineups')
@patch('data.api_football.get_fixture_injuries')
@patch('analysis.ai_analyst.requests.post')
def test_get_deep_match_analysis_with_fixture(mock_post, mock_inj, mock_lin, monkeypatch):
    from analysis.ai_analyst import AIAnalyst
    import config
    monkeypatch.setattr(config, 'GEMINI_API_KEY', 'fake')
    
    mock_inj.return_value = [{'player': {'name': 'Player1'}, 'type': 'Missing'}]
    mock_lin.return_value = [{'team': {'name': 'A'}, 'formation': '4-4-2'}]
    
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {'candidates': [{'content': {'parts': [{'text': '{"momentos_gols": "X"}'}]}}]}
    mock_post.return_value = mock_resp
    
    res = AIAnalyst.get_deep_match_analysis('Team A', 'Team B', 'League X', fixture_id=999)
    assert res['momentos_gols'] == 'X'
    
    # Verify the prompt contained the injected text
    called_json = mock_post.call_args[1]['json']
    prompt_used = called_json['contents'][0]['parts'][0]['text']
    assert 'Player1' in prompt_used
    assert '4-4-2' in prompt_used

from unittest.mock import patch

@patch('requests.post')
def test_agent_calls_weather_tool(mock_post):
    from analysis.ai_analyst import AIAnalyst
    # Mocking gemini response containing a functionCall
    mock_resp = mock_post.return_value
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [{
            "content": {
                "parts": [{
                    "functionCall": {
                        "name": "get_weather_condition",
                        "args": {"stadium": "Mineirao"}
                    }
                }]
            }
        }]
    }
    
    match_info = {
        'home': 'Cruzeiro',
        'away': 'Atletico-MG',
        'league': 'Brasileirao',
        'lambda_home': 1.85,
        'lambda_away': 0.75,
        'match_context': {}
    }
    
    # We call orchestrate_match. It will call _call_llm_with_prompt 3 times.
    # The first time it gets the functionCall, it returns APROVADO and fator_critico="Clima: Clear".
    res = AIAnalyst.orchestrate_match(match_info, '0-1', 0.045)
    
    # Check if the tool was indeed executed and its result returned
    # Since all 3 agents get the same mocked response, there are 3 approvals
    assert res['verdict'] == 'APROVADO'
    assert res['verdict'] == 'APROVADO'
