import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from web.app import app, auth

@pytest.fixture
def client():
    app.config['TESTING'] = True
    
    # Mock authentication completely
    @auth.verify_password
    def verify_password(username, password):
        return "testuser"
        
    with app.test_client() as client:
        yield client

def test_backtest_page_loads(client):
    response = client.get('/backtest', headers={'Authorization': 'Basic dGVzdHVzZXI6dGVzdHBhc3M='})
    assert response.status_code == 200
    assert 'Backtest'.encode('utf-8') in response.data

def test_backtest_api_returns_data(client):
    payload = {
        "market": "0-1",
        "odd": 12.0,
        "stake": 100,
        "min_power": 99.0,
        "max_power": 100.0
    }
    response = client.post('/api/backtest/run', json=payload, headers={'Authorization': 'Basic dGVzdHVzZXI6dGVzdHBhc3M='})
    assert response.status_code == 200
    data = response.get_json()
    assert 'volume' in data
    assert 'winrate' in data
    assert 'profit' in data
    assert 'roi' in data
    assert 'chart_data' in data
    assert isinstance(data['chart_data'], list)
