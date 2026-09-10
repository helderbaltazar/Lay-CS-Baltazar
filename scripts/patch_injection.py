import re

with open("run_real_injection.py", "r") as f:
    content = f.read()

# Add sqlite3 import if not present
if "import sqlite3" not in content:
    content = content.replace("import pytz", "import pytz\nimport sqlite3")
    
# Add the historical cache and filter function
historical_func = """
_historical_names_cache = []
_historical_stats_cache = {}

def get_historical_stats(team_name):
    global _historical_names_cache, _historical_stats_cache
    import sqlite3
    import difflib
    
    conn = sqlite3.connect('data_store/database.sqlite3')
    
    if not _historical_names_cache:
        c = conn.cursor()
        c.execute("SELECT DISTINCT home_name FROM telegram_dataset WHERE home_name IS NOT NULL")
        rows = c.fetchall()
        _historical_names_cache = [r[0] for r in rows]
        
    if team_name in _historical_stats_cache:
        conn.close()
        return _historical_stats_cache[team_name]
        
    # Find closest match
    matches = difflib.get_close_matches(team_name, _historical_names_cache, n=1, cutoff=0.5)
    if not matches:
        conn.close()
        return None
        
    matched_name = matches[0]
    query = '''
        SELECT 
            AVG(Media_Gols_no_1T_Casa),
            AVG(Efic_xG_Casa)
        FROM telegram_dataset
        WHERE home_name = ?
    '''
    c = conn.cursor()
    c.execute(query, (matched_name,))
    row = c.fetchone()
    conn.close()
    
    if row and row[0] is not None and row[1] is not None:
        stats = {"media_ht": float(row[0]), "efic_xg": float(row[1])}
        _historical_stats_cache[team_name] = stats
        return stats
    return None

def check_golden_filters(home_team, away_team, target, power_score):
    if target not in ["UNDER_0.5_HT", "UNDER_1.5_HT", "UNDER_2.5_HT"]:
        return True # Nao aplica filtros de ouro para outros mercados
        
    h_stats = get_historical_stats(home_team)
    a_stats = get_historical_stats(away_team)
    
    if not h_stats or not a_stats:
        print(f"      [Filtro] Sem dados hist. p/ {home_team} ou {away_team}")
        return False
        
    soma_ht = h_stats["media_ht"] + a_stats["media_ht"]
    efic_home = h_stats["efic_xg"]
    efic_away = a_stats["efic_xg"]
    
    if target == "UNDER_0.5_HT":
        if power_score >= 30 and soma_ht <= 1.2 and efic_home <= 1.0 and efic_away <= 1.0:
            print(f"      [U05 Ouro] SomaHT={soma_ht:.2f}, EficH={efic_home:.2f}, EficA={efic_away:.2f}")
            return True
            
    elif target == "UNDER_1.5_HT":
        if soma_ht <= 1.4:
            print(f"      [U15 Ouro] SomaHT={soma_ht:.2f}")
            return True
            
    elif target == "UNDER_2.5_HT":
        if soma_ht <= 1.8 and efic_home <= 1.0 and efic_away <= 1.0:
            print(f"      [U25 Ouro] SomaHT={soma_ht:.2f}, EficH={efic_home:.2f}, EficA={efic_away:.2f}")
            return True
            
    return False
"""

if "def check_golden_filters" not in content:
    content = content.replace("def is_injection_completed_today():", historical_func + "\n\ndef is_injection_completed_today():")


# Add new targets and import bot IDs
if "LAY_U05_HT_BOT_ID" not in content:
    content = content.replace(
        "LAY_1_3_BOT_ID",
        "LAY_1_3_BOT_ID, LAY_U05_HT_BOT_ID, LAY_U15_HT_BOT_ID, LAY_U25_HT_BOT_ID"
    )
    
if "LAY_U05_HT_BOT_ID" in content and "(\"UNDER_0.5_HT" not in content:
    old_targets = '''    targets = [
        (LAY_0_1_BOT_ID, "bot_lay_0_1", "0-1"),
        (LAY_0_2_BOT_ID, "bot_lay_0_2", "0-2"),
        (LAY_0_3_BOT_ID, "bot_lay_0_3", "0-3"),
        (LAY_1_3_BOT_ID, "bot_lay_1_3", "1-3"),
    ]'''
    
    new_targets = '''    targets = [
        (LAY_0_1_BOT_ID, "bot_lay_0_1", "0-1"),
        (LAY_0_2_BOT_ID, "bot_lay_0_2", "0-2"),
        (LAY_0_3_BOT_ID, "bot_lay_0_3", "0-3"),
        (LAY_1_3_BOT_ID, "bot_lay_1_3", "1-3"),
        (LAY_U05_HT_BOT_ID, "bot_u05_ht", "UNDER_0.5_HT"),
        (LAY_U15_HT_BOT_ID, "bot_u15_ht", "UNDER_1.5_HT"),
        (LAY_U25_HT_BOT_ID, "bot_u25_ht", "UNDER_2.5_HT"),
    ]'''
    content = content.replace(old_targets, new_targets)


# Remove match_odd restriction for the new markets in the loop
old_query = '''        preds = db.query(Prediction).join(Match).filter(
            Prediction.target_score == target,
            Prediction.power_score >= threshold,
            Prediction.match_odd != None,
            Prediction.match_odd <= 2.0,
            Match.date >= today_start
        ).order_by(
            Prediction.power_score.desc().nullslast(),
        ).all()'''
        
new_query = '''        
        # Filtro base do banco de dados
        if "UNDER_" in target:
            # Para Unders, não restringimos a odd do match winner (porque não é relevante pro Layback aqui)
            preds = db.query(Prediction).join(Match).filter(
                Prediction.target_score == target,
                Prediction.power_score >= threshold,
                Match.date >= today_start
            ).order_by(
                Prediction.power_score.desc().nullslast(),
            ).all()
        else:
            preds = db.query(Prediction).join(Match).filter(
                Prediction.target_score == target,
                Prediction.power_score >= threshold,
                Prediction.match_odd != None,
                Prediction.match_odd <= 2.0,
                Match.date >= today_start
            ).order_by(
                Prediction.power_score.desc().nullslast(),
            ).all()'''

content = content.replace(old_query, new_query)


# Add the Golden Filter check inside the injection loop
old_loop = '''        bot_games_str = []
        teams_data = []
        for p in preds:
            m = p.match
            conf_str = f" [Score: {p.power_score:.1f}]" if p.power_score else ""
            print(f"[{target}] {m.home_team} x {m.away_team} {conf_str}")
            bot_games_str.append(f"⚽ {m.home_team} x {m.away_team} {conf_str}")
            h_bf = get_betfair_id(m.home_team, layback_teams)
            a_bf = get_betfair_id(m.away_team, layback_teams)
            if h_bf: teams_data.append(h_bf)
            if a_bf: teams_data.append(a_bf)'''

new_loop = '''        bot_games_str = []
        teams_data = []
        for p in preds:
            m = p.match
            
            # Filtro Histórico Ouro para novos mercados
            if "UNDER_" in target:
                if not check_golden_filters(m.home_team, m.away_team, target, p.power_score):
                    continue
            
            conf_str = f" [Score: {p.power_score:.1f}]" if p.power_score else ""
            print(f"[{target}] {m.home_team} x {m.away_team} {conf_str}")
            bot_games_str.append(f"⚽ {m.home_team} x {m.away_team} {conf_str}")
            h_bf = get_betfair_id(m.home_team, layback_teams)
            a_bf = get_betfair_id(m.away_team, layback_teams)
            if h_bf: teams_data.append(h_bf)
            if a_bf: teams_data.append(a_bf)'''

content = content.replace(old_loop, new_loop)

# Adjust thresholds for Under HT 
old_threshold = '''        if target == "0-1": threshold = 94.0
        elif target == "0-2": threshold = 94.0
        elif target == "0-3": threshold = 99.20
        elif target == "1-3": threshold = 99.31
        else: threshold = 99.0'''
        
new_threshold = '''        if target == "0-1": threshold = 94.0
        elif target == "0-2": threshold = 94.0
        elif target == "0-3": threshold = 99.20
        elif target == "1-3": threshold = 99.31
        elif target == "UNDER_0.5_HT": threshold = 30.0 # Aprovado na nossa IA
        elif target == "UNDER_1.5_HT": threshold = 0.0 # Controlado só pelo SomaHT
        elif target == "UNDER_2.5_HT": threshold = 0.0 # Controlado só pelo SomaHT
        else: threshold = 99.0'''

content = content.replace(old_threshold, new_threshold)

with open("run_real_injection.py", "w") as f:
    f.write(content)

print("Patch aplicado com sucesso!")
