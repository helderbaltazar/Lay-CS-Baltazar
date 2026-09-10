import sqlite3
import pandas as pd
import numpy as np

conn = sqlite3.connect('data_store/database.sqlite3')
query = """
    SELECT 
        HTGoalCount, odds_1st_half_under05, odds_ft_under25,
        Media_Gols_no_1T_Casa, Media_Gols_no_1T_Visitante,
        Efic_xG_Casa, Efic_xG_Visitante
    FROM telegram_dataset
    WHERE Media_Gols_no_1T_Casa IS NOT NULL 
      AND HTGoalCount IS NOT NULL
      AND odds_1st_half_under05 IS NOT NULL
      AND odds_ft_under25 IS NOT NULL
      AND Efic_xG_Casa IS NOT NULL
"""
df = pd.read_sql_query(query, conn)
conn.close()

df['Soma_Media_HT'] = df['Media_Gols_no_1T_Casa'] + df['Media_Gols_no_1T_Visitante']
df['Soma_Efic_xG'] = df['Efic_xG_Casa'] + df['Efic_xG_Visitante']
df['U05'] = (df['HTGoalCount'] < 0.5).astype(int)

df = df[df['odds_1st_half_under05'] > 1.0]

results = []
for min_odd in [2.3, 2.4, 2.5]:
    for max_ft_u25 in [1.5, 1.6, 1.7, 1.8]:
        for max_ht_goals in [1.2, 1.3, 1.4]:
            for max_efic in [1.8, 2.0, 2.2]:
                
                mask = (df['odds_1st_half_under05'] >= min_odd) & \
                       (df['odds_ft_under25'] <= max_ft_u25) & \
                       (df['Soma_Media_HT'] <= max_ht_goals) & \
                       (df['Soma_Efic_xG'] <= max_efic) & \
                       (df['Soma_Efic_xG'] > 0)
                
                t = mask.sum()
                if t < 300: continue
                
                sub = df[mask]
                h = sub['U05'].sum()
                inv = t * 100
                ret = (sub[sub['U05'] == 1]['odds_1st_half_under05'] * 100).sum()
                roi = ((ret - inv) / inv) * 100
                
                results.append((roi, t, min_odd, max_ft_u25, max_ht_goals, max_efic))

results.sort(reverse=True)
for r in results[:15]:
    print(f"ROI: {r[0]:.2f}% | Vol: {r[1]} | OddU05>={r[2]:.2f} | OddU25FT<={r[3]:.2f} | SomaHT<={r[4]:.1f} | SomaEfic<={r[5]:.1f}")
