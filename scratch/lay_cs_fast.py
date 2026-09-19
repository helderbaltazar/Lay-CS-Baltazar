import pandas as pd
import numpy as np
import glob

def load_data():
    files = glob.glob('/Users/macgeint/Downloads/datafootball-base-2026-09-16 *.csv')
    df_list = []
    for f in files:
        df = pd.read_csv(f, low_memory=False, on_bad_lines='skip')
        df_list.append(df)
    return pd.concat(df_list, ignore_index=True)

df = load_data()
df = df[df['Status'].str.lower() == 'complete']

for col in ['Odd 1', 'Odd X', 'Odd 2', 'Under 2.5', 'Gols HT Casa', 'Gols HT Fora', 'goals_2hg_team_a', 'goals_2hg_team_b']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

df = df.dropna(subset=['Odd 1', 'Odd 2', 'Gols HT Casa', 'Gols HT Fora', 'goals_2hg_team_a', 'goals_2hg_team_b'])

df['FT_Home'] = df['Gols HT Casa'] + df['goals_2hg_team_a']
df['FT_Away'] = df['Gols HT Fora'] + df['goals_2hg_team_b']

# Implied probabilities
df['p_h'] = 1 / df['Odd 1']
df['p_d'] = 1 / df['Odd X']
df['p_a'] = 1 / df['Odd 2']
# Normalize
sum_p = df['p_h'] + df['p_d'] + df['p_a']
df['p_h'] /= sum_p
df['p_d'] /= sum_p
df['p_a'] /= sum_p

df['p_u25'] = np.where(df['Under 2.5'] > 1.0, 1 / df['Under 2.5'], 0.5)
df['total_xg'] = 2.6 + (0.5 - df['p_u25']) * 4.0
df['total_xg'] = np.clip(df['total_xg'], 1.5, 4.5)

df['lam_h'] = df['total_xg'] * (df['p_h'] / (df['p_h'] + df['p_a']))
df['lam_a'] = df['total_xg'] * (df['p_a'] / (df['p_h'] + df['p_a']))

rho = -0.10
zip_prob = 0.05
df['tau_0_1'] = 1 + df['lam_h'] * rho
df['tau_0_2'] = 1.0
df['tau_0_3'] = 1.0

df['prob_0_1_raw'] = np.exp(-df['lam_h']) * (df['lam_a'] * np.exp(-df['lam_a'])) * df['tau_0_1']
df['prob_0_2_raw'] = np.exp(-df['lam_h']) * (df['lam_a']**2 * np.exp(-df['lam_a']) / 2) * df['tau_0_2']
df['prob_0_3_raw'] = np.exp(-df['lam_h']) * (df['lam_a']**3 * np.exp(-df['lam_a']) / 6) * df['tau_0_3']

df['prob_0_1'] = (1 - zip_prob) * df['prob_0_1_raw'] + zip_prob * 0.2 * df['prob_0_1_raw']
df['prob_0_2'] = (1 - zip_prob) * df['prob_0_2_raw']
df['prob_0_3'] = (1 - zip_prob) * df['prob_0_3_raw']

df['lay_odd_0_1'] = (1 / df['prob_0_1']) * 1.05
df['lay_odd_0_2'] = (1 / df['prob_0_2']) * 1.05
df['lay_odd_0_3'] = (1 / df['prob_0_3']) * 1.05

df['lay_odd_0_1'] = np.clip(df['lay_odd_0_1'], 2.0, 50.0)
df['lay_odd_0_2'] = np.clip(df['lay_odd_0_2'], 2.0, 50.0)
df['lay_odd_0_3'] = np.clip(df['lay_odd_0_3'], 2.0, 50.0)

df['is_0_1'] = (df['FT_Home'] == 0) & (df['FT_Away'] == 1)
df['is_0_2'] = (df['FT_Home'] == 0) & (df['FT_Away'] == 2)
df['is_0_3'] = (df['FT_Home'] == 0) & (df['FT_Away'] == 3)

COMMISSION = 0.065
def calc_profit(df_sub, target='0_1'):
    odd_col = f'lay_odd_{target}'
    is_col = f'is_{target}'
    profit = np.where(~df_sub[is_col], 1.0 * (1 - COMMISSION), -(df_sub[odd_col] - 1.0))
    return profit.sum(), len(df_sub), df_sub[is_col].sum(), profit

print(f"Total Matches Valid: {len(df)}")
for target in ['0_1', '0_2', '0_3']:
    p, n, hits, _ = calc_profit(df, target)
    print(f"Base Lay {target.replace('_', 'x')} - N: {n}, Hits: {hits}, SR: {(n-hits)/n*100:.2f}%, Profit: {p:.2f} un")

# Agora vamos procurar EV+ em blocos específicos
# Filtro 1: Casa Super Favorito (Odd < 1.5) mas visitante ganha?
# Actually we want Lay Away (Away wins 0-1, 0-2). If Home is Super Favorite, Away winning exactly 0-1 is very rare, so Lay 0x1 might be EV+.
f1 = df[df['Odd 1'] <= 1.5]
for target in ['0_1', '0_2', '0_3']:
    p, n, hits, _ = calc_profit(f1, target)
    if n > 0: print(f"Filtro [Home Fav < 1.5] Lay {target.replace('_', 'x')} - N: {n}, Profit: {p:.2f} un")

# Filtro 2: Casa Zebra (Odd > 3.0), ou seja, Fora é Favorito
f2 = df[df['Odd 1'] > 3.0]
for target in ['0_1', '0_2', '0_3']:
    p, n, hits, _ = calc_profit(f2, target)
    if n > 0: print(f"Filtro [Home Zebra > 3.0] Lay {target.replace('_', 'x')} - N: {n}, Profit: {p:.2f} un")

# Filtro 3: BTTS Sim Alto (Potencial > 60%) => Times que marcam e sofrem
df['Potencial BTTS'] = pd.to_numeric(df['Potencial BTTS'].astype(str).str.replace('%',''), errors='coerce')
f3 = df[df['Potencial BTTS'] >= 60]
for target in ['0_1', '0_2', '0_3']:
    p, n, hits, _ = calc_profit(f3, target)
    if n > 0: print(f"Filtro [BTTS >= 60%] Lay {target.replace('_', 'x')} - N: {n}, Profit: {p:.2f} un")

