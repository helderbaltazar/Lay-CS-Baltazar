import pytest
from unittest.mock import patch, MagicMock
from analysis.odds_fetcher import fetch_odds_cascade

@patch('analysis.odds_fetcher.get_events')
def test_odds_cascade_odds_api(mock_get_events):
    mock_get_events.return_value = [{
        'home_team': 'Cruzeiro',
        'away_team': 'Atletico Mineiro',
        'bookmakers': [{
            'markets': [
                {'key': 'h2h', 'outcomes': [{'name': 'Cruzeiro', 'price': 2.10}]},
                {'key': 'btts', 'outcomes': [{'name': 'Yes', 'price': 1.85}]}
            ]
        }]
    }]
    
    fixture = {
        'teams': {'home': {'name': 'Cruzeiro'}, 'away': {'name': 'Atletico Mineiro'}},
        'league': {'id': 71}, # Brazil Serie A
        'fixture': {'id': 1234}
    }
    
    with patch('analysis.odds_fetcher.SPORT_KEYS', {'soccer_brazil_serie_a': 71}):
        match_odd, btts_odd, source = fetch_odds_cascade(fixture)
        
    assert match_odd == 2.10
    assert btts_odd == 1.85
    assert source == "Odds-API"

@patch('analysis.odds_fetcher.get_events')
def test_odds_cascade_unavailable(mock_get_events):
    mock_get_events.return_value = []
    
    fixture = {
        'teams': {'home': {'name': 'Unknown'}, 'away': {'name': 'Unknown'}},
        'league': {'id': 999},
        'fixture': {'id': 1234}
    }
    
    match_odd, btts_odd, source = fetch_odds_cascade(fixture)
    
    assert match_odd is None
    assert btts_odd is None
    assert source == "unavailable"
