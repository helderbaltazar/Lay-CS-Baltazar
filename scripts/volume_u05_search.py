import sqlite3
import pandas as pd
import numpy as np

conn = sqlite3.connect('data_store/database.sqlite3')
query = """
    SELECT 
        HTGoalCount, odds_1st_half_under05, odds_ft_under25,
        Media_Gols_Total_Casa, Media_Gols_Total_Visitante,
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

print("=== BUSCANDO VOLUME PARA UNDER 0.5 HT ===")
best_roi = 0

# Test combinations
for min_odd in [2.3, 2.4, 2.5, 2.6]:
    for max_ft_u25 in [1.6, 1.7, 1.8, 1.9]:
        for max_ht_goals in [1.2, 1.3, 1.4]:
            for max_efic in [2.0, 2.2, 2.4]: # Soma de eficiência (ex: 1.0 + 1.0)
                
                mask = (df['odds_1st_half_under05'] >= min_odd) & \
                       (df['odds_ft_under25'] <= max_ft_u25) & \
                       (df['Soma_Media_HT'] <= max_ht_goals) & \
                       (df['Soma_Efic_xG'] <= max_efic) & \
                       (df['Soma_Efic_xG'] > 0)
                
                t = mask.sum()
                if t < 400: continue
                
                sub = df[mask]
                h = sub['U05'].sum()
                inv = t * 100
                ret = (sub[sub['U05'] == 1]['odds_1st_half_under05'] * 100).sum()
                roi = ((ret - inv) / inv) * 100
                
                if roi > 3.0: # Only print if ROI is somewhat profitable
                    print(f"OddU05>={min_odd:.2f} | OddU25FT<={max_ft_u25:.2f} | SomaHT<={max_ht_goals:.1f} | SomaEfic<={max_efic:.1f} -> Vol: {t} | Acertos: {h} | WR: {h/t*100:.2f}% | ROI: {roi:.2f}%")

