import config
import sys
from playwright.sync_api import sync_playwright

def p(msg):
    print(msg)
    sys.stdout.flush()

bot_ids = {
    "0-1": 150,
    "0-2": 151,
    "0-3": 152
}

with sync_playwright() as play:
    p("Launching browser...")
    browser = play.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 1440, 'height': 3000})
    page = context.new_page()
    
    p("Going to login...")
    page.goto("https://bot-betfair.layback.trade/login", timeout=30000, wait_until="domcontentloaded")
    
    p("Clicking Continuar com Betfair...")
    with page.expect_navigation():
        page.click("text='Continuar com Betfair'")
        
    p("Waiting for username...")
    page.wait_for_selector("#username", timeout=15000)
    page.fill('#username', config.LAYBACK_EMAIL)
    page.fill('#password', config.LAYBACK_PASSWORD)
    
    p("Clicking login...")
    page.click('#login')
    page.wait_for_selector("[href='/dashboard']", timeout=30000)
    
    for target, bot_id in bot_ids.items():
        json_file = f"data/bot_lay_{target.replace('-', '_')}.json"
        
        p(f"\\n--- Processando Bot {bot_id} ({target}) ---")
        page.goto(f"https://bot-betfair.layback.trade/bots/{bot_id}", timeout=30000, wait_until="domcontentloaded")
        
        p("Waiting for Configuração...")
        page.wait_for_selector("button:has-text('Configuração')", timeout=20000)
        page.wait_for_timeout(3000)
        
        page.click("button:has-text('Configuração')")
        page.wait_for_timeout(3000)
        
        p("Unhiding buttons...")
        page.evaluate("""() => {
            document.querySelectorAll("div").forEach(div => {
                if (div.className && div.className.includes("[&_button]:hidden")) {
                    div.className = div.className.replace("[&_button]:hidden", "");
                }
            });
        }""")
        page.wait_for_timeout(500)
        
        p("Clicking Editar on Times (trusted click)...")
        section = page.locator("div.rounded-xl", has_text="Times para apostar").first
        section.locator("button", has_text="Editar").click()
        
        page.wait_for_timeout(3000)
        
        import_btn = page.query_selector("button:has-text('Importar times')")
        p(f"Botão 'Importar times' apareceu? {import_btn is not None}")
        
        if import_btn:
            p("Uploading JSON...")
            page.set_input_files("input[type='file'][accept='.json']", json_file)
            page.wait_for_timeout(2000)
            
            p("Clicando em Salvar/Avançar...")
            avancar = page.query_selector("button:has-text('Avançar')")
            if avancar:
                avancar.click()
                page.wait_for_timeout(1000)
            
            salvar = page.query_selector("button:has-text('Salvar')")
            if salvar:
                salvar.click()
                page.wait_for_timeout(3000)
            
            p(f"Sucesso ao importar times para bot {bot_id}")
        else:
            p(f"Falha: botão de importar não apareceu no bot {bot_id}.")
            
    browser.close()
