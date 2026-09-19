import pandas as pd
import numpy as np
from scipy.stats import poisson

def test_strategy(df, name, condition):
    filtered = df[condition].copy()
    if len(filtered) == 0:
        return {"Name": name, "Games": 0, "StrikeRate": 0, "ROI": 0, "Profit": 0, "MaxODD": 0, "AvgODD": 0}
    
    profit = filtered['pnl'].sum()
    roi = (profit / len(filtered)) * 100
    strike_rate = (~filtered['is_red']).mean() * 100
    
    return {
        "Name": name,
        "Games": len(filtered),
        "StrikeRate": strike_rate,
        "ROI": roi,
        "Profit": profit,
        "MaxODD": filtered['lay_odd'].max(),
        "AvgODD": filtered['lay_odd'].mean()
    }

df = pd.read_pickle('data_cache.pkl')
df['odd_h'] = df['Odd 1'].fillna(df['home_odds'])
df['odd_a'] = df['Odd 2'].fillna(df['away_odds'])

df['PPG Casa Pré-Jogo'] = pd.to_numeric(df['PPG Casa Pré-Jogo'], errors='coerce')
df['PPG Fora Pré-Jogo'] = pd.to_numeric(df['PPG Fora Pré-Jogo'], errors='coerce')
if df['Potencial BTTS'].dtype == object:
    df['Potencial BTTS'] = df['Potencial BTTS'].astype(str).str.replace('%','').astype(float) / 100.0

df = df.dropna(subset=['team_a_xg_prematch', 'team_b_xg_prematch', 'odd_h', 'odd_a'])

lambda_h = df['team_a_xg_prematch'].values
lambda_a = df['team_b_xg_prematch'].values

p_0_1 = poisson.pmf(0, lambda_h) * poisson.pmf(1, lambda_a)
p_0_2 = poisson.pmf(0, lambda_h) * poisson.pmf(2, lambda_a)
p_0_3 = poisson.pmf(0, lambda_h) * poisson.pmf(3, lambda_a)

p_target = p_0_1 + p_0_2 + p_0_3
p_target = np.clip(p_target, 0.001, 1.0)

fair_odd = 1.0 / p_target
df['lay_odd'] = np.clip(fair_odd * 1.10, 1.01, 100) # cap at 100

df['is_red'] = ((df['Gols Casa'] == 0) & (df['Gols Fora'].isin([1, 2, 3])))
df['pnl'] = np.where(df['is_red'], -(df['lay_odd'] - 1), 1 * (1 - 0.065))

strategies = []
strategies.append(test_strategy(df, "1. Combo Base", 
                                (df['team_a_xg_prematch'] > 1.5) & (df['Potencial BTTS'] > 0.6) & (df['odd_h'] < 2.2)))

strategies.append(test_strategy(df, "2. Combo Base + Odd Home < 2.0", 
                                (df['team_a_xg_prematch'] > 1.5) & (df['Potencial BTTS'] > 0.6) & (df['odd_h'] < 2.0)))

strategies.append(test_strategy(df, "3. Combo Base + Lay Odd < 15", 
                                (df['team_a_xg_prematch'] > 1.5) & (df['Potencial BTTS'] > 0.6) & (df['odd_h'] < 2.2) & (df['lay_odd'] < 15)))

strategies.append(test_strategy(df, "4. Combo Base + Lay Odd < 20", 
                                (df['team_a_xg_prematch'] > 1.5) & (df['Potencial BTTS'] > 0.6) & (df['odd_h'] < 2.2) & (df['lay_odd'] < 20)))

strategies.append(test_strategy(df, "5. BTTS > 65% + Home xG > 1.6 + Odd Home < 2.2", 
                                (df['team_a_xg_prematch'] > 1.6) & (df['Potencial BTTS'] > 0.65) & (df['odd_h'] < 2.2)))

strategies.append(test_strategy(df, "6. Home PPG > 1.5 + Combo Base", 
                                (df['team_a_xg_prematch'] > 1.5) & (df['Potencial BTTS'] > 0.6) & (df['odd_h'] < 2.2) & (df['PPG Casa Pré-Jogo'] > 1.5)))

res_df = pd.DataFrame(strategies)
print(res_df.to_string(index=False))
