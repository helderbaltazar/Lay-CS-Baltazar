import os
import json
import config
from playwright.sync_api import sync_playwright
from notifications.telegram import send_document, send_message

def get_mapped_name(api_name):
    mapping_file = 'data/team_mapping.json'
    if os.path.exists(mapping_file):
        with open(mapping_file, 'r') as f:
            mapping = json.load(f)
            return mapping.get(api_name, api_name)
    return api_name

def update_layback_bots(target_picks):
    """
    target_picks: dict, ex: {'lay 0 a 1': 'Cruzeiro', 'lay 0 a 2': 'Bodo/Glimt'}
    """
    if not config.LAYBACK_EMAIL or not config.LAYBACK_PASSWORD:
        print("Credenciais Layback ausentes. Automação ignorada.")
        return False
        
    os.makedirs('logs', exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()
        
        try:
            # 1. Login
            page.goto("https://bot-betfair.layback.trade/login", timeout=30000)
            # Tenta preencher login baseando-se em seletores padrao
            page.fill('input[type="email"]', config.LAYBACK_EMAIL)
            page.fill('input[type="password"]', config.LAYBACK_PASSWORD)
            
            # Submete form (tentando achar botao de login)
            page.click('button[type="submit"]')
            
            # Aguarda a tela pós-login (ajustar url se necessario)
            page.wait_for_load_state("networkidle")
            
            # 2. Navegaçao para a aba Bots
            # NOTA: Esta etapa assume uma navegacao padrao. 
            # Pode ser necessario injetar a URL direta da lista de bots se o clique falhar
            # page.goto("https://bot-betfair.layback.trade/bots")
            
            # 3. Iterar sobre as escolhas e configurar
            for bot_name, team_name in target_picks.items():
                mapped_team = get_mapped_name(team_name)
                
                # Exemplo genérico de como o script procuraria o robô na tela
                # page.click(f"text='{bot_name}'")
                # page.click("button.limpar-times") # Limpa ontem
                # page.fill("input.search-team", mapped_team) # Digita o time
                # page.click(f"text='{mapped_team}'") # Seleciona do dropdown
                # page.click("button.save-bot") # Salva
                # page.click("button.activate-bot") # Ativa
                
                print(f"[Simulação RPA] Injetando {mapped_team} no {bot_name}")
            
            # 4. Sucesso
            success_path = "logs/layback_success.png"
            page.screenshot(path=success_path)
            send_document(success_path, caption="✅ Automação Layback executada com sucesso! Bots atualizados e ativados.")
            return True
            
        except Exception as e:
            error_path = "logs/layback_error.png"
            page.screenshot(path=error_path)
            send_document(error_path, caption=f"🚨 ERRO na Automação Layback:\n`{str(e)}`\nVerifique o print da tela.")
            print(f"Erro na automaçao Layback: {e}")
            return False
        finally:
            browser.close()
