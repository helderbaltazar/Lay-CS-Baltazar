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
        
    # The frontend usually fetches teams and competitions on the edit page
    headers = {"accept": "application/json", "content-type": "application/json"}
    
    # Try different team endpoints
    urls_to_try = [
        "https://bot-betfair.layback.trade/api/teams",
        "https://bot-betfair.layback.trade/api/teams-summary",
        "https://bot-betfair.layback.trade/api/competitions",
        "https://bot-betfair.layback.trade/api/teams?limit=10000"
    ]
    
    for url in urls_to_try:
        print(f"Trying {url}...")
        r = session.get(url, headers=headers)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            print(f"Data snippet: {r.text[:300]}")
            with open("data/teams_api.json", "w") as f:
                f.write(r.text)
            break

    browser.close()
