from unittest.mock import patch
import pytest
from analysis.scanner import calculate_lambdas

@patch("analysis.scanner.get_league_form_elo")
@patch("analysis.scanner.get_team_xg")
def test_calculate_lambdas_with_smoothing(mock_xg, mock_elo):
    """Should correctly calculate lambdas factoring in time decay and Elo"""
    home_stats = {
        'team': {'id': 10},
        'fixtures': {'played': {'home': 5}},
        'goals': {'for': {'total': {'home': 10}}, 'against': {'total': {'home': 5}}}
    }
    
    away_stats = {
        'team': {'id': 20},
        'fixtures': {'played': {'away': 5}},
        'goals': {'for': {'total': {'away': 5}}, 'against': {'total': {'away': 10}}}
    }
    
    mock_xg.return_value = {"xG_home": 1.5, "xGA_home": 1.2, "xG_away": 1.3, "xGA_away": 1.4}
    mock_elo.return_value.get_team_factors.return_value = (1.5, 1.2, 1500)
    lam_home, lam_away = calculate_lambdas(home_stats, away_stats, (1.5, 1.2), league_id=71)
    
    # 0 goals + 0.1 smoothing
    assert lam_home > 0
    assert lam_away > 0

@patch('analysis.ai_analyst.AIAnalyst.analyze_top_rankings', side_effect=lambda x, top_n=None: x)
def test_rank_by_target(mock_ai):
    from data.sportapi7 import SportAPI7
    SportAPI7.extract_smart_money_signals = lambda: {}
    from analysis.scanner import rank_by_target
    extra_markets_dict = {
        "OVER_2.5": 0.5, "UNDER_2.5": 0.5, "UNDER_3.5": 0.5, "UNDER_4.5": 0.5, 
        "BTTS_YES": 0.5, "BACK_HOME": 0.5, "LAY_DRAW": 0.5, "UNDER_0.5_HT": 0.5, "UNDER_1.5_HT": 0.5, "UNDER_2.5_HT": 0.5
    }
    results = [
        {'fixture_id': 1, 'date': '2026-08-25', 'status': 'NS', 'league': 'L', 'home': 'A', 'away': 'B', 'lambda_home': 1, 'lambda_away': 1, 'probabilities': {'0-1': 0.10, '0-2': 0.10, '0-3': 0.10, '1-3': 0.10, 'UNDER_0.5_HT': 0.10, 'UNDER_1.5_HT': 0.10, 'UNDER_2.5_HT': 0.10}, 'extra_probabilities': extra_markets_dict},
        {'fixture_id': 2, 'date': '2026-08-25', 'status': 'NS', 'league': 'L', 'home': 'C', 'away': 'D', 'lambda_home': 1, 'lambda_away': 1, 'probabilities': {'0-1': 0.05, '0-2': 0.05, '0-3': 0.05, '1-3': 0.05, 'UNDER_0.5_HT': 0.05, 'UNDER_1.5_HT': 0.05, 'UNDER_2.5_HT': 0.05}, 'extra_probabilities': extra_markets_dict}
    ]
    
    class DummyModel:
        def get_probabilities(self, l_h, l_a, targets):
            return {t: 0.1 for t in targets}
        def get_extra_probabilities(self, h, a):
            return {}
        def blend_probability(self, prob, odd):
            return prob
        def calculate_ev(self, prob, odd):
            return 0.0
            
    rankings = rank_by_target(results, DummyModel())
    assert rankings['0-1'][0]['fixture_id'] == 2 # menor risco primeiro
    assert rankings['0-1'][0]['rank'] == 1



@patch("analysis.scanner.get_league_form_elo")
@patch("analysis.scanner.get_team_xg")
@patch('analysis.odds_fetcher.fetch_odds_cascade', return_value=(2.10, 1.85, 'Odds-API'))
@patch('analysis.odds_fetcher.fetch_h2h', return_value=(0.5, 0.5))
@patch('analysis.odds_fetcher.fetch_must_win', return_value=True)
def test_scan_match_real_score(mock_must_win, mock_h2h, mock_cascade, mock_xg, mock_elo):
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
        
        mock_xg.return_value = {"xG_home": 1.5, "xGA_home": 1.2, "xG_away": 1.3, "xGA_away": 1.4}
        mock_elo.return_value.get_team_factors.return_value = (1.5, 1.2, 1500)
        res = scan_match(fixture, DummyModel(), ['0-1'])
        assert res is not None
        assert res['real_score'] == '2-1'
