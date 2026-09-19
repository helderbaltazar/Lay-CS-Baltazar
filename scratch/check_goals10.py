import pandas as pd
df = pd.read_csv('/Users/macgeint/Downloads/datafootball-base-2026-09-16 A.csv', low_memory=False, on_bad_lines='skip')
print(df['Gols HT Casa'].value_counts())
print(df['goals_2hg_team_a'].value_counts())
print(df['Gols Totais'].value_counts())
