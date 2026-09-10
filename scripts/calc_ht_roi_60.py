import sqlite3
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.poisson import PoissonDixonColes

conn = sqlite3.connect('data_store/database.sqlite3')
query = """
    SELECT 
        HTGoalCount, odds_1st_half_under05, Media_Gols_Total_Casa, Media_Gols_Total_Visitante
    FROM telegram_dataset
    WHERE Media_Gols_Total_Casa IS NOT NULL 
      AND Media_Gols_Total_Visitante IS NOT NULL
      AND HTGoalCount IS NOT NULL
      AND odds_1st_half_under05 IS NOT NULL
"""
df = pd.read_sql_query(query, conn)
conn.close()

model = PoissonDixonColes(rho=-0.10)

invested = 0
returned = 0
matches = 0
hits = 0

for idx, row in df.iterrows():
    lam_home = float(row['Media_Gols_Total_Casa'])
    lam_away = float(row['Media_Gols_Total_Visitante'])
    if lam_home == 0 and lam_away == 0: continue
        
    probs = model.get_extra_probabilities(lam_home, lam_away)
    score_05 = probs["UNDER_0.5_HT"] * 100
    
    if score_05 >= 60:
        odd = float(row['odds_1st_half_under05'])
        if odd > 1.0:
            matches += 1
            invested += 100
            if int(row['HTGoalCount']) < 0.5:
                hits += 1
                returned += 100 * odd

if matches > 0:
    print(f"Total Matches >= 60: {matches}")
    print(f"Hits: {hits}")
    print(f"Win Rate: {(hits/matches)*100:.2f}%")
    print(f"Investido: R$ {invested:.2f}")
    print(f"Retornado: R$ {returned:.2f}")
    print(f"Lucro: R$ {returned-invested:.2f}")
    print(f"ROI: {((returned-invested)/invested)*100:.2f}%")
