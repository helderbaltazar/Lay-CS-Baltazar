import re

files_to_fix = [
    'tests/unit/test_scanner.py',
    'tests/integration/test_full_pipeline.py'
]

for filepath in files_to_fix:
    with open(filepath, 'r') as f:
        content = f.read()
    
    # regex replace 'fixtures': {'goals': ... } to 'goals': ..., 'fixtures': {'played': ... }
    # Since writing regex for this is hard, I'll just write new content for test_scanner.py
    
    if 'test_scanner.py' in filepath:
        new_content = """import pytest
from analysis.scanner import calculate_lambdas

def test_calculate_lambdas_with_smoothing():
    home_stats = {'goals': {'for': {'total': {'home': 0}}, 'against': {'total': {'home': 0}}}, 'fixtures': {'played': {'home': 0}}}
    away_stats = {'goals': {'for': {'total': {'away': 0}}, 'against': {'total': {'away': 0}}}, 'fixtures': {'played': {'away': 0}}}
    
    lam_home, lam_away = calculate_lambdas(home_stats, away_stats, (1.5, 1.2))
    
    # 0 goals + 0.1 smoothing
    assert lam_home > 0
    assert lam_away > 0

def test_rank_by_target():
    from analysis.scanner import rank_by_target
    results = [
        {'fixture_id': 1, 'target_probabilities': {'0-1': 0.10}},
        {'fixture_id': 2, 'target_probabilities': {'0-1': 0.05}}
    ]
    rankings = rank_by_target(results)
    assert rankings['0-1'][0]['fixture_id'] == 2 # menor risco primeiro
    assert rankings['0-1'][0]['rank'] == 1
"""
        with open(filepath, 'w') as f:
            f.write(new_content)
            
    if 'test_full_pipeline.py' in filepath:
        old_mock = """    mock_get_stats.return_value = {
        'fixtures': {
            'goals': {'for': {'total': {'home': 10, 'away': 10}}, 'against': {'total': {'home': 5, 'away': 5}}},
            'played': {'home': 10, 'away': 10}
        }
    }"""
        new_mock = """    mock_get_stats.return_value = {
        'goals': {'for': {'total': {'home': 10, 'away': 10}}, 'against': {'total': {'home': 5, 'away': 5}}},
        'fixtures': {'played': {'home': 10, 'away': 10}}
    }"""
        if old_mock in content:
            with open(filepath, 'w') as f:
                f.write(content.replace(old_mock, new_mock))
