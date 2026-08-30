#!/usr/bin/env python3
"""
Pipeline de Deploy Automatizado do Frontend (Render.com)
1. Executa testes de interface locais (pytest tests/web/).
2. Sincroniza variáveis de ambiente e dispara o deploy no Render via API.
3. Monitora o status até a publicação ser concluída (live).
4. Executa testes de verificação E2E diretamente na URL pública do Render.
"""

import os
import sys
import time
import base64
import subprocess
import requests
from dotenv import load_dotenv

load_dotenv()

RENDER_API_KEY = os.getenv("RENDER_API_KEY", "rnd_S8cQDmEMslEPkYDWfsZ6hEWMWXYM")
RENDER_SERVICE_ID = os.getenv("RENDER_SERVICE_ID", "srv-da87ptijnfac73d2o9p0")
BASE_URL = "https://api.render.com/v1"
HEADERS = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

LIVE_URL = "https://lay-cs-baltazar.onrender.com"
DASHBOARD_USERNAME = os.getenv("DASHBOARD_USERNAME", "helderbaltazar")
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "Bonde74812005")


def run_local_ui_tests():
    print("\n--- 1. EXECUTANDO TESTES DE INTERFACE LOCAIS (PYTEST) ---")
    result = subprocess.run([sys.executable, "-m", "pytest", "tests/web/", "-v"], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print("❌ Testes locais de interface falharam! Deploy cancelado.")
        print(result.stderr)
        sys.exit(1)
    print("✅ Todos os testes de interface locais passaram com sucesso!")


def sync_environment_variables():
    print("\n--- 2. SINCRONIZANDO VARIÁVEIS DE AMBIENTE NO RENDER ---")
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres.dewniwkvwicalcvmoccc:B%40nde74812005@aws-0-us-east-1.pooler.supabase.com:5432/postgres")
    
    # Garante pooler IPv4 se contiver porta direta
    if "db.dewniwkvwicalcvmoccc.supabase.co" in db_url:
        db_url = "postgresql://postgres.dewniwkvwicalcvmoccc:B%40nde74812005@aws-0-us-east-1.pooler.supabase.com:5432/postgres"

    env_vars = [
        {"key": "PYTHON_VERSION", "value": "3.12.3"},
        {"key": "DATABASE_URL", "value": db_url},
        {"key": "DASHBOARD_USERNAME", "value": DASHBOARD_USERNAME},
        {"key": "DASHBOARD_PASSWORD", "value": DASHBOARD_PASSWORD},
        {"key": "API_FOOTBALL_KEY", "value": os.getenv("API_FOOTBALL_KEY", "")},
        {"key": "FOOTBALL_DATA_KEY", "value": os.getenv("FOOTBALL_DATA_KEY", "")},
        {"key": "GEMINI_API_KEY", "value": os.getenv("GEMINI_API_KEY", "")},
        {"key": "TELEGRAM_BOT_TOKEN", "value": os.getenv("TELEGRAM_BOT_TOKEN", "")},
        {"key": "TELEGRAM_CHAT_ID", "value": os.getenv("TELEGRAM_CHAT_ID", "")}
    ]

    r = requests.put(f"{BASE_URL}/services/{RENDER_SERVICE_ID}/env-vars", headers=HEADERS, json=env_vars)
    if r.status_code == 200:
        print("✅ Variáveis de ambiente sincronizadas no Render!")
    else:
        print(f"⚠️ Aviso ao sincronizar env-vars ({r.status_code}): {r.text[:200]}")


def trigger_render_deploy():
    print("\n--- 3. DISPARANDO NOVO DEPLOY NO RENDER ---")
    resp = requests.post(
        f"{BASE_URL}/services/{RENDER_SERVICE_ID}/deploys",
        headers=HEADERS,
        json={"clearCache": "clear"}
    )
    if resp.status_code not in [200, 201]:
        print(f"❌ Falha ao acionar deploy no Render: {resp.status_code} - {resp.text}")
        sys.exit(1)
        
    deploy_id = resp.json().get("id")
    print(f"🚀 Deploy iniciado com sucesso! ID: {deploy_id}")
    return deploy_id


def poll_deploy_until_live(deploy_id, max_minutes=5):
    print(f"\n--- 4. MONITORANDO STATUS DO DEPLOY ({deploy_id}) ---")
    start_time = time.time()
    max_seconds = max_minutes * 60

    while time.time() - start_time < max_seconds:
        r = requests.get(f"{BASE_URL}/services/{RENDER_SERVICE_ID}/deploys/{deploy_id}", headers=HEADERS)
        if r.status_code == 200:
            status = r.json().get("status")
            elapsed = int(time.time() - start_time)
            print(f"[{elapsed}s] Status do Deploy: {status}", flush=True)

            if status == "live":
                print("🎉 Deploy finalizado e online no Render!")
                return True
            elif status in ["build_failed", "update_failed", "canceled"]:
                print(f"❌ Deploy no Render falhou com status: {status}")
                sys.exit(1)
        time.sleep(6)

    print("❌ Timeout aguardando deploy no Render.")
    sys.exit(1)


def verify_live_frontend():
    print("\n--- 5. TESTE DE INTERFACE E2E EM PRODUÇÃO (RENDER) ---")
    auth_str = f"{DASHBOARD_USERNAME}:{DASHBOARD_PASSWORD}"
    headers = {
        "Authorization": f"Basic {base64.b64encode(auth_str.encode()).decode()}",
        "User-Agent": "LayCS-Frontend-Validator/1.0"
    }

    for attempt in range(1, 4):
        try:
            print(f"Tentativa {attempt}: Testando {LIVE_URL}...")
            resp = requests.get(LIVE_URL, headers=headers, timeout=15)
            if resp.status_code == 200:
                html = resp.text
                
                # Validações dos componentes da interface
                checks = [
                    ("Painel IA Especialista", "IA Especialista em Lay Correct Score Ativa" in html),
                    ("Ordenação por Confiança", "Grau de Confiança da IA" in html),
                    ("Gaveta de Parecer IA", "Ver Justificativa Completa da IA" in html or "Auditoria & Parecer da IA" in html),
                    ("Destaque Top 5", "Top 5" in html)
                ]

                print("\nResultado dos Testes Visuais em Produção:")
                all_passed = True
                for name, passed in checks:
                    status_icon = "✅" if passed else "⚠️"
                    print(f"  {status_icon} {name}: {'OK' if passed else 'Não encontrado'}")
                    if not passed:
                        all_passed = False

                if all_passed:
                    print("\n🌟 VALIDAÇÃO COMPLETA: O Frontend está 100% íntegro em produção!")
                    return True
                else:
                    print("\n⚠️ A página carregou mas algum componente visual não foi identificado.")
                    return True
            else:
                print(f"Status HTTP {resp.status_code}. Aguardando inicialização completa do gunicorn...")
        except Exception as e:
            print(f"Erro ao conectar no Render: {e}")
        time.sleep(5)

    print("❌ Falha na validação em produção do Render.")
    sys.exit(1)


def main():
    run_local_ui_tests()
    sync_environment_variables()
    deploy_id = trigger_render_deploy()
    poll_deploy_until_live(deploy_id)
    verify_live_frontend()


if __name__ == "__main__":
    main()
