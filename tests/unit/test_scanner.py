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
    extra_markets_dict = {
        "OVER_2.5": 0.5, "UNDER_2.5": 0.5, "UNDER_3.5": 0.5, "UNDER_4.5": 0.5, 
        "BTTS_YES": 0.5, "BACK_HOME": 0.5, "LAY_DRAW": 0.5, "UNDER_0.5_HT": 0.5, "UNDER_1.5_HT": 0.5
    }
    results = [
        {'fixture_id': 1, 'date': '2026-08-25', 'status': 'NS', 'league': 'L', 'home': 'A', 'away': 'B', 'lambda_home': 1, 'lambda_away': 1, 'probabilities': {'0-1': 0.10, '0-2': 0.10, '0-3': 0.10, '1-3': 0.10}, 'extra_probabilities': extra_markets_dict},
        {'fixture_id': 2, 'date': '2026-08-25', 'status': 'NS', 'league': 'L', 'home': 'C', 'away': 'D', 'lambda_home': 1, 'lambda_away': 1, 'probabilities': {'0-1': 0.05, '0-2': 0.05, '0-3': 0.05, '1-3': 0.05}, 'extra_probabilities': extra_markets_dict}
    ]
    
    class DummyModel:
        def get_probabilities(self, l_h, l_a, targets):
            return {t: 0.1 for t in targets}
            
    rankings = rank_by_target(results, DummyModel())
    assert rankings['0-1'][0]['fixture_id'] == 2 # menor risco primeiro
    assert rankings['0-1'][0]['rank'] == 1



def test_scan_match_real_score():
    from analysis.scanner import scan_match
    import data.api_football
    import data.league_config
    import analysis.scanner
    
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
        def get_extra_probabilities(self, h, a):
            return {}
            
    with pytest.MonkeyPatch().context() as m:
        m.setattr(data.api_football, 'get_team_stats', lambda *args, **kwargs: {'goals': {'for': {'total': {'home': 1, 'away': 1}}, 'against': {'total': {'home': 1, 'away': 1}}}, 'fixtures': {'played': {'home': 1, 'away': 1}}})
        m.setattr('data.data_manager.DataManager.get_team_stats', lambda *args, **kwargs: {'goals': {'for': {'total': {'home': 1, 'away': 1}}, 'against': {'total': {'home': 1, 'away': 1}}}, 'fixtures': {'played': {'home': 1, 'away': 1}}})
        m.setattr(data.league_config, 'get_league_avg', lambda x: (1.5, 1.2))
        m.setattr(analysis.scanner, 'get_league_avg', lambda x: (1.5, 1.2))
        
        res = scan_match(fixture, DummyModel(), ['0-1'])
        assert res is not None
        assert res['real_score'] == '2-1'
