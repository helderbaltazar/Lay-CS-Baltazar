import os

with open('tests/unit/test_ai_analyst.py', 'r') as f:
    content = f.read()

old = "@patch('analysis.ai_analyst.api_football')"
new = "@patch('data.api_football.get_fixture_lineups')\n@patch('data.api_football.get_fixture_injuries')"
content = content.replace(old, new)

old_def = "def test_get_deep_match_analysis_with_fixture(mock_post, mock_api_football, monkeypatch):"
new_def = "def test_get_deep_match_analysis_with_fixture(mock_post, mock_inj, mock_lin, monkeypatch):"
content = content.replace(old_def, new_def)

old_mock = "mock_api_football.get_fixture_injuries.return_value = [{'player': {'name': 'Player1'}, 'type': 'Missing'}]"
new_mock = "mock_inj.return_value = [{'player': {'name': 'Player1'}, 'type': 'Missing'}]"
content = content.replace(old_mock, new_mock)

old_mock2 = "mock_api_football.get_fixture_lineups.return_value = [{'team': {'name': 'A'}, 'formation': '4-4-2'}]"
new_mock2 = "mock_lin.return_value = [{'team': {'name': 'A'}, 'formation': '4-4-2'}]"
content = content.replace(old_mock2, new_mock2)

with open('tests/unit/test_ai_analyst.py', 'w') as f:
    f.write(content)
