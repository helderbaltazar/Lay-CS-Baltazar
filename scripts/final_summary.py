import sqlite3
import pandas as pd
import numpy as np

conn = sqlite3.connect('data_store/database.sqlite3')
query = """
    SELECT 
        HTGoalCount, odds_ft_under25,
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
df['U15'] = (df['HTGoalCount'] < 1.5).astype(int)
df['U25'] = (df['HTGoalCount'] < 2.5).astype(int)

# U15 Flat
mask_u15 = (df['odds_ft_under25'] <= 1.60) & (df['Soma_Media_HT'] <= 1.4)
t15 = mask_u15.sum()
h15 = df[mask_u15]['U15'].sum()

print(f"U15: Vol: {t15} | WR: {h15/t15*100:.2f}% | OddJusta: {100/(h15/t15*100):.2f}")

# U25 Flat
mask_u25 = (df['odds_ft_under25'] <= 1.60) & (df['Soma_Media_HT'] <= 1.8) & (df['Efic_xG_Casa'] <= 1.0) & (df['Efic_xG_Visitante'] <= 1.0) & (df['Efic_xG_Casa'] > 0) & (df['Efic_xG_Visitante'] > 0)
t25 = mask_u25.sum()
h25 = df[mask_u25]['U25'].sum()

print(f"U25: Vol: {t25} | WR: {h25/t25*100:.2f}% | OddJusta: {100/(h25/t25*100):.2f}")
