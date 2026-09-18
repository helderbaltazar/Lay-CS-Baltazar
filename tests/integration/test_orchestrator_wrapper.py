"""
tests/integration/test_orchestrator_wrapper.py

Testa o OrchestratorAgent como wrapper fino em volta do run_real_injection.py.
Mocka as funções reais (ensure_data_in_db, inject_from_db) para validar
que o orquestrador delega corretamente sem reimplementar lógica.
"""
import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.integration
@pytest.mark.critical
class TestOrchestratorWrapper:
    """Valida que o orquestrador delega para run_real_injection corretamente."""

    @patch("agents.orchestrator.inject_from_db")
    @patch("agents.orchestrator.ensure_data_in_db")
    @patch("agents.orchestrator.check_api_status", return_value={"status": "healthy", "errors": []})
    @patch("agents.orchestrator.send_telegram_alert")
    @patch("agents.orchestrator.load_pending_from_cache", return_value=None)
    def test_full_pipeline_success(self, mock_cache, mock_telegram, mock_health, mock_ensure, mock_inject):
        """Pipeline completa delegada ao run_real_injection."""
        from agents.orchestrator import OrchestratorAgent

        mock_ensure.return_value = None
        mock_inject.return_value = {"injected": 5, "bots": 7}

        agent = OrchestratorAgent()
        exit_code = agent.run()

        assert exit_code == 0
        mock_ensure.assert_called_once()
        mock_inject.assert_called_once()

    @patch("agents.orchestrator.inject_from_db")
    @patch("agents.orchestrator.ensure_data_in_db")
    @patch("agents.orchestrator.check_api_status", return_value={"status": "degraded", "errors": ["datafootball: HTTP 500"]})
    @patch("agents.orchestrator.send_telegram_alert")
    @patch("agents.orchestrator.load_pending_from_cache", return_value=None)
    def test_pipeline_with_degraded_apis_still_runs(self, mock_cache, mock_telegram, mock_health, mock_ensure, mock_inject):
        """Pipeline continua mesmo com APIs degradadas (apenas avisa)."""
        from agents.orchestrator import OrchestratorAgent

        mock_inject.return_value = {"injected": 3, "bots": 7}

        agent = OrchestratorAgent()
        exit_code = agent.run()

        assert exit_code == 0
        mock_ensure.assert_called_once()
        mock_inject.assert_called_once()

    @patch("agents.orchestrator.inject_from_db")
    @patch("agents.orchestrator.ensure_data_in_db", side_effect=Exception("DataFootball timeout"))
    @patch("agents.orchestrator.check_api_status", return_value={"status": "healthy", "errors": []})
    @patch("agents.orchestrator.send_telegram_alert")
    @patch("agents.orchestrator.load_pending_from_cache", return_value=None)
    @patch("agents.orchestrator.write_incident_report")
    @patch("agents.orchestrator.abort_gracefully")
    def test_scanner_failure_aborts(self, mock_abort, mock_incident, mock_cache2, mock_telegram, mock_health, mock_ensure, mock_inject):
        """Se ensure_data_in_db falha, orquestrador alerta e aborta."""
        from agents.orchestrator import OrchestratorAgent

        agent = OrchestratorAgent()
        exit_code = agent.run()

        assert exit_code == 1
        mock_inject.assert_not_called()

    @patch("agents.orchestrator.inject_from_db", side_effect=Exception("LayBack 401"))
    @patch("agents.orchestrator.ensure_data_in_db")
    @patch("agents.orchestrator.check_api_status", return_value={"status": "healthy", "errors": []})
    @patch("agents.orchestrator.send_telegram_alert")
    @patch("agents.orchestrator.load_pending_from_cache", return_value=None)
    @patch("agents.orchestrator.write_incident_report")
    @patch("agents.orchestrator.abort_gracefully")
    def test_injection_failure_aborts(self, mock_abort, mock_incident, mock_cache2, mock_telegram, mock_health, mock_ensure, mock_inject):
        """Se inject_from_db falha, orquestrador alerta via Telegram."""
        from agents.orchestrator import OrchestratorAgent

        agent = OrchestratorAgent()
        exit_code = agent.run()

        assert exit_code == 1
        mock_ensure.assert_called_once()
