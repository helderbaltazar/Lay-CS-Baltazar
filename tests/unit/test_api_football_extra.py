import pytest
from unittest.mock import patch
from data import api_football

@patch('data.api_football.requests.get')
@patch('data.api_football.cache.get')
def test_get_fixture_injuries_cached(mock_cache_get, mock_requests_get):
    mock_cache_get.return_value = [{'player': {'name': 'Neymar'}}]
    res = api_football.get_fixture_injuries(123)
    assert len(res) == 1
    assert res[0]['player']['name'] == 'Neymar'
    mock_requests_get.assert_not_called()

@patch('data.api_football.requests.get')
@patch('data.api_football.cache.get')
@patch('data.api_football.cache.set')
def test_get_fixture_lineups_api_call(mock_cache_set, mock_cache_get, mock_requests_get):
    mock_cache_get.return_value = None
    mock_requests_get.return_value.json.return_value = {'response': [{'team': {'name': 'Brasil'}}]}
    res = api_football.get_fixture_lineups(123)
    assert len(res) == 1
    assert res[0]['team']['name'] == 'Brasil'
    mock_cache_set.assert_called_once()
