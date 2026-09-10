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

# Create Odd Bands based on FULL TIME UNDER 2.5 ODDS
bins = [1.0, 1.5, 1.6, 1.7, 1.8, 2.0, 2.3, 100.0]
labels = ['1.01 - 1.50', '1.51 - 1.60', '1.61 - 1.70', '1.71 - 1.80', '1.81 - 2.00', '2.01 - 2.30', '2.31+']
df['Odd_Band'] = pd.cut(df['odds_ft_under25'], bins=bins, labels=labels, right=True)

print("=== UNDER 1.5 HT (Separado pela Odd do Under 2.5 FT) ===")
print("Regras: Soma_Media_HT <= 1.4 AND Efic_xG (Ambos) <= 1.0\n")
mask_u15 = (df['Soma_Media_HT'] <= 1.4) & (df['Efic_xG_Casa'] <= 1.0) & (df['Efic_xG_Visitante'] <= 1.0) & (df['Efic_xG_Casa'] > 0) & (df['Efic_xG_Visitante'] > 0)
df_u15 = df[mask_u15].copy()

for band in labels:
    sub = df_u15[df_u15['Odd_Band'] == band]
    t = len(sub)
    if t == 0: continue
    h = sub['U15'].sum()
    wr = h / t
    odd_justa = 100/(wr*100) if wr > 0 else 0
    print(f"Odd FT {band}: Apostas: {t} | Acertos: {h} | Win Rate: {wr*100:.2f}% | Odd Justa de Equilíbrio: {odd_justa:.2f}")

print("\n=== UNDER 2.5 HT (Separado pela Odd do Under 2.5 FT) ===")
print("Regras: Soma_Media_HT <= 1.8 AND Efic_xG (Ambos) <= 1.0\n")
mask_u25 = (df['Soma_Media_HT'] <= 1.8) & (df['Efic_xG_Casa'] <= 1.0) & (df['Efic_xG_Visitante'] <= 1.0) & (df['Efic_xG_Casa'] > 0) & (df['Efic_xG_Visitante'] > 0)
df_u25 = df[mask_u25].copy()

for band in labels:
    sub = df_u25[df_u25['Odd_Band'] == band]
    t = len(sub)
    if t == 0: continue
    h = sub['U25'].sum()
    wr = h / t
    odd_justa = 100/(wr*100) if wr > 0 else 0
    print(f"Odd FT {band}: Apostas: {t} | Acertos: {h} | Win Rate: {wr*100:.2f}% | Odd Justa de Equilíbrio: {odd_justa:.2f}")

