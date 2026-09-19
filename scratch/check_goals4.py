import pandas as pd
df = pd.read_csv('/Users/macgeint/Downloads/datafootball-base-2026-09-16 A.csv', low_memory=False, on_bad_lines='skip')
df = df[(df['Status'].str.lower() == 'complete') & (df['Total Gols'] > 2)]
cols = ['Casa', 'Fora', 'Total Gols', 'Gols Casa', 'Gols Fora', 'homeGoals_timings', 'awayGoals_timings', 'Vencedor']
print(df[cols].head(5))
