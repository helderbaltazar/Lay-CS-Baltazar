import datetime

# 1. Atualizando o scheduler.py
with open('scheduler.py', 'r') as f:
    sched_content = f.read()

old_scan = """def run_daily_scan():
    print(f"[{datetime.datetime.now()}] Iniciando scan diario...")
    today = datetime.datetime.now(pytz.timezone(config.SCHEDULER_TIMEZONE)).strftime("%Y-%m-%d")
    fixtures = get_fixtures(today)
    if not fixtures:
        print("Nenhum jogo encontrado para hoje ou cota de API excedida.")
        return
        
    model = PoissonDixonColes()
    results = scan_all(fixtures, model)
    rankings = rank_by_target(results)
    
    db = SessionLocal()
    try:
        save_to_db(db, rankings)
        print(f"[{datetime.datetime.now()}] Scan salvo com sucesso.")
    finally:
        db.close()"""

new_scan = """def run_daily_scan():
    print(f"[{datetime.datetime.now()}] Iniciando scan (Hoje e Amanha)...")
    now_br = datetime.datetime.now(pytz.timezone(config.SCHEDULER_TIMEZONE))
    today = now_br.strftime("%Y-%m-%d")
    tomorrow = (now_br + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    
    dates_to_scan = [today, tomorrow]
    model = PoissonDixonColes()
    db = SessionLocal()
    
    try:
        for d in dates_to_scan:
            print(f"Buscando jogos para a data: {d}")
            fixtures = get_fixtures(d)
            if not fixtures:
                print(f"Nenhum jogo importante encontrado para {d}.")
                continue
                
            results = scan_all(fixtures, model)
            rankings = rank_by_target(results)
            save_to_db(db, rankings)
        print(f"[{datetime.datetime.now()}] Scan (Hoje e Amanha) concluido e salvo com sucesso.")
    finally:
        db.close()"""

if old_scan in sched_content:
    sched_content = sched_content.replace(old_scan, new_scan)
    with open('scheduler.py', 'w') as f:
        f.write(sched_content)
    print("scheduler.py atualizado para escanear hoje e amanhã.")

# 2. Atualizando o app.py para repassar as datas para o template
with open('web/app.py', 'r') as f:
    app_content = f.read()

old_app_ret = 'return render_template("index.html", rankings=rankings, date_filter=date_obj.strftime("%Y-%m-%d"))'
new_app_ret = """now_br = datetime.datetime.now(pytz.timezone(config.SCHEDULER_TIMEZONE))
    today_str = now_br.strftime("%Y-%m-%d")
    tomorrow_str = (now_br + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    return render_template("index.html", rankings=rankings, date_filter=date_obj.strftime("%Y-%m-%d"), today_str=today_str, tomorrow_str=tomorrow_str)"""

if old_app_ret in app_content:
    app_content = app_content.replace(old_app_ret, new_app_ret)
    with open('web/app.py', 'w') as f:
        f.write(app_content)
    print("app.py atualizado para passar today_str e tomorrow_str.")

# 3. Atualizando a interface index.html
with open('web/templates/index.html', 'r') as f:
    html = f.read()

old_form = """<div class="card">
    <form method="GET" action="/">
        <label>Data: </label>
        <input type="date" name="date" value="{{ date_filter }}">
        <button type="submit">Buscar</button>
    </form>
</div>"""

new_form = """<div class="card" style="display: flex; gap: 15px; align-items: center;">
    <form method="GET" action="/" style="margin: 0;">
        <label>Data: </label>
        <input type="date" name="date" value="{{ date_filter }}">
        <button type="submit">Buscar</button>
    </form>
    <a href="/?date={{ today_str }}" class="badge" style="text-decoration: none; background: #0097e6; padding: 6px 12px;">Hoje</a>
    <a href="/?date={{ tomorrow_str }}" class="badge" style="text-decoration: none; background: #9c88ff; padding: 6px 12px;">Amanhã</a>
</div>"""

if old_form in html:
    html = html.replace(old_form, new_form)
    with open('web/templates/index.html', 'w') as f:
        f.write(html)
    print("Interface web atualizada com os botoes rápidos.")

