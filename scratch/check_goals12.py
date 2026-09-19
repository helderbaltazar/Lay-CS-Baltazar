import pandas as pd
import glob
files = glob.glob('/Users/macgeint/Downloads/datafootball-base-2026-09-16 *.csv')
max_goals = 0
for f in files:
    df = pd.read_csv(f, low_memory=False, on_bad_lines='skip')
    df['Gols Totais'] = pd.to_numeric(df['Gols Totais'], errors='coerce')
    m = df['Gols Totais'].max()
    if m > max_goals:
        max_goals = m
print("Abs max goals:", max_goals)
