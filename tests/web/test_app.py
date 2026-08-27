import pytest
from web.app import app

import base64
import config

def get_auth_headers():
    username = config.DASHBOARD_USERNAME
    password = config.DASHBOARD_PASSWORD
    token = base64.b64encode(f"{username}:{password}".encode('utf-8')).decode('utf-8')
    return {'Authorization': f'Basic {token}'}

from database.db import Base, SessionLocal
import database.db
from database.models_db import Match, Prediction
from sqlalchemy import create_engine
import datetime

@pytest.fixture(autouse=True)
def setup_db():
    # Isola o banco de dados dos testes criando um banco em memoria
    test_engine = create_engine("sqlite:///:memory:")
    database.db.engine = test_engine
    database.db.SessionLocal.configure(bind=test_engine)
    
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_route(client):
    response = client.get('/', headers=get_auth_headers())
    assert response.status_code == 200
    assert b"Lay CS Scanner" in response.data

def test_history_route(client):
    db = SessionLocal()
    # Adicionamos rank=1 para nao quebrar a ordenacao caso apareca na tela inicial do teste
    m = Match(fixture_id=999, date=datetime.datetime.now(), league_name="PL", home_team="A", away_team="B", status="FT", real_score="2-0")
    db.add(m)
    db.commit()
    p = Prediction(match_id=m.id, target_score="0-1", probability=0.05, rank=1, is_hit=True)
    db.add(p)
    db.commit()
    db.close()
    
    response = client.get('/history', headers=get_auth_headers())
    assert response.status_code == 200
    assert b"Win Rate" in response.data
    assert b"GREEN" in response.data
