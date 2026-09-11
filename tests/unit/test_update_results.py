import pytest
from types import SimpleNamespace
from update_results import resolve_prediction

def test_lay_cs_classic_green():
    pred = SimpleNamespace(target_score='0-1')
    is_hit, profit = resolve_prediction(pred, '2-1')
    assert is_hit is True
    assert profit == 0.935

def test_lay_cs_classic_red():
    pred = SimpleNamespace(target_score='0-1')
    is_hit, profit = resolve_prediction(pred, '0-1')
    assert is_hit is False
    assert profit == -10.0

def test_under_05_ht_green():
    pred = SimpleNamespace(target_score='UNDER_0.5_HT')
    fixture_data = {'score': {'halftime': {'home': 1, 'away': 0}}}
    is_hit, profit = resolve_prediction(pred, '1-0', fixture_data)
    assert is_hit is True

def test_under_05_ht_red():
    pred = SimpleNamespace(target_score='UNDER_0.5_HT')
    fixture_data = {'score': {'halftime': {'home': 0, 'away': 0}}}
    is_hit, profit = resolve_prediction(pred, '0-0', fixture_data)
    assert is_hit is False

def test_under_15_ht_green():
    pred = SimpleNamespace(target_score='UNDER_1.5_HT')
    fixture_data = {'score': {'halftime': {'home': 1, 'away': 1}}}
    is_hit, profit = resolve_prediction(pred, '2-1', fixture_data)
    assert is_hit is True

def test_under_25_ht_green():
    pred = SimpleNamespace(target_score='UNDER_2.5_HT')
    fixture_data = {'score': {'halftime': {'home': 2, 'away': 1}}}
    is_hit, profit = resolve_prediction(pred, '3-1', fixture_data)
    assert is_hit is True

def test_under_market_no_ht_data():
    pred = SimpleNamespace(target_score='UNDER_0.5_HT')
    is_hit, profit = resolve_prediction(pred, '1-0', None)
    assert is_hit is None
    assert profit is None

def test_under_market_missing_halftime():
    pred = SimpleNamespace(target_score='UNDER_0.5_HT')
    fixture_data = {'score': {}}
    is_hit, profit = resolve_prediction(pred, '1-0', fixture_data)
    assert is_hit is None
    assert profit is None
