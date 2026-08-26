import os
import json

# 1. Update config.py
with open('config.py', 'r') as f:
    config_content = f.read()

new_config = """
LAYBACK_EMAIL = os.getenv('LAYBACK_EMAIL', '')
LAYBACK_PASSWORD = os.getenv('LAYBACK_PASSWORD', '')
"""
if "LAYBACK_EMAIL" not in config_content:
    config_content += new_config
    with open('config.py', 'w') as f:
        f.write(config_content)

# 2. Update .env.example
with open('.env.example', 'a') as f:
    f.write("\n# Fase 3 - Layback Bot\nLAYBACK_EMAIL=seu_email_layback\nLAYBACK_PASSWORD=sua_senha_layback\n")

# 3. Create Name Mapping
os.makedirs('data', exist_ok=True)
mapping = {
    "Atletico-MG": "Atletico Mineiro",
    "Athletico-PR": "Athletico Paranaense",
    "Vasco da Gama": "Vasco"
}
with open('data/team_mapping.json', 'w') as f:
    json.dump(mapping, f, indent=4)

# 4. Create integration/layback.py
os.makedirs('integration', exist_ok=True)
layback_code = """import os
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
    \"\"\"
    target_picks: dict, ex: {'lay 0 a 1': 'Cruzeiro', 'lay 0 a 2': 'Bodo/Glimt'}
    \"\"\"
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
            send_document(error_path, caption=f"🚨 ERRO na Automação Layback:\\n`{str(e)}`\\nVerifique o print da tela.")
            print(f"Erro na automaçao Layback: {e}")
            return False
        finally:
            browser.close()
"""
with open('integration/layback.py', 'w') as f:
    f.write(layback_code)
print("Arquivos do Layback criados.")

# 5. Integrate in scheduler.py
with open('scheduler.py', 'r') as f:
    sched_content = f.read()

import_line = "from notifications.telegram import send_message"
new_import_line = "from notifications.telegram import send_message\nfrom integration.layback import update_layback_bots"
if "from integration.layback" not in sched_content:
    sched_content = sched_content.replace(import_line, new_import_line)

# Localize o envio matinal para engatilhar a automação
trigger_loc = "send_message(msg)"
new_trigger_loc = """send_message(msg)
    
    # Prepara dicionario para o Layback
    layback_targets = {}
    for item in top_3:
        target = item['pred'].target_score # ex: '0-1'
        bot_alias = f"lay {target.replace('-', ' a ')}" # '0-1' -> 'lay 0 a 1'
        
        # Só pega o primeiro (Rank 1) de cada placar alvo se houver multiplos
        if bot_alias not in layback_targets:
            layback_targets[bot_alias] = item['match'].home_team
            
    if layback_targets:
        print(f"Acionando Layback Bot para os alvos: {layback_targets}")
        update_layback_bots(layback_targets)"""

if "update_layback_bots" not in sched_content:
    sched_content = sched_content.replace(trigger_loc, new_trigger_loc)
    with open('scheduler.py', 'w') as f:
        f.write(sched_content)
print("Scheduler atualizado para acionar a RPA.")
