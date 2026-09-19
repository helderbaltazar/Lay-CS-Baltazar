import pandas as pd
import glob
files = glob.glob('/Users/macgeint/Downloads/datafootball-base-2026-09-16 *.csv')
sim_count = 0
for f in files:
    df = pd.read_csv(f, low_memory=False, on_bad_lines='skip')
    if '+2.5 Gols' in df.columns:
        sim_count += (df['+2.5 Gols'] == 'Sim').sum()
print("Total Sim for +2.5 Gols:", sim_count)
