import pytest
from unittest.mock import patch
from data import api_football
import config

def test_filter_main_leagues():
    fixtures = [
        {"league": {"id": 39}}, # PL (Main)
        {"league": {"id": 9999}} # Unmapped
    ]
    filtered = api_football.filter_main_leagues(fixtures)
    assert len(filtered) == 1
    assert filtered[0]["league"]["id"] == 39

@patch("data.api_football.cache.get")
@patch("requests.get")
def test_get_fixtures(mock_get, mock_cache):
    mock_cache.return_value = None
    class MockResponse:
        def raise_for_status(self): pass
        def json(self):
            return {"response": [{"league": {"id": 39}}]}
    mock_get.return_value = MockResponse()
    
    fixtures = api_football.get_fixtures("2026-08-25")
    assert len(fixtures) == 1
    assert fixtures[0]["league"]["id"] == 39
    mock_get.assert_called_once()

@patch('data.api_football.cache.get')
@patch('data.api_football.requests.get')
def test_api_timezone_param(mock_get, mock_cache):
    mock_cache.return_value = None
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {'response': []}
    api_football.get_fixtures('2026-08-25')
    called_url = mock_get.call_args[0][0]
    assert f"timezone={config.SCHEDULER_TIMEZONE}" in called_url
