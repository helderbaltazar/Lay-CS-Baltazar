"""Tests for Odds API client and DataManager fallback chain."""
import pytest
from unittest.mock import patch, MagicMock


# ============================================================
# Unit Tests: data/odds_api.py
# ============================================================

class TestOddsApiClient:
    """Tests for the Odds API client module."""

    SAMPLE_EVENTS = [
        {
            "id": "abc123",
            "sport_key": "soccer_brazil_serie_a",
            "sport_title": "Brasileirão Série A",
            "commence_time": "2026-09-03T21:00:00Z",
            "home_team": "Cruzeiro",
            "away_team": "Atletico Mineiro",
            "bookmakers": [
                {
                    "key": "betfair",
                    "title": "Betfair",
                    "markets": [
                        {
                            "key": "h2h",
                            "outcomes": [
                                {"name": "Cruzeiro", "price": 2.10},
                                {"name": "Atletico Mineiro", "price": 3.50},
                                {"name": "Draw", "price": 3.20}
                            ]
                        }
                    ]
                }
            ]
        },
        {
            "id": "def456",
            "sport_key": "soccer_brazil_serie_a",
            "sport_title": "Brasileirão Série A",
            "commence_time": "2026-09-03T23:00:00Z",
            "home_team": "Flamengo",
            "away_team": "Palmeiras",
            "bookmakers": []
        }
    ]

    @patch("data.odds_api.requests.get")
    def test_get_events_success(self, mock_get):
        """Should return events when API responds 200."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = self.SAMPLE_EVENTS
        mock_resp.headers = {"x-requests-remaining": "498"}
        mock_get.return_value = mock_resp

        from data.odds_api import get_events
        events = get_events("soccer_brazil_serie_a")
        assert len(events) == 2
        assert events[0]["home_team"] == "Cruzeiro"

    @patch("data.odds_api.requests.get")
    def test_get_events_failure(self, mock_get):
        """Should return empty list on API error."""
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.raise_for_status.side_effect = Exception("401 Unauthorized")
        mock_get.return_value = mock_resp

        from data.odds_api import get_events
        events = get_events("soccer_brazil_serie_a")
        assert events == []

    @patch("data.odds_api.cache.get")
    @patch("data.odds_api.requests.get")
    def test_get_fixtures_translates_to_api_football_format(self, mock_get, mock_cache):
        """Should translate Odds API events to API-Football fixture format."""
        mock_cache.return_value = None
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = self.SAMPLE_EVENTS
        mock_resp.headers = {"x-requests-remaining": "498"}
        mock_get.return_value = mock_resp

        from data.odds_api import get_fixtures
        fixtures = get_fixtures("2026-09-03")
        assert len(fixtures) >= 1
        f = fixtures[0]
        # Must have API-Football structure
        assert "fixture" in f
        assert "league" in f
        assert "teams" in f
        assert f["teams"]["home"]["name"] == "Cruzeiro"
        assert f["teams"]["away"]["name"] == "Atletico Mineiro"

    def test_sport_key_mapping_covers_main_leagues(self):
        """Ensure SPORT_KEYS covers the critical leagues."""
        from data.odds_api import SPORT_KEYS
        # Must cover at least Brasileirao, Premier League, La Liga
        sport_names = list(SPORT_KEYS.values())
        assert any("brazil" in k for k in SPORT_KEYS.keys())
        assert any("epl" in k or "england" in k for k in SPORT_KEYS.keys())
        assert any("spain" in k or "la_liga" in k for k in SPORT_KEYS.keys())

    @patch("data.odds_api.requests.get")
    def test_get_h2h_odds_extracts_correctly(self, mock_get):
        """Should extract H2H odds from bookmakers."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = self.SAMPLE_EVENTS
        mock_resp.headers = {"x-requests-remaining": "498"}
        mock_get.return_value = mock_resp

        from data.odds_api import get_h2h_odds
        odds = get_h2h_odds("soccer_brazil_serie_a")
        assert len(odds) >= 1
        first = odds[0]
        assert "home_odd" in first
        assert "away_odd" in first
        assert "draw_odd" in first
        assert first["home_odd"] == 2.10


# ============================================================
# Integration Tests: DataManager fallback chain
# ============================================================

class TestDataManagerFallbackChain:
    """Tests for the 3-level fallback in DataManager."""

    @patch("data.data_manager.api_get_fixtures", return_value=[{"fixture": {"id": 1}}])
    def test_primary_source_used_first(self, mock_api):
        """When API-Football works, should use it."""
        from data.data_manager import DataManager
        fixtures, source = DataManager.get_fixtures("2026-09-03")
        assert source == "API-Football"
        assert len(fixtures) == 1

    @patch("data.data_manager.odds_get_fixtures", return_value=[{"fixture": {"id": 3}}])
    @patch("data.data_manager.fd_get_fixtures", return_value=[])
    @patch("data.data_manager.api_get_fixtures", return_value=[])
    def test_falls_through_to_odds_api(self, mock_api, mock_fd, mock_odds):
        """When both API-Football and Football-Data fail, should use Odds API."""
        from data.data_manager import DataManager
        fixtures, source = DataManager.get_fixtures("2026-09-03")
        assert source == "Odds-API"
        assert len(fixtures) == 1

    @patch("data.data_manager.odds_get_fixtures", return_value=[])
    @patch("data.data_manager.fd_get_fixtures", return_value=[])
    @patch("data.data_manager.api_get_fixtures", return_value=[])
    def test_all_sources_fail_returns_empty(self, mock_api, mock_fd, mock_odds):
        """When all sources fail, should return empty list."""
        from data.data_manager import DataManager
        fixtures, source = DataManager.get_fixtures("2026-09-03")
        assert fixtures == []
        assert source is None
