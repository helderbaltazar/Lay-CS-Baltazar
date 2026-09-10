import sqlite3
import pandas as pd
import numpy as np

conn = sqlite3.connect('data_store/database.sqlite3')
query = """
    SELECT 
        HTGoalCount, odds_1st_half_under05, odds_ft_under25,
        Media_Gols_Total_Casa, Media_Gols_Total_Visitante,
        Media_Gols_no_1T_Casa, Media_Gols_no_1T_Visitante,
        Media_Pontos_Casa_Ate_Data, Media_de_Pontos_Visitante
    FROM telegram_dataset
    WHERE Media_Gols_no_1T_Casa IS NOT NULL 
      AND HTGoalCount IS NOT NULL
      AND odds_ft_under25 IS NOT NULL
"""
df = pd.read_sql_query(query, conn)
conn.close()

df['Soma_Media_HT'] = df['Media_Gols_no_1T_Casa'] + df['Media_Gols_no_1T_Visitante']
df['U05'] = (df['HTGoalCount'] < 0.5).astype(int)

df_u05 = df[df['odds_1st_half_under05'] > 1.0].copy()

best_roi = -100
best_u05 = None
for ft_u25_max in [1.5, 1.6, 1.7]:
    for max_ht in [1.0, 1.1, 1.2]:
        for min_odd in [2.3, 2.5, 2.7, 2.8]:
            for max_pts in [2.0, 3.0, 4.0]: # Soma dos pontos
                mask = (df_u05['odds_ft_under25'] <= ft_u25_max) & \
                       (df_u05['Soma_Media_HT'] <= max_ht) & \
                       (df_u05['odds_1st_half_under05'] >= min_odd) & \
                       ((df_u05['Media_Pontos_Casa_Ate_Data'] + df_u05['Media_de_Pontos_Visitante']) <= max_pts)
                
                t = mask.sum()
                if t < 400: continue
                
                sub = df_u05[mask]
                h = sub['U05'].sum()
                inv = t * 100
                ret = (sub[sub['U05'] == 1]['odds_1st_half_under05'] * 100).sum()
                roi = ((ret - inv) / inv) * 100
                if roi > best_roi:
                    best_roi = roi
                    best_u05 = (ft_u25_max, max_ht, min_odd, max_pts, t, h, h/t, roi)

if best_u05: print(f"U05 - FT_U25<={best_u05[0]:.2f} SomaHT<={best_u05[1]:.2f} Odd>={best_u05[2]:.2f} Pts<={best_u05[3]:.1f} | Apostas: {best_u05[4]} | WR: {best_u05[6]*100:.2f}% | ROI: {best_u05[7]:.2f}%")
