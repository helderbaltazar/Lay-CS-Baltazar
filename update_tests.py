import re

with open('tests/unit/test_ai_analyst.py', 'r') as f:
    content = f.read()

new_test = """def test_build_prompt_contains_match_data():
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
    assert 'Risco Alto' in prompt
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
"""

content = re.sub(
    r"def test_build_prompt_contains_match_data\(\):.*?assert '0\.75' in prompt",
    new_test,
    content,
    flags=re.DOTALL
)

with open('tests/unit/test_ai_analyst.py', 'w') as f:
    f.write(content)
