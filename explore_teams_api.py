import config
import json
import requests as req_lib
from playwright.sync_api import sync_playwright

captured_token = None

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 1280, 'height': 800})
    page = context.new_page()
    
    def on_request(request):
        global captured_token
        auth = request.headers.get("authorization", "")
        if auth:
            captured_token = auth
    
    page.on("request", on_request)
    
    page.goto("https://bot-betfair.layback.trade/login", timeout=30000)
    with page.expect_navigation():
        page.click("text='Continuar com Betfair'")
    page.wait_for_selector("#username", timeout=15000)
    page.fill('#username', config.LAYBACK_EMAIL)
    page.fill('#password', config.LAYBACK_PASSWORD)
    page.click('#login')
    page.wait_for_selector("text=Dashboard", timeout=15000)
    page.wait_for_timeout(3000)
    
    print(f"Token capturado: {(captured_token or '')[:80]}...")
    
    # Salva o token
    with open("logs/api_token.txt", "w") as f:
        f.write(captured_token or "")
    
    # Navega para o bot 150 para disparar a chamada ao /api/teams
    page.goto("https://bot-betfair.layback.trade/bots/150")
    page.wait_for_selector("text=Configuração", timeout=15000)
    page.wait_for_timeout(3000)
    page.click("button:has-text('Configuração')")
    page.wait_for_timeout(3000)
    
    # Captura cookies para usar nas chamadas diretas
    cookies = context.cookies()
    cookie_dict = {c["name"]: c["value"] for c in cookies}
    
    # Chama a API /api/teams diretamente via requests
    headers = {
        "authorization": captured_token,
        "accept": "application/json",
        "content-type": "application/json",
    }
    
    # Obtém os times disponíveis
    r = req_lib.get("https://bot-betfair.layback.trade/api/teams", headers=headers, timeout=15)
    print(f"\nGET /api/teams: {r.status_code}")
    teams_data = r.json()
    with open("logs/api_teams_response.json", "w") as f:
        json.dump(teams_data, f, indent=2)
    print(f"Total de times: {len(teams_data.get('data', []))}")
    print(f"Exemplo de time: {json.dumps(teams_data.get('data', [{}])[:3], indent=2)}")
    
    # Obtém a config atual de teams do bot 150
    r2 = req_lib.get("https://bot-betfair.layback.trade/api/bots/150/teams", headers=headers, timeout=15)
    print(f"\nGET /api/bots/150/teams: {r2.status_code}")
    if r2.status_code == 200:
        bot_teams = r2.json()
        with open("logs/bot_150_teams.json", "w") as f:
            json.dump(bot_teams, f, indent=2)
        print(json.dumps(bot_teams, indent=2)[:2000])
    else:
        print(r2.text[:500])
    
    browser.close()
