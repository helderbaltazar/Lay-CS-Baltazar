from database.db import engine
import pandas as pd
import numpy as np

print("Connecting to DB and fetching data...")
query = '''
SELECT "Odd 1", "Odd 2", "odds_1st_half_result_1", "odds_1st_half_result_2", 
       "Gols Casa", "Gols Fora", "Gols HT Casa", "Gols HT Fora",
       "team_a_xg_prematch", "team_b_xg_prematch"
FROM datafootball_historical 
WHERE "Status" = 'complete'
'''
df = pd.read_sql(query, engine)
print(f"Total rows fetched: {len(df)}")

cols_to_numeric = ['Odd 1', 'Odd 2', 'odds_1st_half_result_1', 'odds_1st_half_result_2', 
                   'Gols Casa', 'Gols Fora', 'Gols HT Casa', 'Gols HT Fora',
                   'team_a_xg_prematch', 'team_b_xg_prematch']

for col in cols_to_numeric:
    df[col] = pd.to_numeric(df[col], errors='coerce')

df = df.dropna(subset=['Odd 1', 'Odd 2', 'Gols Casa', 'Gols Fora', 'team_a_xg_prematch', 'team_b_xg_prematch'])
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

df['Fav_xG_pre'] = df.apply(lambda r: r['team_a_xg_prematch'] if r['Fav_Team']=='1' else r['team_b_xg_prematch'], axis=1)
df['Zeb_xG_pre'] = df.apply(lambda r: r['team_b_xg_prematch'] if r['Fav_Team']=='1' else r['team_a_xg_prematch'], axis=1)
df['Fav_Odd_HT'] = df.apply(lambda r: r['odds_1st_half_result_1'] if r['Fav_Team']=='1' else r['odds_1st_half_result_2'], axis=1)
df['Zeb_Odd_HT'] = df.apply(lambda r: r['odds_1st_half_result_2'] if r['Fav_Team']=='1' else r['odds_1st_half_result_1'], axis=1)

def eval_pattern(df_subset, bet_on, is_lay=False, odd_col=''):
    if len(df_subset) == 0:
        return 0, 0, 0, 0
    wins = 0
    profit = 0.0
    for idx, row in df_subset.iterrows():
        odd = row[odd_col]
        if pd.isna(odd) or odd <= 1.0:
            continue
            
        if bet_on['target'] == 'Fav':
            won = (row[bet_on['result_col']] == row['Fav_Team'])
        else:
            won = (row[bet_on['result_col']] != row['Fav_Team'] and row[bet_on['result_col']] != 'X')
            
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
                
    vol = len(df_subset)
    sr = (wins / vol) * 100
    roi = (profit / vol) * 100
    return vol, sr, profit, roi

print("--- BACKTEST PATTERNS ---")

# 1. Back Favorito
f1 = df[(df['Fav_Odd_FT'] < 1.60) & (df['Fav_xG_pre'] > (df['Zeb_xG_pre'] * 2))]
v, sr, p, roi = eval_pattern(f1, {'result_col': 'Result_FT', 'target': 'Fav'}, False, 'Fav_Odd_FT')
print(f"Back Fav FT | Volume: {v} | SR: {sr:.2f}% | Profit: {p:.2f} un | ROI: {roi:.2f}%")

f1_ht = f1[(f1['Result_HT'] != 'Unknown')]
v, sr, p, roi = eval_pattern(f1_ht, {'result_col': 'Result_HT', 'target': 'Fav'}, False, 'Fav_Odd_HT')
print(f"Back Fav HT | Volume: {v} | SR: {sr:.2f}% | Profit: {p:.2f} un | ROI: {roi:.2f}%")

# 2. Lay Favorito
f2 = df[(df['Fav_Odd_FT'] >= 1.50) & (df['Fav_Odd_FT'] <= 2.20) & (df['Fav_xG_pre'] <= df['Zeb_xG_pre'])]
v, sr, p, roi = eval_pattern(f2, {'result_col': 'Result_FT', 'target': 'Fav'}, True, 'Fav_Odd_FT')
print(f"Lay Fav FT | Volume: {v} | SR: {sr:.2f}% | Profit: {p:.2f} un | ROI: {roi:.2f}%")

f2_ht = f2[(f2['Result_HT'] != 'Unknown')]
v, sr, p, roi = eval_pattern(f2_ht, {'result_col': 'Result_HT', 'target': 'Fav'}, True, 'Fav_Odd_HT')
print(f"Lay Fav HT | Volume: {v} | SR: {sr:.2f}% | Profit: {p:.2f} un | ROI: {roi:.2f}%")

# 3. Back Zebra
f3 = df[(df['Zeb_Odd_FT'] > 3.0) & (df['Zeb_xG_pre'] >= df['Fav_xG_pre'])]
v, sr, p, roi = eval_pattern(f3, {'result_col': 'Result_FT', 'target': 'Zeb'}, False, 'Zeb_Odd_FT')
print(f"Back Zeb FT | Volume: {v} | SR: {sr:.2f}% | Profit: {p:.2f} un | ROI: {roi:.2f}%")

f3_ht = f3[(f3['Result_HT'] != 'Unknown')]
v, sr, p, roi = eval_pattern(f3_ht, {'result_col': 'Result_HT', 'target': 'Zeb'}, False, 'Zeb_Odd_HT')
print(f"Back Zeb HT | Volume: {v} | SR: {sr:.2f}% | Profit: {p:.2f} un | ROI: {roi:.2f}%")
