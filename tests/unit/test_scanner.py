from analysis.scanner import calculate_lambdas, rank_by_target
import config

def test_calculate_lambdas_with_smoothing():
    home_stats = {'fixtures': {'goals': {'for': {'total': {'home': 0}}, 'against': {'total': {'home': 0}}}, 'played': {'home': 0}}}
    away_stats = {'fixtures': {'goals': {'for': {'total': {'away': 0}}, 'against': {'total': {'away': 0}}}, 'played': {'away': 0}}}
    
    lam_home, lam_away = calculate_lambdas(home_stats, away_stats, (1.5, 1.2))
    
    assert lam_home >= 0.2
    assert lam_away >= 0.2

def test_rank_by_target():
    results = [
        {'fixture_id': 1, 'date': '2026-08-25', 'status': 'NS', 'league': 'PL', 'home': 'A', 'away': 'B', 'lambda_home': 1, 'lambda_away': 1, 'probabilities': {'0-1': 0.1, '0-2': 0.05}},
        {'fixture_id': 2, 'date': '2026-08-25', 'status': 'NS', 'league': 'PL', 'home': 'C', 'away': 'D', 'lambda_home': 1, 'lambda_away': 1, 'probabilities': {'0-1': 0.02, '0-2': 0.08}}
    ]
    config.TARGET_SCORES = ["0-1", "0-2"]
    
    rankings = rank_by_target(results)
    
    assert rankings['0-1'][0]['fixture_id'] == 2
    assert rankings['0-1'][1]['fixture_id'] == 1
    assert rankings['0-2'][0]['fixture_id'] == 1
    assert rankings['0-2'][1]['fixture_id'] == 2
