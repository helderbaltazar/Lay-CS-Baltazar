import pandas as pd
df = pd.read_csv('/Users/macgeint/Downloads/datafootball-base-2026-09-16 A.csv', low_memory=False, on_bad_lines='skip')
df = df[df['Status'].str.lower() == 'complete']
cols = ['Casa', 'Fora', 'Gols HT Casa', 'Gols HT Fora', 'goals_2hg_team_a', 'goals_2hg_team_b', 'Gols Totais']
print(df[cols].head(10).to_string())
