import sqlite3
import pandas as pd

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
      AND odds_ft_under25 IS NOT NULL
      AND Efic_xG_Casa IS NOT NULL
      AND Efic_xG_Visitante IS NOT NULL
"""
df = pd.read_sql_query(query, conn)
conn.close()

df['Soma_Media_HT'] = df['Media_Gols_no_1T_Casa'] + df['Media_Gols_no_1T_Visitante']
df['U05'] = (df['HTGoalCount'] < 0.5).astype(int)

df_u05 = df[df['odds_1st_half_under05'] >= 2.7].copy()

t = len(df_u05)
print(f"Total jogos com odd >= 2.7: {t}")

for max_efic in [0.8, 0.9, 1.0, 1.1]:
    mask = (df_u05['Efic_xG_Casa'] <= max_efic) & \
           (df_u05['Efic_xG_Visitante'] <= max_efic) & \
           (df_u05['Efic_xG_Casa'] > 0) & \
           (df_u05['Efic_xG_Visitante'] > 0) & \
           (df_u05['Soma_Media_HT'] <= 1.2)
    
    t = mask.sum()
    if t < 50: continue
    
    sub = df_u05[mask]
    h = sub['U05'].sum()
    inv = t * 100
    ret = (sub[sub['U05'] == 1]['odds_1st_half_under05'] * 100).sum()
    roi = ((ret - inv) / inv) * 100
    
    print(f"SomaHT<=1.2 Efic_xG<={max_efic} Odd>=2.70 | Apostas: {t} | WR: {h/t*100:.2f}% | ROI: {roi:.2f}%")
