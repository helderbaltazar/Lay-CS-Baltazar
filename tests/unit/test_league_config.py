from data.league_config import MAIN_LEAGUES, LEAGUE_AVERAGES, get_league_avg

def test_all_main_leagues_have_averages():
    for league_id in MAIN_LEAGUES:
        assert league_id in LEAGUE_AVERAGES

def test_get_league_avg_fallback():
    avg_home, avg_away = get_league_avg(99999) # Liga desconhecida
    assert avg_home == 1.40
    assert avg_away == 1.10

def test_get_league_avg_known():
    avg_home, avg_away = get_league_avg(71)
    assert avg_home == 1.35
    assert avg_away == 1.10
