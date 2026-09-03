import config
import time
from playwright.sync_api import sync_playwright

with sync_playwright() as play:
    browser = play.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1280, 'height': 3000})
    
    page.goto("https://bot-betfair.layback.trade/login")
    page.click("text='Continuar com Betfair'")
    page.wait_for_selector("#username")
    page.fill('#username', config.LAYBACK_EMAIL)
    page.fill('#password', config.LAYBACK_PASSWORD)
    page.click('#login')
    page.wait_for_selector("[href='/dashboard']", timeout=30000)
    
    bot_id = 4626
    page.goto(f"https://bot-betfair.layback.trade/bots/{bot_id}")
    time.sleep(3)
    
    page.screenshot(path="logs/explore_1.png", full_page=True)
    
    # Click Configuração
    page.click("button:has-text('Configuração')")
    time.sleep(3)
    
    page.screenshot(path="logs/explore_2.png", full_page=True)
    
    browser.close()
