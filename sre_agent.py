import os

class SREObserver:
    @staticmethod
    def analyze_logs(log_path="debug.log"):
        """
        Le as ultimas linhas do log para procurar anomalias continuas.
        Fase 5 - Auto-Healing SRE
        """
        if not os.path.exists(log_path):
            return {"status": "ok", "action": "none"}
            
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()[-100:]
            
        error_count = sum(1 for line in lines if "error" in line.lower() or "timeout" in line.lower())
        api_odds_failures = sum(1 for line in lines if "falha" in line.lower() and "odds" in line.lower())
        
        if api_odds_failures >= 3:
            return {
                "status": "critical",
                "action": "disable_odds_api",
                "reason": f"Detectadas {api_odds_failures} falhas consecutivas na captura de Odds."
            }
        
        if error_count > 10:
            return {
                "status": "warning",
                "action": "alert_admin",
                "reason": f"Alta taxa de erros ({error_count} em 100 linhas)."
            }
            
        return {"status": "ok", "action": "none"}
