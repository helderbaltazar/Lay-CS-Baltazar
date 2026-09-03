import config
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 1280, 'height': 800})
    page = context.new_page()
    
    print("Logando na Layback...")
    page.goto("https://bot-betfair.layback.trade/login", timeout=30000)
    with page.expect_navigation():
        page.click("text='Continuar com Betfair'")
        
    page.wait_for_selector("#username", timeout=15000)
    page.fill('#username', config.LAYBACK_EMAIL)
    page.fill('#password', config.LAYBACK_PASSWORD)
    page.click('#login')
    
    # Aguarda o redirecionamento de volta para o Layback e carregamento do Dashboard
    page.wait_for_load_state("networkidle")
    
    print("URL apos login:", page.url)
    
    # Navegar para a pagina de Bots
    # Tenta achar um link com texto Bots ou apenas vai para a possivel URL
    bots_link = page.query_selector("a:has-text('Bots')")
    if bots_link:
        bots_link.click()
    else:
        page.goto("https://bot-betfair.layback.trade/bots")
        
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(3000) # Aguarda renderizar UI React/Vue
    
    print("URL atual:", page.url)
    page.screenshot(path="logs/layback_bots_page.png")
    
    # Extrair todos os elementos clicaveis que contenham 'Lay CS' ou '0 a'
    elements = page.query_selector_all("div, span, button, a")
    found = set()
    for el in elements:
        text = (el.inner_text() or "").strip()
        if text and ("Lay CS" in text or "0 a" in text or "lay" in text.lower()):
            if len(text) < 100:
                found.add(text)
                
    print("\nTextos encontrados na tela relacionados aos bots:")
    for t in found:
        print(f"- {t}")
        
    browser.close()
