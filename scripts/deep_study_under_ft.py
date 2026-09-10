import sqlite3
import pandas as pd
from models.poisson import PoissonDixonColes

# Load full DB
conn = sqlite3.connect("data_store/database.sqlite3")
df = pd.read_sql_query("""
    SELECT 
        homeGoalCount, awayGoalCount, totalGoalCount,
        Media_Gols_Total_Casa, Media_Gols_Total_Visitante,
        Media_Gols_no_1T_Casa, Media_Gols_no_1T_Visitante,
        Efic_xG_Casa, Efic_xG_Visitante,
        odds_ft_under25
    FROM telegram_dataset
    WHERE Media_Gols_Total_Casa IS NOT NULL 
      AND Media_Gols_Total_Visitante IS NOT NULL
      AND totalGoalCount IS NOT NULL
""", conn)
conn.close()

print(f"Total Matches: {len(df)}")

df['Soma_Media_Gols_FT'] = df['Media_Gols_Total_Casa'] + df['Media_Gols_Total_Visitante']
df['Soma_Efic_xG'] = df['Efic_xG_Casa'] + df['Efic_xG_Visitante']

# Target conditions
df['Under25_Hit'] = df['totalGoalCount'] <= 2
df['Under35_Hit'] = df['totalGoalCount'] <= 3
df['Under45_Hit'] = df['totalGoalCount'] <= 4

print(f"Base Win Rate Under 2.5: {df['Under25_Hit'].mean()*100:.2f}%")
print(f"Base Win Rate Under 3.5: {df['Under35_Hit'].mean()*100:.2f}%")
print(f"Base Win Rate Under 4.5: {df['Under45_Hit'].mean()*100:.2f}%")

print("\n--- UNDER 2.5 FT STUDY ---")
best_profit = -99999
best_params = {}
for soma_max in [1.5, 1.8, 2.0, 2.2, 2.5]:
    for efic_max in [0.8, 1.0, 1.2, 1.5]:
        mask = (df['Soma_Media_Gols_FT'] <= soma_max) & (df['Efic_xG_Casa'] <= efic_max) & (df['Efic_xG_Visitante'] <= efic_max)
        sub = df[mask].copy()
        vol = len(sub)
        if vol < 300: continue
        
        wr = sub['Under25_Hit'].mean()
        
        # Calculate profit using odds_ft_under25 (ignoring missing odds or filling with 1.60 average)
        sub_odds = sub[sub['odds_ft_under25'] > 1.0].copy()
        if len(sub_odds) < vol * 0.5:
            # Not enough odds, estimate with avg 1.60
            profit = (sub['Under25_Hit'].sum() * 100 * 0.60) - ((vol - sub['Under25_Hit'].sum()) * 100)
        else:
            wins = sub_odds[sub_odds['Under25_Hit']]
            losses = sub_odds[~sub_odds['Under25_Hit']]
            profit = (wins['odds_ft_under25'] - 1).sum() * 100 - (len(losses) * 100)
            
        roi = profit / (vol * 100)
        if roi > best_profit:
            best_profit = roi
            best_params = {'soma': soma_max, 'efic': efic_max, 'vol': vol, 'wr': wr, 'roi': roi, 'profit': profit}

print(f"Best U2.5: Soma_FT<={best_params['soma']}, Efic_xG<={best_params['efic']} -> WR: {best_params['wr']*100:.2f}% | Vol: {best_params['vol']} | ROI: {best_params['roi']*100:.2f}% | Profit: R$ {best_params['profit']:.2f}")


print("\n--- UNDER 3.5 FT STUDY ---")
best_profit = -99999
best_params = {}
for soma_max in [2.0, 2.5, 2.8, 3.0]:
    for efic_max in [1.0, 1.2, 1.5, 1.8]:
        mask = (df['Soma_Media_Gols_FT'] <= soma_max) & (df['Efic_xG_Casa'] <= efic_max) & (df['Efic_xG_Visitante'] <= efic_max)
        sub = df[mask]
        vol = len(sub)
        if vol < 300: continue
        wr = sub['Under35_Hit'].mean()
        
        # Estimating average odd for U3.5 around 1.30
        profit = (sub['Under35_Hit'].sum() * 100 * 0.30) - ((vol - sub['Under35_Hit'].sum()) * 100)
        roi = profit / (vol * 100)
        
        if roi > best_profit:
            best_profit = roi
            best_params = {'soma': soma_max, 'efic': efic_max, 'vol': vol, 'wr': wr, 'roi': roi, 'profit': profit}

print(f"Best U3.5: Soma_FT<={best_params['soma']}, Efic_xG<={best_params['efic']} -> WR: {best_params['wr']*100:.2f}% | Vol: {best_params['vol']} | ROI: {best_params['roi']*100:.2f}% | Profit: R$ {best_params['profit']:.2f} (Est Odd 1.30)")


print("\n--- UNDER 4.5 FT STUDY ---")
best_profit = -99999
best_params = {}
for soma_max in [2.5, 3.0, 3.5, 4.0]:
    for efic_max in [1.2, 1.5, 2.0, 2.5]:
        mask = (df['Soma_Media_Gols_FT'] <= soma_max) & (df['Efic_xG_Casa'] <= efic_max) & (df['Efic_xG_Visitante'] <= efic_max)
        sub = df[mask]
        vol = len(sub)
        if vol < 300: continue
        wr = sub['Under45_Hit'].mean()
        
        # Estimating average odd for U4.5 around 1.15
        profit = (sub['Under45_Hit'].sum() * 100 * 0.15) - ((vol - sub['Under45_Hit'].sum()) * 100)
        roi = profit / (vol * 100)
        
        if roi > best_profit:
            best_profit = roi
            best_params = {'soma': soma_max, 'efic': efic_max, 'vol': vol, 'wr': wr, 'roi': roi, 'profit': profit}

print(f"Best U4.5: Soma_FT<={best_params['soma']}, Efic_xG<={best_params['efic']} -> WR: {best_params['wr']*100:.2f}% | Vol: {best_params['vol']} | ROI: {best_params['roi']*100:.2f}% | Profit: R$ {best_params['profit']:.2f} (Est Odd 1.15)")

