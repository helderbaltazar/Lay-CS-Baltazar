"""
agents/tools.py

Ferramentas de remediação do Agente Orquestrador (Auto-Healing SRE).
Cada função é independente e testável de forma isolada.

Decisões de design aprovadas pelo usuário:
  - Re-login automático no LayBack: APROVADO
  - Supabase offline: retry por até 10 min → salva em cache/ + Telegram
"""
import json
import os
import time
import datetime
import requests
import config

# ────────────────────────────────────────────────────────────────
# 1. check_api_status
# ────────────────────────────────────────────────────────────────
ENDPOINTS = {
    "datafootball": "https://webhook.datafootball.com.br/webhook/matches_day",
    "layback": "https://api.layback.com.br",
}

def check_api_status(timeout: int = 5) -> dict:
    """
    Pinga os endpoints externos e retorna health status.
    Returns: {"status": "healthy"|"degraded", "errors": [...]}
    """
    errors = []
    
    # Configurar proxy se existir no ambiente
    proxies = None
    proxy_server = os.getenv("PROXY_SERVER")
    if proxy_server:
        proxy_user = os.getenv("PROXY_USERNAME")
        proxy_pass = os.getenv("PROXY_PASSWORD")
        if proxy_user and proxy_pass:
            auth_url = f"http://{proxy_user}:{proxy_pass}@{proxy_server}"
            proxies = {"http": auth_url, "https": auth_url}
        else:
            proxies = {"http": f"http://{proxy_server}", "https": f"http://{proxy_server}"}

    for name, url in ENDPOINTS.items():
        try:
            resp = requests.get(url, timeout=timeout, proxies=proxies)
            if resp.status_code >= 500:
                errors.append(f"{name}: HTTP {resp.status_code}")
        except Exception as e:
            errors.append(f"{name}: {str(e)[:80]}")

    return {
        "status": "degraded" if errors else "healthy",
        "errors": errors,
        "checked_at": _now_iso(),
    }


# ────────────────────────────────────────────────────────────────
# 2. retry_with_backoff
# ────────────────────────────────────────────────────────────────
def retry_with_backoff(fn, max_retries: int = 3, delay: float = 2.0, backoff: float = 2.0):
    """
    Tenta executar `fn` até `max_retries` vezes com delay exponencial.
    Levanta a última exceção se todas as tentativas falharem.
    """
    last_exc = None
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as e:
            last_exc = e
            if attempt < max_retries - 1:
                sleep_time = delay * (backoff ** attempt)
                time.sleep(sleep_time)
    raise last_exc


# ────────────────────────────────────────────────────────────────
# 3. retry_for_duration (até 10 minutos)
# ────────────────────────────────────────────────────────────────
def retry_for_duration(fn, max_seconds: int = 600, delay: float = 30.0):
    """
    Tenta executar `fn` repetidamente por até `max_seconds` segundos.
    Se não conseguir no prazo, salva os dados pendentes e alerta.
    Returns: resultado de fn() ou None em caso de timeout.
    """
    deadline = time.time() + max_seconds
    attempt = 0
    last_exc = None

    while time.time() < deadline:
        attempt += 1
        try:
            result = fn()
            print(f"[Orchestrator] ✅ Sucesso na tentativa {attempt}.")
            return result
        except Exception as e:
            last_exc = e
            remaining = int(deadline - time.time())
            print(f"[Orchestrator] ⚠️ Tentativa {attempt} falhou: {e}. "
                  f"Tentando novamente em {delay}s... ({remaining}s restantes)")
            if time.time() + delay < deadline:
                time.sleep(delay)

    # Timeout — salva estado pendente e alerta
    msg = (f"⛔ Orquestrador: timeout após {max_seconds // 60} min. "
           f"Última falha: {str(last_exc)[:200]}")
    print(f"[Orchestrator] {msg}")
    send_telegram_alert(msg, level="critical")
    return None


# ────────────────────────────────────────────────────────────────
# 4. trigger_fallback_mode
# ────────────────────────────────────────────────────────────────
def trigger_fallback_mode() -> dict:
    """
    Ativa o modo de análise estatística pura (sem IA).
    Sinaliza via variável de ambiente para run_real_injection.py.
    """
    os.environ["USE_FALLBACK_ANALYSIS"] = "1"
    print("[Orchestrator] 🔄 Modo de fallback estatístico ativado.")
    return {"action": "fallback_activated", "ts": _now_iso()}


# ────────────────────────────────────────────────────────────────
# 5. refresh_layback_cookies (re-login automático APROVADO)
# ────────────────────────────────────────────────────────────────
def refresh_layback_cookies() -> dict:
    """
    Re-faz o login no LayBack usando Playwright e salva os novos cookies no banco.
    Aprovado pelo usuário como ação automática do orquestrador.
    """
    try:
        from scripts.verify_cookies import verify
        from integration.layback import do_login_and_save_cookies
        print("[Orchestrator] 🔑 Tentando re-login automático no LayBack...")
        do_login_and_save_cookies()
        verify()
        print("[Orchestrator] ✅ Cookies do LayBack renovados com sucesso.")
        return {"action": "cookies_refreshed", "success": True, "ts": _now_iso()}
    except Exception as e:
        print(f"[Orchestrator] ❌ Falha no re-login: {e}")
        return {"action": "cookies_refreshed", "success": False, "error": str(e), "ts": _now_iso()}


# ────────────────────────────────────────────────────────────────
# 6. save_pending_to_cache  (comportamento para Supabase offline)
# ────────────────────────────────────────────────────────────────
PENDING_CACHE_PATH = "cache/orchestrator_pending.json"

def save_pending_to_cache(data: dict) -> dict:
    """
    Salva dados pendentes em cache/ para ser recuperado na próxima execução.
    O GitHub Actions já persiste a pasta cache/ entre runs via actions/cache.
    """
    os.makedirs("cache", exist_ok=True)
    payload = {
        "ts": _now_iso(),
        "data": data,
    }
    with open(PENDING_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"[Orchestrator] 💾 Dados pendentes salvos em {PENDING_CACHE_PATH}")
    return {"action": "saved_to_cache", "path": PENDING_CACHE_PATH, "ts": _now_iso()}


def load_pending_from_cache() -> dict | None:
    """
    Recupera dados pendentes salvos pela execução anterior.
    Retorna None se não houver nada pendente.
    """
    if not os.path.exists(PENDING_CACHE_PATH):
        return None
    with open(PENDING_CACHE_PATH, "r", encoding="utf-8") as f:
        payload = json.load(f)
    print(f"[Orchestrator] 🔍 Dados pendentes encontrados (salvos em {payload.get('ts')}).")
    os.remove(PENDING_CACHE_PATH)  # consume e remove para não reprocessar infinitamente
    return payload.get("data")


# ────────────────────────────────────────────────────────────────
# 7. send_telegram_alert
# ────────────────────────────────────────────────────────────────
def send_telegram_alert(message: str, level: str = "warning") -> dict:
    """
    Envia uma mensagem para o canal Telegram configurado.
    Nunca lança exceção — notificação é best-effort.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN") or getattr(config, "TELEGRAM_BOT_TOKEN", None)
    chat_id = os.getenv("TELEGRAM_CHAT_ID") or getattr(config, "TELEGRAM_CHAT_ID", None)

    if not token or not chat_id:
        print("[Orchestrator] ⚠️ Telegram não configurado. Pulando alerta.")
        return {"sent": False, "reason": "no_credentials"}

    level_emoji = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨"}.get(level.lower(), "🔔")
    text = f"{level_emoji} *[Orquestrador Lay CS]* — {level.upper()}\n\n{message}"

    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        resp = requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}, timeout=10)
        return {"sent": resp.status_code == 200}
    except Exception as e:
        print(f"[Orchestrator] Falha ao enviar Telegram: {e}")
        return {"sent": False, "reason": str(e)}


# ────────────────────────────────────────────────────────────────
# 8. write_incident_report
# ────────────────────────────────────────────────────────────────
DEFAULT_LOG = "cache/orchestrator_incidents.jsonl"

def write_incident_report(report: dict, log_path: str = DEFAULT_LOG) -> dict:
    """
    Appenda uma linha JSON ao log de incidentes estruturado.
    Compatível com o log do GitHub Actions (visível nos artefatos).
    """
    os.makedirs(os.path.dirname(log_path) if os.path.dirname(log_path) else ".", exist_ok=True)
    record = {"ts": _now_iso(), **report}
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return {"logged": True, "path": log_path}


# ────────────────────────────────────────────────────────────────
# 9. abort_gracefully
# ────────────────────────────────────────────────────────────────
def abort_gracefully(reason: str) -> dict:
    """
    Para a execução de forma limpa, envia alerta e registra incidente.
    Nunca deixa estado sujo no banco.
    """
    print(f"[Orchestrator] 🛑 Abortando: {reason}")
    send_telegram_alert(f"Pipeline abortada: {reason}", level="critical")
    write_incident_report({"event": "abort", "reason": reason})
    return {"aborted": True, "reason": reason, "ts": _now_iso()}


# ────────────────────────────────────────────────────────────────
# Utilitários internos
# ────────────────────────────────────────────────────────────────
def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()
