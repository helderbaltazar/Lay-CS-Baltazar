import json
import logging
import os
import difflib
import requests as req
import config

logger = logging.getLogger(__name__)

LAY_0_1_BOT_ID = 4626
LAY_0_2_BOT_ID = 4753
LAY_0_3_BOT_ID = 27251
LAY_1_3_BOT_ID = 29778
BASE_URL = "https://bot-betfair.layback.trade"
_layback_teams_cache = None


def generate_layback_json(teams_data, bot_name, output_dir="data"):
    bot_json = {"version": "1.0", "betOnNewTeam": True, "teams": []}
    for team in teams_data:
        bot_json["teams"].append({"name": team["name"], "id": str(team["id"]), "checked": True, "side": "A"})
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
    cookies_list = get_cookies_from_db()
    if not cookies_list:
        logger.error("Nenhum cookie de sessao encontrado no banco de dados!")
        return None, None
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Origin": BASE_URL,
        "Referer": f"{BASE_URL}/",
        "Cookie": "; ".join([f"{c['name']}={c['value']}" for c in cookies_list]),
    }
    session = req.Session()
    session.headers.update(headers)
    return session, cookies_list


def get_all_layback_teams(session):
    global _layback_teams_cache
    if _layback_teams_cache is not None:
        return _layback_teams_cache
    try:
        r = session.get(f"{BASE_URL}/api/teams", timeout=15)
        if r.status_code == 200:
            _layback_teams_cache = r.json()['data']['teams']
            logger.info(f"Total de {len(_layback_teams_cache)} times carregados da Layback API.")
            return _layback_teams_cache
    except Exception as e:
        logger.error(f"Erro ao buscar times da Layback: {e}")
    return []


def find_layback_team_id(team_name, all_teams):
    names = [t["name"] for t in all_teams]
    # Correspondencia exata
    if team_name in names:
        t = next(t for t in all_teams if t["name"] == team_name)
        return {"id": t["id"], "name": t["name"]}
    # Normalizacoes
    replacements = {
        " FC": "", "FC ": "", " CF": "", " SC": "", " AC": "",
        " SP": "", " RJ": "", " MG": "", " RS": "", " PR": "",
        " BA": "", " GO": "", " CE": "", " PE": "", " ES": "",
        "Atletico Mineiro": "Atletico MG", "Athletico Paranaense": "Atletico PR",
        "Atletico Goianiense": "Atletico GO", "Botafogo RJ": "Botafogo",
        "Fluminense FC": "Fluminense", "Flamengo RJ": "Flamengo",
        "Cruzeiro": "Cruzeiro MG",
    }
    modified_name = team_name
    for k, v in replacements.items():
        if k in modified_name:
            modified_name = modified_name.replace(k, v).strip()
    if modified_name in names:
        t = next(t for t in all_teams if t["name"] == modified_name)
        return {"id": t["id"], "name": t["name"]}
    # Fuzzy
    for candidate in [team_name, modified_name]:
        matches = difflib.get_close_matches(candidate, names, n=1, cutoff=0.6)
        if matches:
            t = next(t for t in all_teams if t["name"] == matches[0])
            logger.info(f"  Fuzzy match: '{team_name}' -> '{t['name']}'")
            return {"id": t["id"], "name": t["name"]}
    return None


def inject_teams_ui(bot_id, json_path):
    """Injeta times no bot via API REST da Layback. Sem Playwright, sem Cloudflare."""
    if not os.getenv("GITHUB_ACTIONS"):
        logger.info(f"[MOCK] Simulando injecao no bot {bot_id} (Arquivo: {json_path})")
        return True

    # 1. Carrega JSON de times
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            teams_data = json.load(f)
        teams_from_file = teams_data.get("teams", [])
        if not teams_from_file:
            logger.error(f"[{bot_id}] Nenhum time no arquivo {json_path}")
            return False
        logger.info(f"[{bot_id}] {len(teams_from_file)} times carregados do arquivo.")
    except Exception as e:
        logger.error(f"[{bot_id}] Erro ao ler {json_path}: {e}")
        return False

    # 2. Sessao autenticada
    session, _ = get_layback_session()
    if not session:
        return False

    # 3. Verifica autenticacao
    try:
        r = session.get(f"{BASE_URL}/api/bots/{bot_id}", timeout=15)
        if r.status_code == 401:
            logger.error(f"[{bot_id}] Sessao expirada (401). Renovar cookies!")
            try:
                from notifications.telegram import send_message
                send_message(f"Sessao Layback expirada no Bot {bot_id}! Faca login manual.")
            except Exception:
                pass
            return False
        elif r.status_code != 200:
            logger.error(f"[{bot_id}] Erro ao buscar bot: {r.status_code}")
            return False
        bot_name = r.json()['data']['bot']['name']
        logger.info(f"[{bot_id}] Bot '{bot_name}' autenticado.")
    except Exception as e:
        logger.error(f"[{bot_id}] Erro de conexao: {e}")
        return False

    # 4. Traduz nomes para IDs Layback
    all_layback_teams = get_all_layback_teams(session)
    resolved_teams = []
    not_found = []

    for team in teams_from_file:
        team_name = team.get("name", "")
        found = find_layback_team_id(team_name, all_layback_teams)
        if found:
            resolved_teams.append({"id": str(found["id"]), "name": found["name"], "checked": True, "side": "A"})
            logger.info(f"[{bot_id}]   OK '{team_name}' -> Layback ID {found['id']} ({found['name']})")
        else:
            not_found.append(team_name)
            logger.warning(f"[{bot_id}]   AVISO Time '{team_name}' NAO encontrado na Layback!")

    if not resolved_teams:
        logger.error(f"[{bot_id}] Nenhum time resolvido. Abortando.")
        return False
    if not_found:
        logger.warning(f"[{bot_id}] Times nao encontrados: {not_found}")

    # 5. POST /api/bots/bulk/teams (substitui TODOS os times)
    payload = {"ids": [bot_id], "teams": resolved_teams}
    try:
        r2 = session.post(f"{BASE_URL}/api/bots/bulk/teams", json=payload, timeout=15)
        if r2.status_code == 200:
            count = r2.json().get("data", {}).get("count", 0)
            logger.info(f"[{bot_id}] SUCESSO! {len(resolved_teams)} times injetados! (count={count})")
            return True
        else:
            logger.error(f"[{bot_id}] Falha na injec: {r2.status_code} -> {r2.text[:300]}")
            return False
    except Exception as e:
        logger.error(f"[{bot_id}] Erro ao injetar: {e}")
        return False


def get_bot_teams_api(bot_id, session=None):
    """Retorna times injetados no bot (via campo 'teams' do GET /api/bots/{id})."""
    if session is None:
        session, _ = get_layback_session()
        if not session:
            return []
    try:
        r = session.get(f"{BASE_URL}/api/bots/{bot_id}", timeout=10)
        if r.status_code == 200:
            return r.json()['data']['bot'].get("teams", [])
    except Exception as e:
        logger.error(f"Erro ao buscar bot {bot_id}: {e}")
    return []


def get_betfair_id(team_name, layback_teams):
    return find_layback_team_id(team_name, layback_teams)


def update_layback_bots():
    from run_real_injection import ensure_data_in_db, inject_from_db
    logger.info("Iniciando rotina de injec do Layback...")
    ensure_data_in_db()
    inject_from_db()
    logger.info("Rotina de injec concluida.")
