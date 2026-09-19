import pandas as pd
df = pd.read_csv('/Users/macgeint/Downloads/datafootball-base-2026-09-16 A.csv', low_memory=False, on_bad_lines='skip')
cols = ['+0.5 Gols', '+1.5 Gols', '+2.5 Gols', '+3.5 Gols', '+4.5 Gols', '+5.5 Gols', 'Gols Totais']
print(df[cols].head(15))
print("Counts for +2.5 Gols:")
print(df['+2.5 Gols'].value_counts())
