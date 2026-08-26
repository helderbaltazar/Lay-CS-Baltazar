with open('analysis/scanner.py', 'r') as f:
    content = f.read()

# 1. Update scan_match
old_return = """    return {
        'fixture_id': fixture_info['id'],
        'date': fixture_info['date'],
        'status': fixture_info['status']['short'],
        'league': league_info['name'],"""
        
new_return = """    real_score = None
    if fixture_info['status']['short'] in ['FT', 'AET', 'PEN']:
        goals = fixture.get('goals', {})
        if goals.get('home') is not None and goals.get('away') is not None:
            real_score = f"{goals['home']}-{goals['away']}"

    return {
        'fixture_id': fixture_info['id'],
        'date': fixture_info['date'],
        'status': fixture_info['status']['short'],
        'real_score': real_score,
        'league': league_info['name'],"""
content = content.replace(old_return, new_return)

# 2. Update rank_by_target
old_rank = """                'date': res['date'],
                'status': res['status'],
                'league': res['league'],"""
new_rank = """                'date': res['date'],
                'status': res['status'],
                'real_score': res.get('real_score'),
                'league': res['league'],"""
content = content.replace(old_rank, new_rank)

# 3. Update save_to_db
old_save_create = """                    match = Match(
                        fixture_id=fix_id,
                        date=dt,
                        league_name=rec['league'],
                        home_team=rec['home'],
                        away_team=rec['away'],
                        status=rec['status']
                    )
                    db.add(match)
                    db.flush()
                else:
                    match.status = rec['status']"""
new_save_create = """                    match = Match(
                        fixture_id=fix_id,
                        date=dt,
                        league_name=rec['league'],
                        home_team=rec['home'],
                        away_team=rec['away'],
                        status=rec['status'],
                        real_score=rec.get('real_score')
                    )
                    db.add(match)
                    db.flush()
                else:
                    match.status = rec['status']
                    match.real_score = rec.get('real_score')"""
content = content.replace(old_save_create, new_save_create)

with open('analysis/scanner.py', 'w') as f:
    f.write(content)
print("Scanner patched with real_score extraction.")

# Now write tests
import os
tests_api_football_path = 'tests/integration/test_api_football.py'
if os.path.exists(tests_api_football_path):
    with open(tests_api_football_path, 'a') as f:
        f.write("""\n
import config
from unittest.mock import patch
def test_api_timezone_param():
    from data.api_football import get_fixtures
    with patch('data.api_football.requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'response': []}
        get_fixtures('2026-08-25')
        called_url = mock_get.call_args[0][0]
        assert f"timezone={config.SCHEDULER_TIMEZONE}" in called_url
""")
        
tests_scanner_path = 'tests/unit/test_scanner.py'
if os.path.exists(tests_scanner_path):
    with open(tests_scanner_path, 'a') as f:
        f.write("""\n
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
""")
print("Tests created.")
