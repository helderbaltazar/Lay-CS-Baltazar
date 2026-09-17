"""
agents/orchestrator.py

Agente Orquestrador de Auto-Healing — Fase 5.
Substitui a chamada direta ao run_real_injection.py no GitHub Actions,
adicionando um loop de controle ReAct (Observe → Think → Act → Validate).

Modelo: Gemini 1.5 Pro (janela de 1M tokens para ler logs completos).
"""
import os
import sys
import time
import json
import datetime
import traceback
from agents.tools import (
    check_api_status,
    retry_for_duration,
    trigger_fallback_mode,
    refresh_layback_cookies,
    save_pending_to_cache,
    load_pending_from_cache,
    send_telegram_alert,
    write_incident_report,
    abort_gracefully,
)

# ── Constantes de configuração ──────────────────────────────────
MAX_RETRY_SECONDS = 600      # 10 minutos (aprovado pelo usuário)
HEARTBEAT_INTERVAL = 120     # emite heartbeat a cada 2 min
INCIDENT_LOG = "cache/orchestrator_incidents.jsonl"


class OrchestratorAgent:
    """
    Agente de Auto-Healing que executa a pipeline de injeção
    com capacidade de detectar, diagnosticar e remediar falhas em tempo real.
    """

    def __init__(self):
        self.incidents: list[dict] = []
        self.start_time = time.time()
        self.degraded_mode = False

    # ── Ponto de entrada principal ───────────────────────────────
    def run(self) -> int:
        """
        Executa a pipeline completa.
        Returns: 0 (sucesso) ou 1 (falha terminal).
        """
        print(f"[Orchestrator] 🚀 Iniciando pipeline — {_now()}")
        self._heartbeat("start")

        # ── Pré-check: dados pendentes da execução anterior ──────
        pending = load_pending_from_cache()
        if pending:
            print("[Orchestrator] 📦 Dados pendentes encontrados. Retomando injeção anterior...")
            send_telegram_alert(
                f"♻️ Retomando injeção pendente salva em {pending.get('saved_at', 'execução anterior')}.",
                level="info",
            )
            return self._run_injection(prefetched_matches=pending.get("matches"))

        # ── Fluxo normal ─────────────────────────────────────────
        return self._run_injection()

    # ── Fluxo principal de injeção com auto-healing ──────────────
    def _run_injection(self, prefetched_matches=None) -> int:
        try:
            # PASSO 1: Smoke Test de APIs externas
            print("[Orchestrator] 🔍 Verificando status das APIs externas...")
            health = check_api_status()
            if health["status"] == "degraded":
                for err in health["errors"]:
                    self._record_incident("api_check", err, action="warning_logged")
                send_telegram_alert(
                    f"⚠️ APIs degradadas antes da injeção: {health['errors']}",
                    level="warning",
                )

            # PASSO 2: Scanner de partidas (com retry de 10 min)
            matches = prefetched_matches
            if matches is None:
                print("[Orchestrator] 📡 Buscando partidas do dia...")
                matches = self._step_with_retry(
                    step_name="scanner",
                    fn=self._run_scanner,
                    on_total_failure=lambda e: self._handle_scanner_failure(e),
                )
                if matches is None:
                    return 1  # abort_gracefully já foi chamado internamente

            # PASSO 3: Análise de IA (com fallback automático para quota 429)
            print(f"[Orchestrator] 🤖 Analisando {len(matches)} partidas com IA...")
            analyzed = self._step_with_retry(
                step_name="ai_analysis",
                fn=lambda: self._run_ai_analysis(matches),
                on_total_failure=lambda e: self._handle_ai_failure(e, matches),
            )
            if analyzed is None:
                return 1

            # PASSO 4: Injeção no LayBack (com re-login automático)
            print("[Orchestrator] 💉 Iniciando injeção no LayBack...")
            injected = self._step_with_retry(
                step_name="layback_injection",
                fn=lambda: self._run_injection_step(analyzed),
                on_total_failure=lambda e: self._handle_injection_failure(e, analyzed),
            )
            if injected is None:
                return 1

            print(f"[Orchestrator] ✅ Pipeline concluída com sucesso! — {_now()}")
            send_telegram_alert(
                f"✅ Injeção concluída: {injected.get('injected', 0)} bots atualizados.",
                level="info",
            )
            return 0

        except Exception as e:
            tb = traceback.format_exc()
            print(f"[Orchestrator] 💥 Erro não tratado: {e}\n{tb}")
            abort_gracefully(f"Erro fatal não tratado: {e}")
            return 1

    # ── Step runner com retry de 10 minutos ─────────────────────
    def _step_with_retry(self, step_name: str, fn, on_total_failure) -> any:
        """
        Tenta executar `fn` por até 10 minutos.
        Em caso de timeout, chama `on_total_failure` e retorna None.
        """
        result = retry_for_duration(fn, max_seconds=MAX_RETRY_SECONDS, delay=30)
        if result is None:
            self._record_incident(step_name, "timeout após 10 min", action="escalated")
            on_total_failure(Exception(f"{step_name}: timeout após 10 min"))
            return None
        return result

    # ── Handlers de falha por passo (AGORA COM LLM) ──────────────
    def _handle_failure_with_ai(self, step_name: str, exc: Exception, data=None):
        """Envia para o Gemini SRE tentar resolver e retorna True se devemos tentar de novo agora."""
        import traceback
        from agents.react_agent import diagnose_and_heal
        
        tb_str = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        print(f"[Orchestrator] 🚨 Erro crítico em '{step_name}'. Acionando Agente SRE...")
        
        will_retry = diagnose_and_heal(step=step_name, error_msg=str(exc), traceback_str=tb_str)
        
        if will_retry:
            print(f"[Orchestrator] ♻️ Agente aplicou correção. O Orquestrador vai tentar o passo '{step_name}' novamente na próxima iteração.")
            return True
            
        # Agente não conseguiu resolver na hora -> salvar cache e abortar
        write_incident_report({"step": step_name, "error": str(exc), "resolved": False})
        save_pending_to_cache({"step": step_name, "saved_at": _now(), "matches": data})
        send_telegram_alert(
            f"🚨 SRE Agent não conseguiu curar a falha em '{step_name}': {str(exc)[:100]}\nDados salvos em cache.",
            level="critical",
        )
        return False

    def _handle_scanner_failure(self, exc: Exception):
        self._handle_failure_with_ai("scanner", exc)

    def _handle_ai_failure(self, exc: Exception, matches: list):
        self._handle_failure_with_ai("ai_analysis", exc, matches)

    def _handle_injection_failure(self, exc: Exception, analyzed: list):
        self._handle_failure_with_ai("layback_injection", exc, analyzed)


    # ── Sub-rotinas de execução dos passos reais ─────────────────
    def _run_scanner(self) -> list:
        """Chama o scanner real do projeto."""
        from data.data_manager import DataManager
        from analysis.scanner import scan_all
        dm = DataManager()
        fixtures = dm.get_fixtures()
        if not fixtures:
            raise ValueError("Scanner retornou 0 partidas.")
        return fixtures

    def _run_ai_analysis(self, matches: list) -> list:
        """Chama o analisador de IA (ou fallback se ativado)."""
        use_fallback = os.environ.get("USE_FALLBACK_ANALYSIS") == "1"
        from analysis.ai_analyst import AIAnalyst
        from analysis.scanner import scan_all, rank_by_target

        analyzed = []
        for match in matches:
            if use_fallback:
                result = AIAnalyst._fallback_analysis(match)
            else:
                result = AIAnalyst.analyze_match(match)
            analyzed.append(result)
        return analyzed

    def _run_injection_step(self, analyzed: list) -> dict:
        """Executa a injeção no LayBack."""
        # Importa e executa o fluxo de injeção existente
        import run_real_injection
        count = run_real_injection.run_injection(analyzed)
        return {"injected": count}

    # ── Utilitários ──────────────────────────────────────────────
    def _record_incident(self, step: str, error: str, action: str = "none"):
        incident = {"step": step, "error": error, "action": action}
        self.incidents.append(incident)
        write_incident_report(incident, log_path=INCIDENT_LOG)

    def _heartbeat(self, phase: str):
        elapsed = int(time.time() - self.start_time)
        print(f"[Orchestrator] 💓 heartbeat | fase={phase} | elapsed={elapsed}s")


def _now() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ── Entry point para o GitHub Actions ───────────────────────────
if __name__ == "__main__":
    agent = OrchestratorAgent()
    exit_code = agent.run()
    sys.exit(exit_code)
