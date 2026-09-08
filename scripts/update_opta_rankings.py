import re
import json
import os
import subprocess

OPTA_JS_URL = "https://dataviz.theanalyst.com/opta-power-rankings/index.js"
OUTPUT_FILE = "data_store/opta_rankings.json"

def fetch_and_extract_opta():
    print(f"Buscando JS da Opta via curl...")
    result = subprocess.run(["curl", "-s", OPTA_JS_URL], capture_output=True, text=True)
    js_content = result.stdout
    
    if "contestantName" not in js_content:
        raise ValueError("Falha ao baixar o arquivo JS com curl.")

    print("Extraindo blocos JSON via Regex...")
    blocks = re.findall(r'\{"rank":\d+,"contestantId":.*?\}', js_content)
    
    teams = {}
    for block in blocks:
        rank_m = re.search(r'"currentGlobalRank":"?(\d+)"?', block)
        name_m = re.search(r'"contestantName":"([^"]+)"', block)
        rating_m = re.search(r'"currentRating":([\d.]+)', block)
        conf_rank_m = re.search(r'"currentConfederationRank":"?(\d+)"?', block)
        league_m = re.search(r"'competitionName':\s*'([^']+)'", block)
        
        if name_m and rating_m:
            name = name_m.group(1).encode('utf-8').decode('unicode_escape')
            rating = float(rating_m.group(1))
            global_rank = int(rank_m.group(1)) if rank_m else 99999
            conf_rank = int(conf_rank_m.group(1)) if conf_rank_m else 99999
            league = league_m.group(1) if league_m else "Unknown"
            
            if name not in teams or teams[name]['rating'] < rating:
                teams[name] = {
                    "name": name,
                    "rating": rating,
                    "global_rank": global_rank,
                    "confederation_rank": conf_rank,
                    "league": league
                }

    # Agora calcular o "Domestic Rank"
    league_teams = {}
    for t_name, data in teams.items():
        lg = data["league"]
        if lg not in league_teams:
            league_teams[lg] = []
        league_teams[lg].append(data)
        
    for lg, lst in league_teams.items():
        lst.sort(key=lambda x: x["rating"], reverse=True)
        for idx, t in enumerate(lst):
            teams[t["name"]]["domestic_rank"] = idx + 1
                
    if not teams:
        raise ValueError("Nenhum time extraído.")
        
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(teams, f, ensure_ascii=False, indent=2)
        
    print(f"Sucesso! {len(teams)} times únicos salvos.")

if __name__ == "__main__":
    fetch_and_extract_opta()
