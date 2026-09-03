import json
import config
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    
    # Login
    page.goto("https://bot-betfair.layback.trade/login", timeout=30000)
    with page.expect_navigation():
        page.click("text='Continuar com Betfair'")
    page.wait_for_selector("#username", timeout=15000)
    page.fill('#username', config.LAYBACK_EMAIL)
    page.fill('#password', config.LAYBACK_PASSWORD)
    page.click('#login')
    page.wait_for_selector("[href='/dashboard'], [href*='/bots']", timeout=30000)
    page.wait_for_timeout(3000)
    
    page.goto("https://bot-betfair.layback.trade/bots/150", timeout=30000)
    page.wait_for_timeout(5000)
    
    # Dump __NEXT_DATA__
    next_data = page.evaluate("() => window.__NEXT_DATA__")
    
    with open("logs/next_data.json", "w") as f:
        json.dump(next_data, f, indent=2)
        
    print("next_data.json created.")
    
    browser.close()
