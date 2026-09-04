import pytest
from analysis.scanner import rank_by_target
import config

def test_ranking_logic_lowest_prob_is_first():
    # Simulando resultados do scanner
    # Queremos que o jogo com MENOR probabilidade do placar exato fique em #1
    # Porque a menor probabilidade de 0-1 significa a MAIOR probabilidade de dar Green (Lay)
    extra_markets_dict = {
        "OVER_2.5": 0.5, "UNDER_2.5": 0.5, "UNDER_3.5": 0.5, "UNDER_4.5": 0.5, 
        "BTTS_YES": 0.5, "BACK_HOME": 0.5, "LAY_DRAW": 0.5, "UNDER_0.5_HT": 0.5, "UNDER_1.5_HT": 0.5, "UNDER_2.5_HT": 0.5
    }
    results = [
        {
            'fixture_id': 1, 'date': '2026-08-25', 'status': 'NS', 'league': 'L1', 'home': 'Time A', 'away': 'Time B',
            'lambda_home': 1.0, 'lambda_away': 1.0, 'probabilities': {'0-1': 0.15},
            'extra_probabilities': extra_markets_dict
        },
        {
            'fixture_id': 2, 'date': '2026-08-25', 'status': 'NS', 'league': 'L1', 'home': 'Time C', 'away': 'Time D',
            'lambda_home': 1.0, 'lambda_away': 1.0, 'probabilities': {'0-1': 0.02},
            'extra_probabilities': extra_markets_dict
        },
        {
            'fixture_id': 3, 'date': '2026-08-25', 'status': 'NS', 'league': 'L1', 'home': 'Time E', 'away': 'Time F',
            'lambda_home': 1.0, 'lambda_away': 1.0, 'probabilities': {'0-1': 0.08},
            'extra_probabilities': extra_markets_dict
        }
    ]
    
    config.TARGET_SCORES = ['0-1']
    
    class DummyModel:
        def get_probabilities(self, l_h, l_a, targets):
            return {t: 0.1 for t in targets}
        def blend_probability(self, prob, odd):
            return prob
        def calculate_ev(self, prob, odd):
            return 0.0
    
    rankings = rank_by_target(results, DummyModel())
    
    # O jogo 2 (0.02) deve ser o Rank 1
    assert rankings['0-1'][0]['fixture_id'] == 2
    assert rankings['0-1'][0]['rank'] == 1
    
    # O jogo 3 (0.08) deve ser o Rank 2
    assert rankings['0-1'][1]['fixture_id'] == 3
    assert rankings['0-1'][1]['rank'] == 2
    
    # O jogo 1 (0.15) deve ser o Rank 3
    assert rankings['0-1'][2]['fixture_id'] == 1
    assert rankings['0-1'][2]['rank'] == 3
