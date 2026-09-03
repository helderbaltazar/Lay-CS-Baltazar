import config
import json
import requests as req_lib
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 1280, 'height': 800})
    page = context.new_page()
    
    # Login
    page.goto("https://bot-betfair.layback.trade/login", timeout=30000)
    with page.expect_navigation():
        page.click("text='Continuar com Betfair'")
    page.wait_for_selector("#username", timeout=15000)
    page.fill('#username', config.LAYBACK_EMAIL)
    page.fill('#password', config.LAYBACK_PASSWORD)
    page.click('#login')
    
    # Aguarda o dashboard
    page.wait_for_selector("[href='/dashboard'], [href*='/bots']", timeout=30000)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(3000)
    
    # Captura cookies
    cookies = context.cookies()
    cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
    print(f"Cookies capturados: {len(cookies)}")
    for c in cookies:
        print(f"  {c['name']}: {c['value'][:60]}...")
    
    with open("logs/session_cookies.json", "w") as f:
        json.dump(cookies, f, indent=2)
    
    # Usa cookies para chamar a API
    session = req_lib.Session()
    for c in cookies:
        session.cookies.set(c['name'], c['value'], domain=c['domain'])
    
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "referer": "https://bot-betfair.layback.trade/bots/150",
    }
    
    # Testa a API
    print("\n=== TESTANDO ENDPOINTS ===")
    for url in [
        "https://bot-betfair.layback.trade/api/bots/150",
        "https://bot-betfair.layback.trade/api/bots/150/with-status",
    ]:
        r = session.get(url, headers=headers, timeout=10)
        print(f"\nGET {url.split('/')[-1]}: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(json.dumps(data, indent=2)[:500])
        else:
            print(r.text[:300])
    
    browser.close()
