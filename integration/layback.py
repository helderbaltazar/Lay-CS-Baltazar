import json
import logging
import os
import time
from playwright.sync_api import sync_playwright
import config

logger = logging.getLogger(__name__)

# IDs corretos do grupo "Lista CS"
LAY_0_1_BOT_ID = 4626
LAY_0_2_BOT_ID = 4753
LAY_0_3_BOT_ID = 27251

def generate_layback_json(teams_data: list, bot_name: str) -> str:
    """
    Gera o arquivo JSON para ser importado no Layback.
    """
    bot_json = {
        "version": "1.0",
        "betOnNewTeam": True,
        "teams": []
    }
    
    for team in teams_data:
        bot_json["teams"].append({
            "name": team["name"],
            "id": str(team["id"]),
            "checked": True,
            "side": "A"  # Both sides
        })
        
    filename = f"data/{bot_name}.json"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(bot_json, f, ensure_ascii=False, indent=2)
        
    return filename

def inject_teams_ui(bot_id: int, json_path: str):
    """
    Injeta o JSON no bot navegando pela interface web.
    """
    with sync_playwright() as play:
        browser = play.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1280, 'height': 3000})
        
        logger.info(f"[{bot_id}] Fazendo login...")
        page.goto("https://bot-betfair.layback.trade/login")
        page.click("text='Continuar com Betfair'")
        page.wait_for_selector("#username", timeout=15000)
        page.fill('#username', config.LAYBACK_EMAIL)
        page.fill('#password', config.LAYBACK_PASSWORD)
        page.click('#login')
        page.wait_for_selector("[href='/dashboard']", timeout=30000)
        
        logger.info(f"[{bot_id}] Navegando para edição do bot...")
        page.goto(f"https://bot-betfair.layback.trade/bots/{bot_id}/edit", wait_until="networkidle")
        time.sleep(3)
        
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1)
        
        logger.info(f"[{bot_id}] Expandindo aba Times...")
        aba_times = page.locator("text='Times'")
        if aba_times.count() > 0:
            aba_times.last.click()
            time.sleep(2)
            
            importar = page.locator("button:has-text('Importar')")
            if importar.count() > 0:
                importar.first.click()
                time.sleep(1)
                
                file_input = page.locator("input[type='file']")
                if file_input.count() > 0:
                    logger.info(f"[{bot_id}] Fazendo upload de {json_path}...")
                    file_input.first.set_input_files(os.path.abspath(json_path))
                    time.sleep(3)
                    
                    # Gerar evidência (opcional, só se precisar, já geramos no script final_ui_upload)
                    ver_sel = page.locator("button:has-text('selecionados')")
                    if ver_sel.count() > 0:
                        ver_sel.first.click()
                        time.sleep(2)
                        
                    salvar = page.locator("button:has-text('Salvar Bot')")
                    if salvar.count() > 0:
                        salvar.first.click()
                        time.sleep(5)
                        logger.info(f"[{bot_id}] Upload e salvamento CONCLUÍDOS!")
                        browser.close()
                        return True
                    else:
                        logger.error(f"[{bot_id}] Botão Salvar Bot não encontrado")
                else:
                    logger.error(f"[{bot_id}] Input de arquivo não encontrado")
            else:
                logger.error(f"[{bot_id}] Botão Importar não encontrado")
        else:
            logger.error(f"[{bot_id}] Aba Times não encontrada")
            
        browser.close()
        return False


def get_betfair_id(team_name, layback_teams):
    import difflib
    names = [t["name"] for t in layback_teams]
    if team_name in names:
        team = next((t for t in layback_teams if t["name"] == team_name), None)
        return {"name": team["name"], "id": int(team["id"])}
        
    replacements = {
        " FC": "", "FC ": "", " CF": "", " Clube": "", " Esporte": "", 
        " SP": "", " RJ": "", " MG": "", " RS": "", " PR": "", 
        " SC": "", " BA": "", " GO": "", " CE": "", " PE": "",
        "Atletico Mineiro": "Atletico MG", "Athletico Paranaense": "Atletico PR",
        "Atletico Paranaense": "Atletico PR", "Atletico Goianiense": "Atletico GO",
        "Botafogo RJ": "Botafogo", "Fluminense RJ": "Fluminense",
        "Flamengo RJ": "Flamengo", "Vasco da Gama": "Vasco da Gama",
        "Cruzeiro": "Cruzeiro MG"
    }
    
    modified_name = team_name
    for k, v in replacements.items():
        if k in modified_name:
            modified_name = modified_name.replace(k, v).strip()
            
    if modified_name in names:
        team = next((t for t in layback_teams if t["name"] == modified_name), None)
        return {"name": team["name"], "id": int(team["id"])}
        
    matches = difflib.get_close_matches(team_name, names, n=1, cutoff=0.6)
    if matches:
        match_name = matches[0]
        team = next((t for t in layback_teams if t["name"] == match_name), None)
        return {"name": team["name"], "id": int(team["id"])}
        
    return None

def update_layback_bots():
    import datetime
    import pytz
    from analysis.scanner import scan_all, rank_by_target
    from models.poisson import PoissonDixonColes
    from data.api_football import get_fixtures
    
    logger.info("Iniciando extração e injeção real (Hoje e Amanhã)...")
    now_br = datetime.datetime.now(pytz.timezone(config.SCHEDULER_TIMEZONE))
    dates_to_scan = [now_br.strftime("%Y-%m-%d"), (now_br + datetime.timedelta(days=1)).strftime("%Y-%m-%d")]
    
    model = PoissonDixonColes()
    all_fixtures = []
    for d in dates_to_scan:
        f = get_fixtures(d)
        if f: all_fixtures.extend(f)
            
    if not all_fixtures:
        logger.warning("Nenhum jogo encontrado nas ligas configuradas.")
        return
        
    results = scan_all(all_fixtures, model)
    rankings = rank_by_target(results)
    
    with open("logs/teams_api.json", "r") as f:
        layback_teams = json.load(f)["data"]["teams"]
        
    rank1_01 = [r for r in rankings.get("0-1", []) if r["rank"] == 1]
    rank1_02 = [r for r in rankings.get("0-2", []) if r["rank"] == 1]
    rank1_03 = [r for r in rankings.get("0-3", []) if r["rank"] == 1]
    
    bots_targets = [
        (LAY_0_1_BOT_ID, "bot_lay_0_1", rank1_01, "0-1"),
        (LAY_0_2_BOT_ID, "bot_lay_0_2", rank1_02, "0-2"),
        (LAY_0_3_BOT_ID, "bot_lay_0_3", rank1_03, "0-3"),
    ]
    
    for bot_id, bot_name, rank_list, target in bots_targets:
        if not rank_list:
            continue
            
        game = rank_list[0]
        home_bf = get_betfair_id(game['home'], layback_teams)
        away_bf = get_betfair_id(game['away'], layback_teams)
        
        teams_data = []
        if home_bf: teams_data.append(home_bf)
        if away_bf: teams_data.append(away_bf)
            
        if not teams_data:
            continue
            
        json_file = generate_layback_json(teams_data, bot_name)
        inject_teams_ui(bot_id, json_file)
