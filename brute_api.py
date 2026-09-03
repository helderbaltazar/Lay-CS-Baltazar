import config
import requests
from playwright.sync_api import sync_playwright
with sync_playwright() as play:
    browser = play.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://bot-betfair.layback.trade/login")
    page.click("text='Continuar com Betfair'")
    page.wait_for_selector("#username", timeout=15000)
    page.fill('#username', config.LAYBACK_EMAIL)
    page.fill('#password', config.LAYBACK_PASSWORD)
    page.click('#login')
    page.wait_for_selector("[href='/dashboard']", timeout=30000)
    
    session = requests.Session()
    for c in page.context.cookies():
        session.cookies.set(c['name'], c['value'], domain=c['domain'])
        
    headers = {"accept": "application/json", "content-type": "application/json"}
    
    # Brute force 1
    r = session.post("https://bot-betfair.layback.trade/api/bots/150/teams", json={"teams": [{"name": "Cruzeiro", "checked": True}]}, headers=headers)
    print(f"POST /teams: {r.status_code}")
    
    # Brute force 2
    r = session.put("https://bot-betfair.layback.trade/api/bots/150/teams", json={"teams": [{"name": "Cruzeiro", "checked": True}]}, headers=headers)
    print(f"PUT /teams: {r.status_code}")
    
    # Brute force 3
    r = session.post("https://bot-betfair.layback.trade/api/bots/150/import", json={"teams": [{"name": "Cruzeiro", "checked": True}]}, headers=headers)
    print(f"POST /import: {r.status_code}")

    browser.close()
