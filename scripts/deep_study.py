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
"""
df = pd.read_sql_query(query, conn)
conn.close()

# Feature Engineering
df['Soma_Media_HT'] = df['Media_Gols_no_1T_Casa'] + df['Media_Gols_no_1T_Visitante']
df['Soma_Media_FT'] = df['Media_Gols_Total_Casa'] + df['Media_Gols_Total_Visitante']
df['Soma_Pontos'] = df.get('Media_Pontos_Casa_Ate_Data', 0) + df.get('Media_de_Pontos_Visitante', 0)

# Targets
df['U05'] = (df['HTGoalCount'] < 0.5).astype(int)
df['U15'] = (df['HTGoalCount'] < 1.5).astype(int)
df['U25'] = (df['HTGoalCount'] < 2.5).astype(int)

# 1. UNDER 0.5 HT (Optimize for ROI & Volume > 500)
print("=== ESTUDO PROFUNDO: UNDER 0.5 HT ===")
best_roi = -100
best_u05 = None
df_u05 = df[df['odds_1st_half_under05'] > 1.0].copy()

# Grid Search U05
for max_ht in np.arange(0.7, 1.4, 0.1):
    for max_ft in np.arange(2.0, 3.0, 0.2):
        for min_odd in [2.3, 2.5, 2.7, 2.8]:
            mask = (df_u05['Soma_Media_HT'] <= max_ht) & (df_u05['Soma_Media_FT'] <= max_ft) & (df_u05['odds_1st_half_under05'] >= min_odd)
            t = mask.sum()
            if t < 1000: continue
            
            sub = df_u05[mask]
            h = sub['U05'].sum()
            inv = t * 100
            ret = (sub[sub['U05'] == 1]['odds_1st_half_under05'] * 100).sum()
            roi = ((ret - inv) / inv) * 100
            
            if roi > best_roi:
                best_roi = roi
                best_u05 = (max_ht, max_ft, min_odd, t, h, h/t, roi)

if best_u05:
    print(f"Melhor Filtro U05: Soma_Media_HT <= {best_u05[0]:.1f} | Soma_Media_FT <= {best_u05[1]:.1f} | Odd >= {best_u05[2]:.1f}")
    print(f"Volume: {best_u05[3]} apostas | WR: {best_u05[5]*100:.2f}% | ROI: {best_u05[6]:.2f}%")


# 2. UNDER 1.5 HT (Optimize for WR & Volume > 3000)
print("\n=== ESTUDO PROFUNDO: UNDER 1.5 HT ===")
best_wr_15 = 0
best_u15 = None

for max_ht in np.arange(0.9, 1.6, 0.1):
    for max_ft in np.arange(2.2, 3.2, 0.2):
        mask = (df['Soma_Media_HT'] <= max_ht) & (df['Soma_Media_FT'] <= max_ft)
        t = mask.sum()
        if t < 3000: continue
        
        h = df[mask]['U15'].sum()
        wr = h / t
        
        if wr > best_wr_15:
            best_wr_15 = wr
            best_u15 = (max_ht, max_ft, t, h, wr)

if best_u15:
    print(f"Melhor Filtro U15: Soma_Media_HT <= {best_u15[0]:.1f} | Soma_Media_FT <= {best_u15[1]:.1f}")
    print(f"Volume: {best_u15[2]} apostas | WR: {best_u15[4]*100:.2f}% | Odd Justa: {100/(best_u15[4]*100):.2f}")


# 3. UNDER 2.5 HT (Optimize for WR & Volume > 5000)
print("\n=== ESTUDO PROFUNDO: UNDER 2.5 HT ===")
best_wr_25 = 0
best_u25 = None

for max_ht in np.arange(1.1, 2.0, 0.1):
    for max_ft in np.arange(2.5, 3.5, 0.2):
        mask = (df['Soma_Media_HT'] <= max_ht) & (df['Soma_Media_FT'] <= max_ft)
        t = mask.sum()
        if t < 5000: continue
        
        h = df[mask]['U25'].sum()
        wr = h / t
        
        if wr > best_wr_25:
            best_wr_25 = wr
            best_u25 = (max_ht, max_ft, t, h, wr)

if best_u25:
    print(f"Melhor Filtro U25: Soma_Media_HT <= {best_u25[0]:.1f} | Soma_Media_FT <= {best_u25[1]:.1f}")
    print(f"Volume: {best_u25[2]} apostas | WR: {best_u25[4]*100:.2f}% | Odd Justa: {100/(best_u25[4]*100):.2f}")

