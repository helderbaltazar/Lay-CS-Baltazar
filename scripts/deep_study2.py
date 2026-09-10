import sqlite3
import pandas as pd
import numpy as np

conn = sqlite3.connect('data_store/database.sqlite3')
query = """
    SELECT 
        HTGoalCount, odds_1st_half_under05, 
        Media_Gols_Total_Casa, Media_Gols_Total_Visitante,
        Media_Gols_no_1T_Casa, Media_Gols_no_1T_Visitante
    FROM telegram_dataset
    WHERE Media_Gols_no_1T_Casa IS NOT NULL 
      AND Media_Gols_no_1T_Visitante IS NOT NULL
      AND HTGoalCount IS NOT NULL
"""
df = pd.read_sql_query(query, conn)
conn.close()

df['Soma_Media_HT'] = df['Media_Gols_no_1T_Casa'] + df['Media_Gols_no_1T_Visitante']
df['Soma_Media_FT'] = df['Media_Gols_Total_Casa'] + df['Media_Gols_Total_Visitante']

df['U05'] = (df['HTGoalCount'] < 0.5).astype(int)
df['U15'] = (df['HTGoalCount'] < 1.5).astype(int)
df['U25'] = (df['HTGoalCount'] < 2.5).astype(int)

df_u05 = df[df['odds_1st_half_under05'] > 1.0].copy()

# Under 0.5
best_roi = -100
best_u05 = None
for max_ht in np.arange(0.8, 1.6, 0.1):
    for min_odd in [2.3, 2.5, 2.6, 2.7, 2.8]:
        mask = (df_u05['Soma_Media_HT'] <= max_ht) & (df_u05['odds_1st_half_under05'] >= min_odd)
        t = mask.sum()
        if t < 500: continue
        
        sub = df_u05[mask]
        h = sub['U05'].sum()
        inv = t * 100
        ret = (sub[sub['U05'] == 1]['odds_1st_half_under05'] * 100).sum()
        roi = ((ret - inv) / inv) * 100
        if roi > best_roi:
            best_roi = roi
            best_u05 = (max_ht, min_odd, t, h, h/t, roi)

if best_u05: print(f"U05 - HT<={best_u05[0]:.2f} Odd>={best_u05[1]:.2f} | Apostas: {best_u05[2]} | WR: {best_u05[4]*100:.2f}% | ROI: {best_u05[5]:.2f}%")

# Under 1.5
best_wr = 0
best_u15 = None
for max_ht in np.arange(0.9, 1.8, 0.1):
    mask = (df['Soma_Media_HT'] <= max_ht)
    t = mask.sum()
    if t < 1000: continue
    
    h = df[mask]['U15'].sum()
    wr = h / t
    if wr > best_wr:
        best_wr = wr
        best_u15 = (max_ht, t, h, wr)

if best_u15: print(f"U15 - HT<={best_u15[0]:.2f} | Apostas: {best_u15[1]} | WR: {best_u15[3]*100:.2f}% | Odd Justa: {100/(best_u15[3]*100):.2f}")

# Under 2.5
best_wr = 0
best_u25 = None
for max_ht in np.arange(1.0, 2.0, 0.1):
    mask = (df['Soma_Media_HT'] <= max_ht)
    t = mask.sum()
    if t < 2000: continue
    
    h = df[mask]['U25'].sum()
    wr = h / t
    if wr > best_wr:
        best_wr = wr
        best_u25 = (max_ht, t, h, wr)

if best_u25: print(f"U25 - HT<={best_u25[0]:.2f} | Apostas: {best_u25[1]} | WR: {best_u25[3]*100:.2f}% | Odd Justa: {100/(best_u25[3]*100):.2f}")
