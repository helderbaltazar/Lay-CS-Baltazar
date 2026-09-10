import json

class MultiAgentOrchestrator:
    @staticmethod
    def evaluate_match(opinions: list) -> dict:
        """
        Recebe uma lista de opiniões de agentes.
        opinion form: {"veredito": "APROVADO", "risco_extremo": False, "confianca": 85, "motivo": "..."}
        
        Regras de Consenso:
        1. Se qualquer agente tiver risco_extremo = True -> VETO ABSOLUTO
        2. Se 2 ou mais agentes aprovarem -> APROVADO
        3. Caso contrário -> VETADO
        """
        for op in opinions:
            if op.get("risco_extremo", False):
                return {
                    "veredito": "VETADO",
                    "confianca": 0,
                    "fator_critico": f"VETO ABSOLUTO: {op.get('motivo', 'Risco Extremo identificado')}",
                    "analise_detalhada": "Partida vetada devido a risco extremo identificado por um dos agentes."
                }
        
        aprovacoes = sum(1 for op in opinions if op.get("veredito") == "APROVADO")
        
        if aprovacoes >= 2:
            return {
                "veredito": "APROVADO",
                "confianca": sum(op.get("confianca", 0) for op in opinions) // len(opinions),
                "fator_critico": "Consenso Alcançado (>=2)",
                "analise_detalhada": "A maioria dos agentes aprovou a entrada."
            }
        else:
            return {
                "veredito": "VETADO",
                "confianca": 0,
                "fator_critico": "Falta de Consenso",
                "analise_detalhada": "Menos de 2 agentes aprovaram a entrada."
            }

