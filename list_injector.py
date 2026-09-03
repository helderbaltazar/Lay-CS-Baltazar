import config
import requests
from playwright.sync_api import sync_playwright
import json

with sync_playwright() as play:
    browser = play.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://bot-betfair.layback.trade/login", timeout=30000)
    page.click("text='Continuar com Betfair'")
    page.wait_for_selector("#username", timeout=15000)
    page.fill('#username', config.LAYBACK_EMAIL)
    page.fill('#password', config.LAYBACK_PASSWORD)
    page.click('#login')
    page.wait_for_selector("[href='/dashboard']", timeout=30000)
    
    cookies = context.cookies()
    session = requests.Session()
    for c in cookies:
        session.cookies.set(c['name'], c['value'], domain=c['domain'])
        
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "referer": "https://bot-betfair.layback.trade/lists",
    }
    
    # 1. Obter times para apostar (exemplo: lay 0 a 1)
    with open("data/bot_lay_0_1.json", "r") as f:
        data = json.load(f)
        
    active_teams = [t['name'] for t in data.get('teams', []) if t.get('checked')]
    print(f"Times ativos para Lay 0-1: {active_teams}")
    
    if not active_teams:
        print("Nenhum time ativo. Criando lista vazia...")
    else:
        # 2. Criar uma nova lista!
        list_name = "Lay CS - Jogos de Hoje/Amanha"
        r_create = session.post("https://bot-betfair.layback.trade/api/lists", headers=headers, json={"name": list_name})
        
        if r_create.status_code == 201:
            list_id = r_create.json()['data']['list']['id']
            print(f"Lista criada! ID: {list_id}")
            
            # Vamos tentar atualizar a lista com o filtro do time
            # Pela análise, o update de list aceita o mesmo schema
            # filter.team = nome do time? 
            # O sistema layback suporta apenas uma string em team? 
            # Ou podemos colocar todos os times separados por vírgula?
            
            # Como Lists é a única saída robusta sem Playwright UI-click, vamos atrelar
            
            bots = [150, 151, 152]
            for b in bots:
                r_assign = session.post(f"https://bot-betfair.layback.trade/api/lists/{list_id}/bot-assignments", 
                                        headers=headers, json={"botsId": [b]})
                print(f"Atribuindo lista {list_id} ao bot {b}: {r_assign.status_code}")
                
            # Now we must update the bot payload to usaLista: true, listaId: list_id
            for b in bots:
                r_get = session.get(f"https://bot-betfair.layback.trade/api/bots/{b}", headers=headers)
                bot_data = r_get.json()['data']['bot']
                bot_data['usaLista'] = True
                bot_data['listaId'] = list_id
                r_patch = session.patch(f"https://bot-betfair.layback.trade/api/bots/{b}", headers=headers, json=bot_data)
                print(f"Bot {b} usaLista atualizado: {r_patch.status_code}")
                
    browser.close()
