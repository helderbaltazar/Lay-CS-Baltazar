import pytest
import os
from unittest.mock import patch, MagicMock
from integration.layback import generate_layback_json, update_layback_bots, inject_teams_ui

def test_generate_layback_json(tmp_path):
    teams = [{"name": "Cruzeiro MG", "id": 1915199}]
    path = generate_layback_json(teams, "test_bot", output_dir=str(tmp_path))
    assert path == str(tmp_path / "test_bot.json")
    
    import json
    import os
    assert os.path.exists(path)
    with open(path, "r") as f:
        data = json.load(f)
    assert data["version"] == "1.0"
    assert data["betOnNewTeam"] is True
    assert len(data["teams"]) == 1
    assert data["teams"][0]["id"] == "1915199"

@patch.dict(os.environ, {"GITHUB_ACTIONS": "true"})
@patch("integration.layback.time.sleep")
@patch("integration.layback.get_cookies_from_db")
@patch("integration.layback.sync_playwright")
def test_inject_teams_ui(mock_playwright, mock_db, mock_sleep):
    mock_play = MagicMock()
    mock_browser = MagicMock()
    mock_page = MagicMock()
    
    mock_playwright.return_value.__enter__.return_value = mock_play
    mock_play.chromium.launch.return_value = mock_browser
    
    mock_context = MagicMock()
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page

    
    # Simulate count > 0 to pass conditionals
    mock_locator = MagicMock()
    mock_locator.count.return_value = 1
    mock_page.locator.return_value = mock_locator
    
    result = inject_teams_ui(4626, "data/test_bot.json")
    
    # Check that it tried to save
    assert result is True
    mock_page.goto.assert_any_call("https://bot-betfair.layback.trade/bots/4626/edit", wait_until="networkidle")
