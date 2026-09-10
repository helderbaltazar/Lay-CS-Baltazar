import json

class MultiAgentOrchestrator:
    @staticmethod
    def evaluate_match(opinions: list) -> dict:
        for op in opinions:
            if op.get("risco_extremo", False):
                return {
                    "verdict": "VETADO",
                    "confidence": 0,
                    "critical_factor": f"VETO ABSOLUTO: {op.get('motivo', 'Risco Extremo identificado')}",
                    "detailed_analysis": "Partida vetada devido a risco extremo identificado por um dos agentes."
                }
        
        aprovacoes = sum(1 for op in opinions if op.get("veredito") == "APROVADO")
        
        if aprovacoes >= 2:
            return {
                "verdict": "APROVADO",
                "confidence": sum(op.get("confianca", 0) for op in opinions) // len(opinions),
                "critical_factor": "Consenso Alcançado (>=2)",
                "detailed_analysis": "A maioria dos agentes aprovou a entrada."
            }
        else:
            return {
                "verdict": "VETADO",
                "confidence": 0,
                "critical_factor": "Falta de Consenso",
                "detailed_analysis": "Menos de 2 agentes aprovaram a entrada."
            }
