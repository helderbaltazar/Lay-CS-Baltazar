import pytest
import os
import json
from unittest.mock import patch, MagicMock
from integration.layback import generate_layback_json, update_layback_bots, inject_teams_ui

def test_generate_layback_json(tmp_path):
    teams = [{"name": "Cruzeiro MG", "id": 1915199}]
    path = generate_layback_json(teams, "test_bot", output_dir=str(tmp_path))
    assert path == str(tmp_path / "test_bot.json")
    assert os.path.exists(path)
    with open(path, "r") as f:
        data = json.load(f)
    assert data["version"] == "1.0"
    assert data["betOnNewTeam"] is True
    assert len(data["teams"]) == 1
    assert data["teams"][0]["id"] == "1915199"


@patch("integration.layback.get_layback_session")
@patch("integration.layback.get_all_layback_teams")
@patch.dict(os.environ, {"GITHUB_ACTIONS": "true"})
def test_inject_teams_ui(mock_teams, mock_session, tmp_path):
    """Testa que inject_teams_ui usa a API REST correta (POST /api/bots/bulk/teams)."""
    json_file = tmp_path / "bot_0_1.json"
    json_file.write_text(json.dumps({
        "teams": [{"name": "Cruzeiro MG", "id": "1915199"}]
    }))
    mock_get_resp = MagicMock()
    mock_get_resp.status_code = 200
    mock_get_resp.json.return_value = {"data": {"bot": {"name": "Lay 0 a 1 lista"}}}
    mock_post_resp = MagicMock()
    mock_post_resp.status_code = 200
    mock_post_resp.json.return_value = {"data": {"count": 1}}
    mock_http = MagicMock()
    mock_http.get.return_value = mock_get_resp
    mock_http.post.return_value = mock_post_resp
    mock_session.return_value = (mock_http, [])
    mock_teams.return_value = [{"id": "1915199", "name": "Cruzeiro MG"}]
    result = inject_teams_ui(4626, str(json_file))
    assert result is True
    call_args = mock_http.post.call_args
    assert "bulk/teams" in call_args[0][0]
    payload = call_args[1]["json"]
    assert payload["ids"] == [4626]
    assert payload["teams"][0]["name"] == "Cruzeiro MG"
