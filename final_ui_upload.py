import config
import time
import os
from playwright.sync_api import sync_playwright

with sync_playwright() as play:
    browser = play.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1280, 'height': 3000})
    
    print("Fazendo login...")
    page.goto("https://bot-betfair.layback.trade/login")
    page.click("text='Continuar com Betfair'")
    page.wait_for_selector("#username", timeout=15000)
    page.fill('#username', config.LAYBACK_EMAIL)
    page.fill('#password', config.LAYBACK_PASSWORD)
    page.click('#login')
    page.wait_for_selector("[href='/dashboard']", timeout=30000)
    
    bot_id = 4626
    print(f"Navegando para edição do bot {bot_id}...")
    page.goto(f"https://bot-betfair.layback.trade/bots/{bot_id}/edit", wait_until="networkidle")
    time.sleep(3)
    
    # Rolar a página para ver tudo
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(1)
    
    # Clicar na aba "Times" (accordion)
    print("Expandindo aba Times...")
    aba_times = page.locator("text='Times'")
    # É possível que seja "7. Times" ou apenas contém "Times"
    if aba_times.count() > 0:
        aba_times.last.click() # last porque o breadcrumb pode ter Times também
        time.sleep(2)
        
        # Procurar o botão Importar
        print("Procurando botão Importar...")
        importar = page.locator("button:has-text('Importar')")
        if importar.count() > 0:
            importar.first.click()
            time.sleep(1)
            
            # Fazer upload do arquivo
            print("Fazendo upload do JSON...")
            file_input = page.locator("input[type='file']")
            if file_input.count() > 0:
                json_path = os.path.abspath("data/bot_lay_0_1.json")
                file_input.first.set_input_files(json_path)
                time.sleep(3)
                
                print("Procurando 'Ver selecionados'...")
                # Expandir para ver os selecionados (gerar evidencia)
                ver_sel = page.locator("button:has-text('selecionados')")
                if ver_sel.count() > 0:
                    ver_sel.first.click()
                    time.sleep(2)
                    page.screenshot(path=f"logs/evidencia_bot_{bot_id}.png", full_page=True)
                    print(f"Evidência salva em logs/evidencia_bot_{bot_id}.png")
                
                # Salvar o bot
                print("Salvando o bot...")
                salvar = page.locator("button:has-text('Salvar Bot')")
                if salvar.count() > 0:
                    salvar.first.click()
                    time.sleep(5)
                    print("Upload e salvamento CONCLUÍDOS!")
                else:
                    print("Botão Salvar Bot não encontrado")
            else:
                print("Input de arquivo não encontrado")
        else:
            print("Botão Importar não encontrado")
            page.screenshot(path="logs/debug_importar_error.png", full_page=True)
    else:
        print("Aba Times não encontrada")
        page.screenshot(path="logs/debug_aba_error.png", full_page=True)
        
    browser.close()
