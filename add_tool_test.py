import re

with open('tests/unit/test_ai_analyst.py', 'r') as f:
    content = f.read()

new_test = """
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
    assert res['veredito'] == 'APROVADO'
    assert 'Clima: Clear' in res['fator_critico']
"""

with open('tests/unit/test_ai_analyst.py', 'a') as f:
    f.write(new_test)
