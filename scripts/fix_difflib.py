import re

with open("run_real_injection.py", "r") as f:
    content = f.read()
    
new_func = """def get_historical_stats(team_name):
    global _historical_names_cache, _historical_stats_cache
    import sqlite3
    import difflib
    
    if not team_name:
        return None
        
    conn = sqlite3.connect('data_store/database.sqlite3')
    
    if not _historical_names_cache:
        c = conn.cursor()
        c.execute("SELECT DISTINCT home_name FROM telegram_dataset WHERE home_name IS NOT NULL")
        rows = c.fetchall()
        _historical_names_cache = [r[0] for r in rows if r[0] is not None]
        
    if team_name in _historical_stats_cache:
        conn.close()
        return _historical_stats_cache[team_name]
        
    # Find closest match
    matches = difflib.get_close_matches(team_name, _historical_names_cache, n=1, cutoff=0.5)
    if not matches:
        conn.close()
        return None"""

content = re.sub(r"def get_historical_stats\(team_name\):.*?if not matches:\n\s+conn\.close\(\)\n\s+return None", new_func, content, flags=re.DOTALL)

with open("run_real_injection.py", "w") as f:
    f.write(content)
