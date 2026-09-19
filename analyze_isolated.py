import pandas as pd
import numpy as np
from scipy.stats import poisson

def test_single_score(df, name, condition, lay_odd_col, is_red_col):
    filtered = df[condition].copy()
    if len(filtered) == 0:
        return {"Market": name, "Games": 0, "StrikeRate": 0, "ROI": 0, "Profit": 0, "AvgODD": 0}
    
    profit = np.where(filtered[is_red_col], -(filtered[lay_odd_col] - 1), 1 * (1 - 0.065))
    total_profit = profit.sum()
    roi = (total_profit / len(filtered)) * 100
    strike_rate = (~filtered[is_red_col]).mean() * 100
    
    return {
        "Market": name,
        "Games": len(filtered),
        "StrikeRate": strike_rate,
        "ROI": roi,
        "Profit": total_profit,
        "AvgODD": filtered[lay_odd_col].mean(),
        "MaxODD": filtered[lay_odd_col].max()
    }

df = pd.read_pickle('data_cache.pkl')
df['odd_h'] = df['Odd 1'].fillna(df['home_odds'])
df['odd_a'] = df['Odd 2'].fillna(df['away_odds'])

if df['Potencial BTTS'].dtype == object:
    df['Potencial BTTS'] = df['Potencial BTTS'].astype(str).str.replace('%','').astype(float) / 100.0

df = df.dropna(subset=['team_a_xg_prematch', 'team_b_xg_prematch', 'odd_h', 'odd_a'])

lambda_h = df['team_a_xg_prematch'].values
lambda_a = df['team_b_xg_prematch'].values

# Calculate probabilities per score
p_0_1 = poisson.pmf(0, lambda_h) * poisson.pmf(1, lambda_a)
p_0_2 = poisson.pmf(0, lambda_h) * poisson.pmf(2, lambda_a)
p_0_3 = poisson.pmf(0, lambda_h) * poisson.pmf(3, lambda_a)

# Protect against P=0
p_0_1 = np.clip(p_0_1, 0.0001, 1.0)
p_0_2 = np.clip(p_0_2, 0.0001, 1.0)
p_0_3 = np.clip(p_0_3, 0.0001, 1.0)

# Lay Odds (Fair Odd + 10% premium, capped at realistic max for lay markets)
df['lay_odd_0_1'] = np.clip((1.0 / p_0_1) * 1.10, 1.01, 30) # 0-1 usually 6 to 15
df['lay_odd_0_2'] = np.clip((1.0 / p_0_2) * 1.10, 1.01, 60) # 0-2 usually 15 to 40
df['lay_odd_0_3'] = np.clip((1.0 / p_0_3) * 1.10, 1.01, 150) # 0-3 usually 40 to 120

df['is_red_0_1'] = ((df['Gols Casa'] == 0) & (df['Gols Fora'] == 1))
df['is_red_0_2'] = ((df['Gols Casa'] == 0) & (df['Gols Fora'] == 2))
df['is_red_0_3'] = ((df['Gols Casa'] == 0) & (df['Gols Fora'] == 3))

# Best Filters
base_cond = (df['team_a_xg_prematch'] > 1.5) & (df['Potencial BTTS'] > 0.6) & (df['odd_h'] < 2.0)

strategies = []

# No Lay Odd limits
strategies.append(test_single_score(df, "Lay 0-1 (Sem Limite Odd)", base_cond, 'lay_odd_0_1', 'is_red_0_1'))
strategies.append(test_single_score(df, "Lay 0-2 (Sem Limite Odd)", base_cond, 'lay_odd_0_2', 'is_red_0_2'))
strategies.append(test_single_score(df, "Lay 0-3 (Sem Limite Odd)", base_cond, 'lay_odd_0_3', 'is_red_0_3'))

# With realistic Lay Odd limits for each score to mitigate variance
strategies.append(test_single_score(df, "Lay 0-1 (Odd <= 15)", base_cond & (df['lay_odd_0_1'] <= 15), 'lay_odd_0_1', 'is_red_0_1'))
strategies.append(test_single_score(df, "Lay 0-2 (Odd <= 30)", base_cond & (df['lay_odd_0_2'] <= 30), 'lay_odd_0_2', 'is_red_0_2'))
strategies.append(test_single_score(df, "Lay 0-3 (Odd <= 70)", base_cond & (df['lay_odd_0_3'] <= 70), 'lay_odd_0_3', 'is_red_0_3'))

res_df = pd.DataFrame(strategies)
print(res_df.to_string(index=False))
