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

def generate_layback_json(teams_data: list, bot_name: str, output_dir: str = "data") -> str:
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
        
    filename = f"{output_dir}/{bot_name}.json"
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

def get_layback_session():
    """Cria uma sessão requests autenticada usando cookies do banco de dados."""
    import requests as req
    cookies_list = get_cookies_from_db()
    if not cookies_list:
        logger.error("Nenhum cookie de sessão encontrado no banco de dados!")
        return None, None

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Origin": "https://bot-betfair.layback.trade",
        "Referer": "https://bot-betfair.layback.trade/",
        "Cookie": "; ".join([f"{c['name']}={c['value']}" for c in cookies_list]),
    }
    session = req.Session()
    session.headers.update(headers)
    return session, cookies_list


def inject_teams_ui(bot_id: int, json_path: str):
    """
    Injeta times no bot da Layback via API REST.
    Sem Playwright, sem Cloudflare, sem timeout.
    """
    if not os.getenv("GITHUB_ACTIONS"):
        logger.info(f"[MOCK] Simulando injeção no bot {bot_id} (Arquivo: {json_path})")
        return True

    base_url = "https://bot-betfair.layback.trade"

    # Carrega o JSON de times gerado pelo sistema
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            teams_data = json.load(f)
        teams = teams_data.get("teams", [])
        if not teams:
            logger.error(f"[{bot_id}] Nenhum time encontrado no arquivo {json_path}")
            return False
        logger.info(f"[{bot_id}] {len(teams)} times carregados do arquivo.")
    except Exception as e:
        logger.error(f"[{bot_id}] Erro ao ler arquivo {json_path}: {e}")
        return False

    # Obtém sessão autenticada
    session, cookies_list = get_layback_session()
    if not session:
        return False

    # Verifica autenticação e obtém dados atuais do bot
    try:
        r = session.get(f"{base_url}/api/bots/{bot_id}", timeout=15)
        if r.status_code == 401:
            logger.error(f"[{bot_id}] ❌ Sessão expirada (401). Os cookies do banco precisam ser renovados!")
            try:
                from notifications.telegram import send_message
                send_message(f"🚨 *Bot {bot_id}* - Sessão Layback expirada! Faça login manual para renovar cookies.")
            except Exception:
                pass
            return False
        elif r.status_code != 200:
            logger.error(f"[{bot_id}] ❌ Erro ao buscar bot: {r.status_code} -> {r.text[:200]}")
            return False

        bot_data = r.json()['data']['bot']
        logger.info(f"[{bot_id}] ✅ Bot '{bot_data['name']}' encontrado via API.")
    except Exception as e:
        logger.error(f"[{bot_id}] ❌ Erro de conexão com a API Layback: {e}")
        return False

    # Atualiza os times via PATCH
    patch_payload = {
        "isShowedOnProject": bot_data.get("isShowedOnProject", False),
        "teams": [
            {
                "id": str(t.get("id", "")),
                "name": t.get("name", ""),
                "checked": True,
                "side": "A"
            }
            for t in teams
        ]
    }

    try:
        r2 = session.patch(f"{base_url}/api/bots/{bot_id}", json=patch_payload, timeout=15)
        if r2.status_code == 200:
            result = r2.json()
            logger.info(f"[{bot_id}] ✅ SUCESSO! {len(teams)} times injetados via API REST!")
            return True
        else:
            logger.error(f"[{bot_id}] ❌ PATCH falhou: {r2.status_code} -> {r2.text[:300]}")
            return False
    except Exception as e:
        logger.error(f"[{bot_id}] ❌ Erro ao fazer PATCH: {e}")
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
