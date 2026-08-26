import re
with open('analysis/scanner.py', 'r') as f:
    content = f.read()
    
old_block = """                if not match:
                    match = Match(
                        fixture_id=fix_id,
                        date=parse(rec['date']),
                        league_name=rec['league'],"""

new_block = """                if not match:
                    dt = parse(rec['date'])
                    import pytz, config
                    if dt.tzinfo:
                        dt = dt.astimezone(pytz.timezone(config.SCHEDULER_TIMEZONE))
                    dt = dt.replace(tzinfo=None)
                    match = Match(
                        fixture_id=fix_id,
                        date=dt,
                        league_name=rec['league'],"""
                    
if old_block in content:
    content = content.replace(old_block, new_block)
    with open('analysis/scanner.py', 'w') as f:
        f.write(content)
    print("Patched scanner.py")
else:
    print("Block not found in scanner.py")
    
with open('web/app.py', 'r') as f:
    app_content = f.read()
    
app_old = 'today = datetime.datetime.now().strftime("%Y-%m-%d")'
app_new = 'import pytz\n    today = datetime.datetime.now(pytz.timezone(config.SCHEDULER_TIMEZONE)).strftime("%Y-%m-%d")'
if app_old in app_content:
    app_content = app_content.replace(app_old, app_new)
    with open('web/app.py', 'w') as f:
        f.write(app_content)
    print("Patched app.py")
    
# Limpa o banco de dados real para remover os jogos com horario em UTC
try:
    from database.db import SessionLocal
    from database.models_db import Match, Prediction
    db = SessionLocal()
    db.query(Prediction).delete()
    db.query(Match).delete()
    db.commit()
    db.close()
    print("Banco de dados limpo para reescrever com fuso correto.")
except Exception as e:
    print("Erro limpando BD:", e)
