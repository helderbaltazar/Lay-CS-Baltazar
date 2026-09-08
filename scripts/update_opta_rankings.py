import re
import json
import requests
import os

OPTA_JS_URL = "https://dataviz.theanalyst.com/opta-power-rankings/index.js"
OUTPUT_FILE = "data_store/opta_rankings.json"

def fetch_and_extract_opta():
    print(f"Buscando JS da Opta em {OPTA_JS_URL}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    
    response = requests.get(OPTA_JS_URL, headers=headers)
    response.raise_for_status()
    js_content = response.text
    
    print("Extraindo blocos JSON via Regex...")
    blocks = re.findall(r'\{"rank":\d+,"contestantId":.*?\}', js_content)
    
    teams = {}
    for block in blocks:
        rank_m = re.search(r'"globalRank":([\d.]+)', block)
        name_m = re.search(r'"contestantName":"([^"]+)"', block)
        rating_m = re.search(r'"currentRating":([\d.]+)', block)
        
        if name_m and rating_m:
            name = name_m.group(1)
            rating = float(rating_m.group(1))
            rank = int(float(rank_m.group(1))) if rank_m else 99999
            
            # Como a Opta lista times femininos também, nós vamos dar preferência ao time
            # com maior rating se o nome for idêntico (geralmente o masculino principal)
            if name not in teams or teams[name]['rating'] < rating:
                teams[name] = {
                    "name": name,
                    "rating": rating,
                    "global_rank": rank
                }
                
    if not teams:
        raise ValueError("Nenhum time extraído. A estrutura do site pode ter mudado.")
        
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(teams, f, ensure_ascii=False, indent=2)
        
    print(f"Sucesso! {len(teams)} times únicos salvos em {OUTPUT_FILE}.")

if __name__ == "__main__":
    fetch_and_extract_opta()
