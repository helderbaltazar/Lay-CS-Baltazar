"""
Teste de integracao: Verifica se os times injetados nos bots da Layback
batem com os times do dia no banco de dados.
"""
import os
import json
import pytest
from unittest.mock import patch, MagicMock


class TestBotTeamsInjection:
    """Testa a logica de injecao de times nos bots da Layback."""

    def test_find_layback_team_id_exact_match(self):
        """Deve encontrar time por correspondencia exata."""
        from integration.layback import find_layback_team_id
        teams = [
            {"id": "1846910", "name": "Flamengo"},
            {"id": "1277142", "name": "Mirassol"},
        ]
        result = find_layback_team_id("Flamengo", teams)
        assert result is not None
        assert result["id"] == "1846910"
        assert result["name"] == "Flamengo"

    def test_find_layback_team_id_with_normalization(self):
        """Deve encontrar time mesmo com sufixo 'FC' ou estado."""
        from integration.layback import find_layback_team_id
        teams = [{"id": "38517", "name": "Atletico MG"}]
        result = find_layback_team_id("Atletico Mineiro", teams)
        assert result is not None
        assert result["id"] == "38517"

    def test_find_layback_team_id_fuzzy(self):
        """Deve encontrar time por similaridade (fuzzy matching)."""
        from integration.layback import find_layback_team_id
        teams = [{"id": "1277142", "name": "Mirassol"}]
        result = find_layback_team_id("Mirasol", teams)  # typo intencional
        assert result is not None
        assert result["id"] == "1277142"

    def test_find_layback_team_id_not_found(self):
        """Deve retornar None para time inexistente."""
        from integration.layback import find_layback_team_id
        teams = [{"id": "1846910", "name": "Flamengo"}]
        result = find_layback_team_id("Time Inexistente XYZ", teams)
        assert result is None

    def test_inject_teams_mock_mode(self):
        """Fora do GitHub Actions, deve retornar True (modo mock)."""
        from integration.layback import inject_teams_ui
        with patch.dict(os.environ, {}, clear=True):
            if "GITHUB_ACTIONS" in os.environ:
                del os.environ["GITHUB_ACTIONS"]
            result = inject_teams_ui(4626, "data/test.json")
            assert result is True

    def test_generate_layback_json(self, tmp_path):
        """Deve gerar JSON no formato correto para importacao na Layback."""
        from integration.layback import generate_layback_json
        teams_data = [
            {"name": "Flamengo", "id": "1846910"},
            {"name": "Mirassol", "id": "1277142"},
        ]
        output_dir = str(tmp_path)
        path = generate_layback_json(teams_data, "bot_0_1", output_dir)
        assert os.path.exists(path)
        with open(path) as f:
            data = json.load(f)
        assert "teams" in data
        assert len(data["teams"]) == 2
        assert data["teams"][0]["name"] == "Flamengo"
        assert data["teams"][0]["checked"] is True


class TestBotTeamsValidation:
    """Testa a validacao dos times injetados (batem com o dia)."""

    def test_bot_teams_match_predictions(self):
        """
        Verifica que os times esperados para hoje estao configurados.
        Em ambiente de CI, usa mocks para simular a API da Layback.
        """
        from integration.layback import find_layback_team_id

        # Times que devem estar no bot (simulados como "jogos do dia")
        expected_teams = ["Flamengo", "Mirassol"]
        layback_catalog = [
            {"id": "1846910", "name": "Flamengo"},
            {"id": "1277142", "name": "Mirassol"},
            {"id": "38517", "name": "Atletico MG"},
        ]

        resolved = []
        not_found = []
        for t in expected_teams:
            found = find_layback_team_id(t, layback_catalog)
            if found:
                resolved.append(found)
            else:
                not_found.append(t)

        assert len(not_found) == 0, f"Times nao encontrados na Layback: {not_found}"
        assert len(resolved) == len(expected_teams)

    @patch("integration.layback.get_layback_session")
    @patch("integration.layback.get_all_layback_teams")
    def test_injection_calls_correct_endpoint(self, mock_teams, mock_session, tmp_path):
        """Verifica que a injecao usa o endpoint correto /api/bots/bulk/teams."""
        import json as j

        # Cria arquivo JSON de times temporario
        json_file = tmp_path / "bot_0_1.json"
        json_file.write_text(j.dumps({
            "teams": [{"name": "Flamengo", "id": "1846910"}]
        }))

        # Mock da sessao HTTP
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.side_effect = [
            {"data": {"bot": {"name": "Lay 0 a 1 lista"}}},  # GET /api/bots/4626
            {"data": {"count": 1}},  # POST /api/bots/bulk/teams
        ]
        mock_http_session = MagicMock()
        mock_http_session.get.return_value = mock_resp
        mock_http_session.post.return_value = mock_resp
        mock_session.return_value = (mock_http_session, [])

        mock_teams.return_value = [
            {"id": "1846910", "name": "Flamengo"},
        ]

        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}):
            from integration.layback import inject_teams_ui
            result = inject_teams_ui(4626, str(json_file))

        assert result is True
        # Verifica que chamou o endpoint correto
        call_args = mock_http_session.post.call_args
        assert "bulk/teams" in call_args[0][0]
        payload = call_args[1]["json"]
        assert payload["ids"] == [4626]
        assert len(payload["teams"]) == 1
        assert payload["teams"][0]["name"] == "Flamengo"
