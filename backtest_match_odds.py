from database.db import engine
import pandas as pd
import numpy as np

print("Connecting to DB and fetching data...")
# Read all completed matches
query = 'SELECT "Odd 1", "Odd 2", "odds_1st_half_result_1", "odds_1st_half_result_2", "Gols Casa", "Gols Fora", "Gols HT Casa", "Gols HT Fora" FROM datafootball_historical WHERE "Status" = \'complete\''
df = pd.read_sql(query, engine)
print(f"Total rows fetched: {len(df)}")

# Convert to numeric
for col in ['Odd 1', 'Odd 2', 'odds_1st_half_result_1', 'odds_1st_half_result_2', 'Gols Casa', 'Gols Fora', 'Gols HT Casa', 'Gols HT Fora']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Filter valid odds and goals
df = df.dropna(subset=['Odd 1', 'Odd 2', 'Gols Casa', 'Gols Fora'])
print(f"Total rows after dropping na: {len(df)}")

df['Fav_Odd_FT'] = df[['Odd 1', 'Odd 2']].min(axis=1)
df['Zeb_Odd_FT'] = df[['Odd 1', 'Odd 2']].max(axis=1)

def get_ft_result(row):
    if row['Gols Casa'] > row['Gols Fora']: return '1'
    elif row['Gols Casa'] < row['Gols Fora']: return '2'
    return 'X'
df['Result_FT'] = df.apply(get_ft_result, axis=1)

def get_ht_result(row):
    if pd.isna(row['Gols HT Casa']) or pd.isna(row['Gols HT Fora']): return 'Unknown'
    if row['Gols HT Casa'] > row['Gols HT Fora']: return '1'
    elif row['Gols HT Casa'] < row['Gols HT Fora']: return '2'
    return 'X'
df['Result_HT'] = df.apply(get_ht_result, axis=1)

df['Fav_Team'] = df.apply(lambda r: '1' if r['Odd 1'] < r['Odd 2'] else ('2' if r['Odd 2'] < r['Odd 1'] else 'None'), axis=1)
df = df[df['Fav_Team'] != 'None']

def calc_roi(df_filtered, bet_on, is_lay=False, odd_col=None):
    if len(df_filtered) == 0: return 0, 0, 0
    wins = 0
    profit = 0.0
    for idx, row in df_filtered.iterrows():
        if bet_on['target'] == 'Fav':
            won = (row[bet_on['result_col']] == row['Fav_Team'])
        else: # Zebra
            # Zebra wins if result is NOT the Fav_Team and NOT a draw
            won = (row[bet_on['result_col']] != row['Fav_Team'] and row[bet_on['result_col']] != 'X')
            
        odd = row[odd_col]
        if pd.isna(odd) or odd <= 1.0:
            continue
            
        if not is_lay:
            if won:
                profit += (odd - 1)
                wins += 1
            else:
                profit -= 1
        else:
            if not won:
                profit += 1
                wins += 1
            else:
                profit -= (odd - 1)
                
    strike_rate = (wins / len(df_filtered)) * 100
    return len(df_filtered), strike_rate, profit

print("--- BACKTEST RESULTS ---")
df_valid_ft = df[df['Fav_Odd_FT'] > 1.0]

c, sr, p = calc_roi(df_valid_ft, {'result_col': 'Result_FT', 'target': 'Fav'}, False, 'Fav_Odd_FT')
print(f"Back FT Favorito: Jogos={c}, SR={sr:.2f}%, Profit={p:.2f} un")

c, sr, p = calc_roi(df_valid_ft, {'result_col': 'Result_FT', 'target': 'Zeb'}, False, 'Zeb_Odd_FT')
print(f"Back FT Zebra: Jogos={c}, SR={sr:.2f}%, Profit={p:.2f} un")

c, sr, p = calc_roi(df_valid_ft, {'result_col': 'Result_FT', 'target': 'Fav'}, True, 'Fav_Odd_FT')
print(f"Lay FT Favorito: Jogos={c}, SR={sr:.2f}%, Profit={p:.2f} un")

# HT calculations
df['Fav_Odd_HT'] = df.apply(lambda r: r['odds_1st_half_result_1'] if r['Fav_Team']=='1' else r['odds_1st_half_result_2'], axis=1)
df['Zeb_Odd_HT'] = df.apply(lambda r: r['odds_1st_half_result_2'] if r['Fav_Team']=='1' else r['odds_1st_half_result_1'], axis=1)

df_valid_ht = df[(df['Result_HT'] != 'Unknown') & (df['Fav_Odd_HT'] > 1.0)]
c, sr, p = calc_roi(df_valid_ht, {'result_col': 'Result_HT', 'target': 'Fav'}, False, 'Fav_Odd_HT')
print(f"Back HT Favorito: Jogos={c}, SR={sr:.2f}%, Profit={p:.2f} un")

c, sr, p = calc_roi(df_valid_ht, {'result_col': 'Result_HT', 'target': 'Fav'}, True, 'Fav_Odd_HT')
print(f"Lay HT Favorito: Jogos={c}, SR={sr:.2f}%, Profit={p:.2f} un")

df_valid_ht_z = df[(df['Result_HT'] != 'Unknown') & (df['Zeb_Odd_HT'] > 1.0)]
c, sr, p = calc_roi(df_valid_ht_z, {'result_col': 'Result_HT', 'target': 'Zeb'}, False, 'Zeb_Odd_HT')
print(f"Back HT Zebra: Jogos={c}, SR={sr:.2f}%, Profit={p:.2f} un")

