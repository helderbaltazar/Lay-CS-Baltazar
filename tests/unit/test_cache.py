import os
import time
import pytest
from data import cache

@pytest.fixture(autouse=True)
def run_around_tests():
    # Substitui arquivo de cache para testes
    original_file = cache.CACHE_FILE
    cache.CACHE_FILE = "cache/test_cache.json"
    if os.path.exists(cache.CACHE_FILE):
        os.remove(cache.CACHE_FILE)
    
    yield # Executa teste
    
    # Teardown
    if os.path.exists(cache.CACHE_FILE):
        os.remove(cache.CACHE_FILE)
    cache.CACHE_FILE = original_file

def test_set_and_get():
    cache.set("team_1", {"goals": 10})
    val = cache.get("team_1")
    assert val is not None
    assert val["goals"] == 10

def test_get_nonexistent():
    assert cache.get("missing") is None

def test_expired_cache(monkeypatch):
    cache.set("team_2", {"goals": 5})
    # Mock do time para simular 4 dias no futuro
    future_time = time.time() + (4 * 24 * 60 * 60)
    monkeypatch.setattr(time, "time", lambda: future_time)
    assert cache.get("team_2") is None

def test_invalidate():
    cache.set("team_3", {"goals": 2})
    assert cache.get("team_3") is not None
    cache.invalidate("team_3")
    assert cache.get("team_3") is None
