import sqlite3
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.poisson import PoissonDixonColes

# Connect to database
conn = sqlite3.connect('data_store/database.sqlite3')
query = """
    SELECT 
        HTGoalCount, odds_1st_half_under05, Media_Gols_Total_Casa, Media_Gols_Total_Visitante
    FROM telegram_dataset
    WHERE Media_Gols_Total_Casa IS NOT NULL 
      AND Media_Gols_Total_Visitante IS NOT NULL
      AND HTGoalCount IS NOT NULL
"""
df = pd.read_sql_query(query, conn)
conn.close()

model = PoissonDixonColes(rho=-0.10)

cutoffs = {
    "UNDER_0.5_HT": [40, 50, 60], 
    "UNDER_1.5_HT": [70, 75, 80], 
    "UNDER_2.5_HT": [85, 90, 95]
}

results = {c: {k: {"m": 0, "h": 0} for k in cutoffs[c]} for c in cutoffs}

for idx, row in df.iterrows():
    lam_home = float(row['Media_Gols_Total_Casa'])
    lam_away = float(row['Media_Gols_Total_Visitante'])
    if lam_home == 0 and lam_away == 0: continue
        
    probs = model.get_extra_probabilities(lam_home, lam_away)
    ht_goals = int(row['HTGoalCount'])
    
    score_05 = probs["UNDER_0.5_HT"] * 100
    for k in cutoffs["UNDER_0.5_HT"]:
        if score_05 >= k:
            results["UNDER_0.5_HT"][k]["m"] += 1
            if ht_goals < 0.5: results["UNDER_0.5_HT"][k]["h"] += 1

    score_15 = probs["UNDER_1.5_HT"] * 100
    for k in cutoffs["UNDER_1.5_HT"]:
        if score_15 >= k:
            results["UNDER_1.5_HT"][k]["m"] += 1
            if ht_goals < 1.5: results["UNDER_1.5_HT"][k]["h"] += 1
            
    score_25 = probs["UNDER_2.5_HT"] * 100
    for k in cutoffs["UNDER_2.5_HT"]:
        if score_25 >= k:
            results["UNDER_2.5_HT"][k]["m"] += 1
            if ht_goals < 2.5: results["UNDER_2.5_HT"][k]["h"] += 1

print("\n=== UNDER HT ESCALONADO ===")
for market in results:
    for k in cutoffs[market]:
        m = results[market][k]["m"]
        h = results[market][k]["h"]
        if m > 0:
            wr = (h / m) * 100
            print(f"{market} >= {k}: Apostas: {m} | Acertos: {h} | WR: {wr:.2f}% | Odd Justa: {100/wr:.2f}")
