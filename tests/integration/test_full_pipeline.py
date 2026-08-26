import pytest
from unittest.mock import patch
from models.poisson import PoissonDixonColes
from analysis.scanner import scan_all, rank_by_target, save_to_db
from database.db import Base, engine, SessionLocal
from database.models_db import Match, Prediction
import config

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield

@patch('analysis.scanner.get_team_stats')
def test_pipeline_fixtures_to_db(mock_get_stats):
    mock_get_stats.return_value = {
        'fixtures': {
            'goals': {'for': {'total': {'home': 10, 'away': 10}}, 'against': {'total': {'home': 5, 'away': 5}}},
            'played': {'home': 10, 'away': 10}
        }
    }
    
    fixtures = [{
        'fixture': {'id': 101, 'date': '2026-08-25T20:00:00', 'status': {'short': 'NS'}},
        'league': {'id': 71, 'name': 'Brasileirao'},
        'teams': {'home': {'id': 1, 'name': 'Cruzeiro'}, 'away': {'id': 2, 'name': 'Atletico-MG'}}
    }]
    
    config.TARGET_SCORES = ['0-1']
    model = PoissonDixonColes()
    
    results = scan_all(fixtures, model)
    assert len(results) == 1
    
    rankings = rank_by_target(results)
    assert '0-1' in rankings
    assert rankings['0-1'][0]['home'] == 'Cruzeiro'
    
    db = SessionLocal()
    save_to_db(db, rankings)
    
    matches = db.query(Match).all()
    assert len(matches) == 1
    assert matches[0].home_team == 'Cruzeiro'
    
    preds = db.query(Prediction).all()
    assert len(preds) == 1
    assert preds[0].target_score == '0-1'
    db.close()
