"""
tests/unit/test_orchestrator_tools.py

Testes TDD para as ferramentas de remediação do Agente Orquestrador.
Todos os testes devem estar passando ANTES de qualquer implementação real.
"""
import pytest
import time
from unittest.mock import patch, MagicMock


# ─────────────────────────────────────────────────────────────
# check_api_status
# ─────────────────────────────────────────────────────────────
class TestCheckApiStatus:
    def test_all_ok_returns_healthy(self):
        from agents.tools import check_api_status
        with patch("agents.tools.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_get.return_value = mock_resp
            result = check_api_status()
        assert result["status"] == "healthy"
        assert result["errors"] == []

    def test_datafootball_down_returns_degraded(self):
        from agents.tools import check_api_status
        def side_effect(url, **kwargs):
            if "datafootball" in url:
                raise ConnectionError("timeout")
            m = MagicMock(); m.status_code = 200; return m
        with patch("agents.tools.requests.get", side_effect=side_effect):
            result = check_api_status()
        assert result["status"] == "degraded"
        assert any("datafootball" in e.lower() for e in result["errors"])

    def test_layback_down_returns_degraded(self):
        from agents.tools import check_api_status
        def side_effect(url, **kwargs):
            if "layback" in url or "bolsa.bet.br" in url:
                raise ConnectionError("timeout")
            m = MagicMock(); m.status_code = 200; return m
        with patch("agents.tools.requests.get", side_effect=side_effect):
            result = check_api_status()
        assert result["status"] == "degraded"
        assert any("layback" in e.lower() for e in result["errors"])


# ─────────────────────────────────────────────────────────────
# retry_with_backoff
# ─────────────────────────────────────────────────────────────
class TestRetryWithBackoff:
    def test_succeeds_on_first_try(self):
        from agents.tools import retry_with_backoff
        fn = MagicMock(return_value="ok")
        assert retry_with_backoff(fn, max_retries=3, delay=0) == "ok"
        assert fn.call_count == 1

    def test_retries_on_exception_then_succeeds(self):
        from agents.tools import retry_with_backoff
        fn = MagicMock(side_effect=[Exception("fail"), Exception("fail"), "ok"])
        assert retry_with_backoff(fn, max_retries=3, delay=0) == "ok"
        assert fn.call_count == 3

    def test_raises_after_max_retries(self):
        from agents.tools import retry_with_backoff
        fn = MagicMock(side_effect=Exception("always fails"))
        with pytest.raises(Exception, match="always fails"):
            retry_with_backoff(fn, max_retries=3, delay=0)
        assert fn.call_count == 3

    def test_respects_delay_between_attempts(self):
        from agents.tools import retry_with_backoff
        fn = MagicMock(side_effect=[Exception("fail"), "ok"])
        start = time.time()
        retry_with_backoff(fn, max_retries=2, delay=0.05)
        assert time.time() - start >= 0.05


# ─────────────────────────────────────────────────────────────
# trigger_fallback_mode
# ─────────────────────────────────────────────────────────────
class TestTriggerFallbackMode:
    def test_sets_env_var(self):
        import os
        from agents.tools import trigger_fallback_mode
        trigger_fallback_mode()
        assert os.environ.get("USE_FALLBACK_ANALYSIS") == "1"

    def test_returns_activated_status(self):
        from agents.tools import trigger_fallback_mode
        result = trigger_fallback_mode()
        assert result["action"] == "fallback_activated"


# ─────────────────────────────────────────────────────────────
# send_telegram_alert
# ─────────────────────────────────────────────────────────────
class TestSendTelegramAlert:
    def test_sends_message_successfully(self):
        from agents.tools import send_telegram_alert
        with patch("agents.tools.requests.post") as mock_post, \
             patch.dict("os.environ", {"TELEGRAM_BOT_TOKEN": "fake-token", "TELEGRAM_CHAT_ID": "123"}):
            mock_post.return_value.status_code = 200
            result = send_telegram_alert("Test alert", level="warning")
        assert result["sent"] is True

    def test_does_not_raise_if_telegram_fails(self):
        from agents.tools import send_telegram_alert
        with patch("agents.tools.requests.post", side_effect=Exception("network error")), \
             patch.dict("os.environ", {"TELEGRAM_BOT_TOKEN": "fake-token", "TELEGRAM_CHAT_ID": "123"}):
            result = send_telegram_alert("Test alert", level="critical")
        assert result["sent"] is False

    def test_message_includes_level(self):
        from agents.tools import send_telegram_alert
        with patch("agents.tools.requests.post") as mock_post, \
             patch.dict("os.environ", {"TELEGRAM_BOT_TOKEN": "fake-token", "TELEGRAM_CHAT_ID": "123"}):
            mock_post.return_value.status_code = 200
            send_telegram_alert("Something broke", level="critical")
        payload = mock_post.call_args[1].get("json") or mock_post.call_args[0][1]
        assert "critical" in payload["text"].lower()


# ─────────────────────────────────────────────────────────────
# write_incident_report
# ─────────────────────────────────────────────────────────────
class TestWriteIncidentReport:
    def test_saves_json_to_log_file(self, tmp_path):
        import json
        from agents.tools import write_incident_report
        log_path = tmp_path / "incidents.jsonl"
        write_incident_report({"step": "scanner", "error": "HTTP 503"}, log_path=str(log_path))
        lines = log_path.read_text().strip().splitlines()
        assert len(lines) == 1
        saved = json.loads(lines[0])
        assert saved["step"] == "scanner"
        assert "ts" in saved

    def test_appends_to_existing_file(self, tmp_path):
        from agents.tools import write_incident_report
        log_path = tmp_path / "incidents.jsonl"
        write_incident_report({"step": "a"}, log_path=str(log_path))
        write_incident_report({"step": "b"}, log_path=str(log_path))
        assert len(log_path.read_text().strip().splitlines()) == 2


# ─────────────────────────────────────────────────────────────
# abort_gracefully
# ─────────────────────────────────────────────────────────────
class TestAbortGracefully:
    def test_returns_abort_payload(self):
        from agents.tools import abort_gracefully
        with patch("agents.tools.send_telegram_alert"):
            result = abort_gracefully("Supabase offline")
        assert result["aborted"] is True
        assert "Supabase offline" in result["reason"]

    def test_sends_alert_before_aborting(self):
        from agents.tools import abort_gracefully
        with patch("agents.tools.send_telegram_alert") as mock_alert:
            abort_gracefully("critical failure")
        mock_alert.assert_called_once()
