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
LAY_1_3_BOT_ID = 29778

def generate_layback_json(teams_data: list, bot_name: str) -> str:
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
            "side": "A"
        })
        
    filename = f"data/{bot_name}.json"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(bot_json, f, ensure_ascii=False, indent=2)
        
    return filename

def get_db_session():
    from database.db import SessionLocal
    return SessionLocal()

def get_cookies_from_db():
    from database.models_db import SystemConfig
    db = get_db_session()
    try:
        conf = db.query(SystemConfig).filter(SystemConfig.key == "layback_cookies").first()
        if conf and conf.value:
            return json.loads(conf.value)
    except Exception as e:
        logger.error(f"Erro ao ler cookies do BD: {e}")
    finally:
        db.close()
    return None

def save_cookies_to_db(cookies):
    from database.models_db import SystemConfig
    db = get_db_session()
    try:
        conf = db.query(SystemConfig).filter(SystemConfig.key == "layback_cookies").first()
        if not conf:
            conf = SystemConfig(key="layback_cookies", value=json.dumps(cookies))
            db.add(conf)
        else:
            conf.value = json.dumps(cookies)
        db.commit()
    except Exception as e:
        logger.error(f"Erro ao salvar cookies no BD: {e}")
    finally:
        db.close()

def inject_teams_ui(bot_id: int, json_path: str):
    if not os.getenv("GITHUB_ACTIONS"):
        logger.info(f"[MOCK] Simulando injeção no bot {bot_id} (Arquivo: {json_path})")
        return True

    try:
        from playwright_stealth import stealth_sync
    except ImportError:
        logger.warning("playwright-stealth não instalado! Continuando sem stealth mode.")
        stealth_sync = None

    with sync_playwright() as play:
        proxy_server = os.getenv("PROXY_SERVER")
        proxy_username = os.getenv("PROXY_USERNAME")
        proxy_password = os.getenv("PROXY_PASSWORD")
        
        launch_args = {"headless": True}
        
        if proxy_server and proxy_username and proxy_password:
            logger.info(f"[{bot_id}] 🛡️ Iniciando navegador com Proxy Camuflado...")
            launch_args["proxy"] = {
                "server": f"http://{proxy_server}",
                "username": proxy_username,
                "password": proxy_password
            }
        else:
            logger.info(f"[{bot_id}] ⚠️ Nenhum proxy configurado. Rodando com o IP padrão da nuvem.")
            
        browser = play.chromium.launch(**launch_args)
        
        # Cria context e tenta injetar cookies
        context = browser.new_context(viewport={'width': 1280, 'height': 3000})
        saved_cookies = get_cookies_from_db()
        if saved_cookies:
            context.add_cookies(saved_cookies)
            logger.info(f"[{bot_id}] Cookies de sessão carregados do banco.")
            
        page = context.new_page()
        if stealth_sync:
            stealth_sync(page)
            logger.info(f"[{bot_id}] 🥷 Playwright Stealth ativado.")
        
        # Tenta acessar direto a dashboard (Fallback: Se falhar ou pedir login)
        page.goto("https://bot-betfair.layback.trade/dashboard")
        time.sleep(3)
        
        # Verifica se caiu na tela de login
        if "login" in page.url:
            logger.info(f"[{bot_id}] Sessão inválida ou sem cookie. Fazendo login manual...")
            page.goto("https://bot-betfair.layback.trade/login")
            page.click("text='Continuar com Betfair'")
            try:
                page.wait_for_selector("#username", timeout=15000)
                page.fill('#username', config.LAYBACK_EMAIL)
                page.fill('#password', config.LAYBACK_PASSWORD)
                page.click('#login')
                page.wait_for_selector("[href='/dashboard']", timeout=30000)
                
                # Salva a nova sessão!
                new_cookies = context.cookies()
                save_cookies_to_db(new_cookies)
                logger.info(f"[{bot_id}] Novos cookies de sessão salvos no Supabase!")
            except Exception as e:
                page.screenshot(path="logs/login_error.png")
                try:
                    from notifications.telegram import send_document, send_message
                    send_message(f"🚨 *Erro crítico no login do Bot {bot_id}* 🚨\nTimeout ou bloqueio do Cloudflare detectado. Veja a imagem em anexo:")
                    send_document("logs/login_error.png")
                except Exception:
                    pass
                raise e
        else:
            logger.info(f"[{bot_id}] ✅ Sessão recuperada com sucesso via Cookies!")
            
        logger.info(f"[{bot_id}] Navegando para edição do bot...")
        page.goto(f"https://bot-betfair.layback.trade/bots/{bot_id}/edit", wait_until="networkidle")
        time.sleep(3)
        
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1)
        
        logger.info(f"[{bot_id}] Expandindo aba Times...")
        aba_times = page.locator("text='Times'")
        if aba_times.count() == 0:
            logger.error(f"[{bot_id}] Aba Times não encontrada. Tirando screenshot e abortando...")
            page.screenshot(path=f"logs/error_aba_times_{bot_id}.png")
            try:
                from notifications.telegram import send_document, send_message
                send_message(f"🚨 *Erro ao injetar no Bot {bot_id}* 🚨\nAba 'Times' não encontrada! (Pode ser bloqueio Cloudflare). Veja a imagem em anexo:")
                send_document(f"logs/error_aba_times_{bot_id}.png")
            except Exception:
                pass
            return False
            
        if True:
            aba_times.last.click()
            time.sleep(2)
            
            deselect = page.locator("text='Deselecionar todas'")
            if deselect.count() > 0:
                deselect.first.click()
                time.sleep(1)
                logger.info(f"[{bot_id}] Times antigos deselecionados.")
            else:
                logger.warning(f"[{bot_id}] Botão 'Deselecionar todas' não encontrado.")
                
            importar = page.locator("button:has-text('Importar')")
            if importar.count() > 0:
                importar.first.click()
                time.sleep(1)
                
                file_input = page.locator("input[type='file']")
                if file_input.count() > 0:
                    logger.info(f"[{bot_id}] Fazendo upload de {json_path}...")
                    file_input.first.set_input_files(os.path.abspath(json_path))
                    time.sleep(3)
                    
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
    from run_real_injection import ensure_data_in_db, inject_from_db
    logger.info("Iniciando rotina de extração e injeção do Layback...")
    ensure_data_in_db()
    inject_from_db()
    logger.info("Rotina de injeção concluída com sucesso.")
