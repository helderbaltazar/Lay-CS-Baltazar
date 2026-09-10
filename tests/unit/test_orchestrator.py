from analysis.orchestrator import MultiAgentOrchestrator

def test_consensus_approval():
    opinions = [
        {"veredito": "APROVADO", "risco_extremo": False, "confianca": 90, "motivo": "Ok"},
        {"veredito": "APROVADO", "risco_extremo": False, "confianca": 80, "motivo": "Ok"},
        {"veredito": "VETADO", "risco_extremo": False, "confianca": 40, "motivo": "Nao gosto"}
    ]
    result = MultiAgentOrchestrator.evaluate_match(opinions)
    assert result["verdict"] == "APROVADO"
    assert result["confidence"] == (90 + 80 + 40) // 3

def test_consensus_rejection():
    opinions = [
        {"veredito": "APROVADO", "risco_extremo": False, "confianca": 90, "motivo": "Ok"},
        {"veredito": "VETADO", "risco_extremo": False, "confianca": 40, "motivo": "Nao gosto"},
        {"veredito": "VETADO", "risco_extremo": False, "confianca": 30, "motivo": "Ruim"}
    ]
    result = MultiAgentOrchestrator.evaluate_match(opinions)
    assert result["verdict"] == "VETADO"
    assert result["critical_factor"] == "Falta de Consenso"

def test_absolute_veto():
    opinions = [
        {"veredito": "APROVADO", "risco_extremo": False, "confianca": 95, "motivo": "Ok"},
        {"veredito": "APROVADO", "risco_extremo": False, "confianca": 90, "motivo": "Ok"},
        {"veredito": "VETADO", "risco_extremo": True, "confianca": 0, "motivo": "Lesão do goleiro"}
    ]
    result = MultiAgentOrchestrator.evaluate_match(opinions)
    assert result["verdict"] == "VETADO"
    assert "VETO ABSOLUTO: Lesão do goleiro" in result["critical_factor"]
