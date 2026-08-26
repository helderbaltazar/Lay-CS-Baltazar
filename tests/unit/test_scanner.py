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
        {'fixture_id': 1, 'date': '2026-08-25', 'status': 'NS', 'league': 'L', 'home': 'A', 'away': 'B', 'lambda_home': 1, 'lambda_away': 1, 'probabilities': {'0-1': 0.10}},
        {'fixture_id': 2, 'date': '2026-08-25', 'status': 'NS', 'league': 'L', 'home': 'C', 'away': 'D', 'lambda_home': 1, 'lambda_away': 1, 'probabilities': {'0-1': 0.05}}
    ]
    rankings = rank_by_target(results)
    assert rankings['0-1'][0]['fixture_id'] == 2 # menor risco primeiro
    assert rankings['0-1'][0]['rank'] == 1


def test_scan_match_real_score():
    from analysis.scanner import scan_match
    
    # Mock fixture that is finished
    fixture = {
        'fixture': {
            'id': 1,
            'date': '2026-08-25T12:00:00',
            'status': {'short': 'FT'}
        },
        'league': {'id': 39, 'name': 'Premier League'},
        'teams': {'home': {'id': 1, 'name': 'A'}, 'away': {'id': 2, 'name': 'B'}},
        'goals': {'home': 2, 'away': 1}
    }
    
    class DummyModel:
        def get_probabilities(self, h, a, t):
            return {'0-1': 0.1}
            
    import analysis.scanner
    import data.api_football
    import data.league_config
    
    # Mock the stats function
    original_get_team_stats = data.api_football.get_team_stats
    data.api_football.get_team_stats = lambda t, l: {'goals': {'for': {'total': {'home': 1, 'away': 1}}, 'against': {'total': {'home': 1, 'away': 1}}}, 'fixtures': {'played': {'home': 1, 'away': 1}}}
    original_get_league_avg = data.league_config.get_league_avg
    data.league_config.get_league_avg = lambda l: (1.5, 1.2)
    
    res = scan_match(fixture, DummyModel(), ['0-1'])
    
    assert res['real_score'] == '2-1'
    
    # Restore
    data.api_football.get_team_stats = original_get_team_stats
    data.league_config.get_league_avg = original_get_league_avg
