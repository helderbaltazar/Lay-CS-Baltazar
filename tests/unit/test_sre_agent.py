import os
from sre_agent import SREObserver

def test_sre_detects_odds_failure(tmp_path):
    log_file = tmp_path / "fake_debug.log"
    content = ""
    for _ in range(97):
        content += "INFO: Sistema rodando normalmente\n"
    for _ in range(3):
        content += "ERROR: Falha ao buscar Odds na API\n"
        
    log_file.write_text(content)
    
    result = SREObserver.analyze_logs(str(log_file))
    
    assert result["status"] == "critical"
    assert result["action"] == "disable_odds_api"

def test_sre_normal_operation(tmp_path):
    log_file = tmp_path / "fake_debug.log"
    content = "INFO: Iniciando scan...\n" * 50
    log_file.write_text(content)
    
    result = SREObserver.analyze_logs(str(log_file))
    
    assert result["status"] == "ok"
    assert result["action"] == "none"

def test_sre_missing_log():
    result = SREObserver.analyze_logs("non_existent_log_123.log")
    assert result["status"] == "ok"
    assert result["action"] == "none"
