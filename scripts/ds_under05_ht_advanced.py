import sqlite3
import pandas as pd
import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.poisson import PoissonDixonColes

conn = sqlite3.connect('data_store/database.sqlite3')
query = """
    SELECT 
        HTGoalCount, odds_1st_half_under05, 
        Media_Gols_Total_Casa, Media_Gols_Total_Visitante,
        Media_Gols_no_1T_Casa, Media_Gols_no_1T_Visitante,
        Media_Pontos_Casa_Ate_Data, Media_de_Pontos_Visitante
    FROM telegram_dataset
    WHERE Media_Gols_no_1T_Casa IS NOT NULL 
      AND HTGoalCount IS NOT NULL
      AND odds_1st_half_under05 IS NOT NULL
"""
df = pd.read_sql_query(query, conn)
conn.close()

df = df[df['odds_1st_half_under05'] > 1.0].copy()
df['Is_Under_05'] = (df['HTGoalCount'] < 0.5).astype(int)
df['Soma_Media_HT'] = df['Media_Gols_no_1T_Casa'] + df['Media_Gols_no_1T_Visitante']

# Calculate Poisson probabilities for all rows
model = PoissonDixonColes(rho=-0.10)
poisson_scores = []
for idx, row in df.iterrows():
    lam_home = float(row.get('Media_Gols_Total_Casa', 0) or 0)
    lam_away = float(row.get('Media_Gols_Total_Visitante', 0) or 0)
    if lam_home == 0 and lam_away == 0:
        poisson_scores.append(0)
    else:
        probs = model.get_extra_probabilities(lam_home, lam_away)
        poisson_scores.append(probs["UNDER_0.5_HT"] * 100)

df['Poisson_Under05'] = poisson_scores

def test_filter(mask, name):
    sub = df[mask]
    t = len(sub)
    if t == 0: return
    h = sub['Is_Under_05'].sum()
    wr = h / t
    inv = t * 100
    ret = (sub[sub['Is_Under_05'] == 1]['odds_1st_half_under05'] * 100).sum()
    roi = ((ret - inv) / inv) * 100
    if t >= 40 and roi > 10:
        print(f"[{name}] Apostas: {t} | Acertos: {h} | WR: {wr*100:.2f}% | Odd Média: {sub[sub['Is_Under_05'] == 1]['odds_1st_half_under05'].mean():.2f} | ROI: {roi:.2f}%")

# Grid Search
for p_score in [20, 25, 30, 35, 40]:
    for max_ht in [0.7, 0.8, 0.9, 1.0]:
        for min_odd in [2.5, 2.7, 2.9, 3.1]:
            mask = (df['Poisson_Under05'] >= p_score) & (df['Soma_Media_HT'] <= max_ht) & (df['odds_1st_half_under05'] >= min_odd)
            test_filter(mask, f"Poisson >= {p_score} | SomaHT <= {max_ht} | Odd >= {min_odd}")

