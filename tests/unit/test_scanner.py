import pytest
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
