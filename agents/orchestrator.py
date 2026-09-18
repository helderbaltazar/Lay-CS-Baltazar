"""
agents/orchestrator.py

Agente Orquestrador de Auto-Healing — Fase 5.
Wrapper fino em volta do run_real_injection.py, adicionando:
- Health check de APIs antes de iniciar
- Auto-healing via Gemini 1.5 Pro (ReAct) em caso de falha
- Cache de dados pendentes entre execuções
- Alertas Telegram em cada etapa
- Retry com backoff de 10 minutos

Modelo SRE: Gemini 1.5 Pro (janela de 1M tokens para ler logs completos).
"""
import os
import sys
import time
import json
import datetime
import traceback as tb_module

from run_real_injection import ensure_data_in_db, inject_from_db
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
    delegando para run_real_injection.py (wrapper fino).
    Detecta, diagnostica e remedia falhas em tempo real.
    """

    def __init__(self):
        self.incidents: list[dict] = []
        self.start_time = time.time()

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

        try:
            # ── PASSO 1: Health check de APIs externas ───────────
            print("[Orchestrator] 🔍 Verificando status das APIs externas...")
            health = check_api_status()
            if health["status"] == "degraded":
                for err in health["errors"]:
                    self._record_incident("api_check", err, action="warning_logged")
                send_telegram_alert(
                    f"⚠️ APIs degradadas antes da injeção: {health['errors']}",
                    level="warning",
                )

            # ── PASSO 2: Scanner + IA (delegado ao run_real_injection) ──
            print("[Orchestrator] 📡 Executando scanner + análise IA...")
            self._heartbeat("ensure_data")
            ensure_data_in_db()
            print("[Orchestrator] ✅ Scanner e IA concluídos.")

            # ── PASSO 3: Injeção nos bots LayBack ────────────────
            print("[Orchestrator] 💉 Iniciando injeção no LayBack...")
            self._heartbeat("inject")
            result = inject_from_db()

            print(f"[Orchestrator] ✅ Pipeline concluída com sucesso! — {_now()}")
            send_telegram_alert(
                f"✅ Injeção diária concluída com sucesso às {_now()}.",
                level="info",
            )
            return 0

        except Exception as e:
            return self._handle_pipeline_failure(e)

    # ── Handler de falha com Auto-Healing via LLM ────────────────
    def _handle_pipeline_failure(self, exc: Exception) -> int:
        """
        Tenta auto-healing via Gemini 1.5 Pro.
        Se não resolver, salva estado em cache e alerta.
        """
        tb_str = tb_module.format_exc()
        error_msg = str(exc)
        print(f"[Orchestrator] 🚨 Falha na pipeline: {error_msg}")

        # Registrar incidente
        self._record_incident("pipeline", error_msg, action="sre_invoked")

        # Tentar auto-healing via Gemini SRE
        try:
            from agents.react_agent import diagnose_and_heal
            print("[Orchestrator] 🧠 Acionando Agente SRE (Gemini 1.5 Pro)...")
            will_retry = diagnose_and_heal(
                step="pipeline",
                error_msg=error_msg,
                traceback_str=tb_str,
            )

            if will_retry:
                print("[Orchestrator] ♻️ SRE aplicou correção. Re-executando pipeline...")
                try:
                    ensure_data_in_db()
                    inject_from_db()
                    print(f"[Orchestrator] ✅ Pipeline recuperada com sucesso! — {_now()}")
                    send_telegram_alert(
                        f"✅ Pipeline recuperada pelo SRE Agent às {_now()}.",
                        level="info",
                    )
                    return 0
                except Exception as retry_exc:
                    print(f"[Orchestrator] ❌ Re-tentativa também falhou: {retry_exc}")
                    error_msg = str(retry_exc)
                    tb_str = tb_module.format_exc()

        except Exception as sre_exc:
            print(f"[Orchestrator] ⚠️ SRE Agent indisponível: {sre_exc}")

        # SRE não resolveu → salvar estado e abortar graciosamente
        write_incident_report({"step": "pipeline", "error": error_msg, "resolved": False})
        send_telegram_alert(
            f"🚨 Pipeline falhou e SRE não conseguiu curar:\n{error_msg[:200]}\n\nAbortando graciosamente.",
            level="critical",
        )
        abort_gracefully(f"Pipeline falhou: {error_msg[:100]}")
        return 1

    # ── Utilitários ──────────────────────────────────────────────
    def _record_incident(self, step: str, error: str, action: str = "none"):
        incident = {"step": step, "error": error, "action": action, "ts": _now()}
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
