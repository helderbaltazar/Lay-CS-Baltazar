import config
import json
import requests as req_lib
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    
    page.goto("https://bot-betfair.layback.trade/login", timeout=30000)
    with page.expect_navigation():
        page.click("text='Continuar com Betfair'")
    page.wait_for_selector("#username", timeout=15000)
    page.fill('#username', config.LAYBACK_EMAIL)
    page.fill('#password', config.LAYBACK_PASSWORD)
    page.click('#login')
    page.wait_for_selector("[href='/dashboard']", timeout=30000)
    
    cookies = context.cookies()
    session = req_lib.Session()
    for c in cookies:
        session.cookies.set(c['name'], c['value'], domain=c['domain'])
        
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "referer": "https://bot-betfair.layback.trade/bots/150",
    }
    
    with open("data/bot_lay_0_1.json", "r") as f:
        payload = json.load(f)
        
    # Attempt 1: PUT /api/bots/150/teams
    print("Tentando PUT /api/bots/150/teams...")
    r1 = session.put("https://bot-betfair.layback.trade/api/bots/150/teams", headers=headers, json=payload)
    print(r1.status_code, r1.text[:200])

    # Attempt 2: PATCH /api/bots/150/teams
    print("\nTentando PATCH /api/bots/150/teams...")
    r2 = session.patch("https://bot-betfair.layback.trade/api/bots/150/teams", headers=headers, json=payload)
    print(r2.status_code, r2.text[:200])
    
    # Attempt 3: POST /api/bots/150/teams
    print("\nTentando POST /api/bots/150/teams...")
    r3 = session.post("https://bot-betfair.layback.trade/api/bots/150/teams", headers=headers, json=payload)
    print(r3.status_code, r3.text[:200])

    browser.close()
