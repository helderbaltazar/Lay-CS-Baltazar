import pytest
from web.app import app
from database.db import Base, engine, SessionLocal
from database.models_db import Match, Prediction
import datetime

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_route(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"Lay CS Scanner" in response.data

def test_history_route(client):
    db = SessionLocal()
    m = Match(fixture_id=999, date=datetime.datetime.now(), league_name="PL", home_team="A", away_team="B", status="FT", real_score="2-0")
    db.add(m)
    db.commit()
    p = Prediction(match_id=m.id, target_score="0-1", probability=0.05, is_hit=True)
    db.add(p)
    db.commit()
    db.close()
    
    response = client.get('/history')
    assert response.status_code == 200
    assert b"Win Rate" in response.data
    assert b"GREEN" in response.data
