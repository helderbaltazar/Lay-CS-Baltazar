import pandas as pd
df = pd.read_csv('/Users/macgeint/Downloads/datafootball-base-2026-09-16 A.csv', low_memory=False, on_bad_lines='skip')
df = df[df['Status'].str.lower() == 'complete']
cols = ['Casa', 'Fora', 'Gols Casa', 'Gols Fora', 'Total Gols', 'Vencedor']
print(df[cols].head(15))
