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

def generate_layback_json(target_score, target_team):
    """
    Lê o template gigante de times, desmarca todos,
    e marca apenas o time alvo.
    """
    template_path = 'data/layback_teams_template.json'
    if not os.path.exists(template_path):
        print(f"Erro: Template {template_path} nao encontrado.")
        return None
        
    with open(template_path, 'r') as f:
        data = json.load(f)
        
    mapped_team = get_mapped_name(target_team)
    team_found = False
    
    # Varre todos os times e ativa apenas o alvo
    if 'teams' in data:
        for team in data['teams']:
            # Desativa por padrao
            team['checked'] = False
            # Ativa se for o time alvo (case insensitive)
            if str(team.get('name', '')).strip().lower() == str(mapped_team).strip().lower():
                team['checked'] = True
                team_found = True
                
    if not team_found:
        print(f"Aviso: Time {mapped_team} nao encontrado no template do Layback para o alvo {target_score}!")
        
    # Salva arquivo especifico para este bot
    safe_target = target_score.replace('-', '_')
    output_path = f'data/bot_lay_{safe_target}.json'
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
        
    return output_path

def update_layback_bots(best_picks):
    """
    best_picks: dict, ex: {'0-1': MatchObj, '0-2': MatchObj}
    """
    if not config.LAYBACK_EMAIL or not config.LAYBACK_PASSWORD:
        print("Credenciais Layback ausentes. Apenas gerando JSONs localmente.")
        for target, match in best_picks.items():
            generate_layback_json(target, match.home_team)
        return False
        
    os.makedirs('logs', exist_ok=True)
    
    # Primeiro geramos todos os JSONs necessarios
    json_paths = {}
    for target, match in best_picks.items():
        path = generate_layback_json(target, match.home_team)
        if path:
            json_paths[target] = path
            
    if not json_paths:
        return False
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()
        
        try:
            # 1. Login
            page.goto("https://bot-betfair.layback.trade/login", timeout=30000)
            
            # Clica em Continuar com Betfair e aguarda redirecionamento
            with page.expect_navigation():
                page.click("text='Continuar com Betfair'")
                
            page.wait_for_selector("#username", timeout=15000)
            page.fill('#username', config.LAYBACK_EMAIL)
            page.fill('#password', config.LAYBACK_PASSWORD)
            page.click('#login')
            
            page.wait_for_load_state("networkidle")
            
            # 2. Navegacao e Upload (Simulado / Estrutural)
            # Como a interface exata é fechada, esta logica busca as abas/botoes padroes
            # Para cada bot alvo, tentariamos importar o arquivo gerado
            for target, json_path in json_paths.items():
                bot_alias = f"lay {target.replace('-', ' a ')}"
                print(f"[Simulação RPA] Navegando para o bot: {bot_alias}")
                # page.click(f"text='{bot_alias}'")
                # page.click("button.import-json") # Botao hipotetico
                # page.set_input_files('input[type="file"]', json_path)
                # page.click("button.save")
                
            success_path = "logs/layback_success.png"
            page.screenshot(path=success_path)
            # Envia print no final
            # send_document(success_path, caption="✅ Automação Layback executada com sucesso! JSONs injetados.")
            return True
            
        except Exception as e:
            error_path = "logs/layback_error.png"
            page.screenshot(path=error_path)
            send_document(error_path, caption=f"🚨 ERRO na Automação Layback:\\n`{str(e)}`\\nVerifique o print da tela.")
            print(f"Erro Layback: {e}")
            return False
        finally:
            browser.close()
