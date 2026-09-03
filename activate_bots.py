import config
import requests as req_lib
from playwright.sync_api import sync_playwright
import json

def send_telegram_photo(photo_path, caption):
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendPhoto"
    with open(photo_path, "rb") as f:
        req_lib.post(url, data={"chat_id": "870581945", "caption": caption}, files={"photo": f})

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 1440, 'height': 3000})
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
        "referer": "https://bot-betfair.layback.trade/bots",
    }
    
    bot_ids = [150, 151, 152]
    bot_names = ["Lay 0 a 1", "Lay 0 a 2", "Lay 0 a 3"]
    
    for b_id, b_name in zip(bot_ids, bot_names):
        # GET bot
        r = session.get(f"https://bot-betfair.layback.trade/api/bots/{b_id}", headers=headers)
        if r.status_code == 200:
            bot = r.json().get("data", {}).get("bot", {})
            
            # Update isActive to True
            bot["isActive"] = True
            
            # PATCH to save
            headers["referer"] = f"https://bot-betfair.layback.trade/bots/{b_id}"
            r_patch = session.patch(f"https://bot-betfair.layback.trade/api/bots/{b_id}", headers=headers, json=bot)
            
            if r_patch.status_code == 200:
                print(f"Bot {b_name} ({b_id}) ativado com sucesso via API!")
            else:
                print(f"Erro ao ativar {b_name} ({b_id}): {r_patch.text}")
                
        # Access page to take screenshot
        page.goto(f"https://bot-betfair.layback.trade/bots/{b_id}")
        page.wait_for_timeout(3000)
        screenshot_path = f"logs/bot_{b_id}_ativo.png"
        page.screenshot(path=screenshot_path)
        print(f"Screenshot salvo: {screenshot_path}")
        
        # Send to telegram
        send_telegram_photo(screenshot_path, f"🤖 Bot {b_name} foi ATIVADO com sucesso!")
        print(f"Screenshot {b_name} enviado para o Telegram.")
        
    browser.close()
