import pandas as pd
df = pd.read_csv('/Users/macgeint/Downloads/datafootball-base-2026-09-16 A.csv', low_memory=False, on_bad_lines='skip')
print(df['Total Gols'].value_counts())
print(df['Gols Casa'].value_counts())
print(df['Gols Fora'].value_counts())
