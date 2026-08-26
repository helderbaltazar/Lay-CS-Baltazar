import os
import json
import config
from playwright.sync_api import sync_playwright
from notifications.telegram import send_document, send_message

def generate_layback_json(best_picks):
    """Gera o arquivo JSON padrao do Layback com as configuracoes do dia."""
    data = {
        "version": "1.0",
        "betOnNewCompetition": False, # Nao apostar as cegas
        "competitions": [],
        "teams": [] # Adicionamos o parametro de times
    }
    
    for target, match in best_picks.items():
        # Adiciona a competicao
        data["competitions"].append({
            "name": match.league_name,
            "checked": True
        })
        # Adiciona o time
        data["teams"].append({
            "name": match.home_team,
            "target": target,
            "checked": True
        })
        
    os.makedirs('data', exist_ok=True)
    filepath = 'data/layback_daily_config.json'
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)
    return filepath

def update_layback_bots(best_picks):
    if not config.LAYBACK_EMAIL or not config.LAYBACK_PASSWORD:
        print("Credenciais Layback ausentes. Apenas gerando JSON localmente.")
        generate_layback_json(best_picks)
        return False
        
    json_path = generate_layback_json(best_picks)
    os.makedirs('logs', exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()
        
        try:
            page.goto("https://bot-betfair.layback.trade/login", timeout=30000)
            page.fill('input[type="email"]', config.LAYBACK_EMAIL)
            page.fill('input[type="password"]', config.LAYBACK_PASSWORD)
            page.click('button[type="submit"]')
            
            page.wait_for_load_state("networkidle")
            
            # Aqui simula o envio do JSON (o seletor real dependera da interface da Layback)
            # page.goto("https://bot-betfair.layback.trade/bots/import")
            # page.set_input_files('input[type="file"]', json_path)
            # page.click('button.submit-import')
            
            success_path = "logs/layback_success.png"
            page.screenshot(path=success_path)
            # send_document(success_path, caption="✅ JSON do Layback injetado com sucesso!")
            return True
            
        except Exception as e:
            error_path = "logs/layback_error.png"
            page.screenshot(path=error_path)
            send_document(error_path, caption=f"🚨 ERRO na Automação Layback:\n`{str(e)}`\nVerifique o print da tela.")
            print(f"Erro Layback: {e}")
            return False
        finally:
            browser.close()
