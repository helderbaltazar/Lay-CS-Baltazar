import sqlite3
import pandas as pd
import numpy as np

conn = sqlite3.connect('data_store/database.sqlite3')
query = """
    SELECT 
        HTGoalCount, odds_1st_half_under05, 
        Media_Gols_Total_Casa, Media_Gols_Total_Visitante,
        Media_Gols_no_1T_Casa, Media_Gols_no_1T_Visitante,
        Media_Pontos_Casa_Ate_Data, Media_de_Pontos_Visitante
    FROM telegram_dataset
    WHERE Media_Gols_no_1T_Casa IS NOT NULL 
      AND Media_Gols_no_1T_Visitante IS NOT NULL
      AND HTGoalCount IS NOT NULL
      AND odds_1st_half_under05 IS NOT NULL
"""
df = pd.read_sql_query(query, conn)
conn.close()

# Filter basic anomalies
df = df[df['odds_1st_half_under05'] > 1.0].copy()

# Add a target column (1 if Under 0.5 HT, else 0)
df['Is_Under_05'] = (df['HTGoalCount'] < 0.5).astype(int)

# 1. Baseline
total = len(df)
hits = df['Is_Under_05'].sum()
print(f"BASELINE: {total} jogos, {hits} acertos ({hits/total*100:.2f}%). Odd media: {df['odds_1st_half_under05'].mean():.2f}")

# Function to test a filter
def test_filter(mask, name):
    sub = df[mask]
    t = len(sub)
    if t == 0: return
    h = sub['Is_Under_05'].sum()
    wr = h / t
    inv = t * 100
    ret = (sub[sub['Is_Under_05'] == 1]['odds_1st_half_under05'] * 100).sum()
    roi = ((ret - inv) / inv) * 100
    if t >= 30 and roi > 5:
        print(f"[{name}] Apostas: {t} | WR: {wr*100:.2f}% | Odd Média Acertos: {sub[sub['Is_Under_05'] == 1]['odds_1st_half_under05'].mean():.2f} | ROI: {roi:.2f}%")

df['Soma_Media_HT'] = df['Media_Gols_no_1T_Casa'] + df['Media_Gols_no_1T_Visitante']
df['Soma_Media_Total'] = df['Media_Gols_Total_Casa'] + df['Media_Gols_Total_Visitante']

# Let's loop through combinations of odds ranges and historical averages
for max_ht_goals in [0.7, 0.8, 0.9, 1.0, 1.1]:
    for min_odd in [2.5, 2.7, 2.9, 3.0, 3.2]:
        for max_odd in [3.0, 3.2, 3.5, 4.0, 5.0]:
            if min_odd >= max_odd: continue
            
            mask = (df['Soma_Media_HT'] <= max_ht_goals) & (df['odds_1st_half_under05'] >= min_odd) & (df['odds_1st_half_under05'] <= max_odd)
            test_filter(mask, f"SomaHT <= {max_ht_goals} | {min_odd} <= Odd <= {max_odd}")

