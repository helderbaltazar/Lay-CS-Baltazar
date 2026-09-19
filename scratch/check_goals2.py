import pandas as pd
import glob
df = pd.read_csv('/Users/macgeint/Downloads/datafootball-base-2026-09-16 A.csv', low_memory=False, on_bad_lines='skip')
cols = [c for c in df.columns if 'Gol' in c or 'Gols' in c or 'goals' in c or 'Vencedor' in c]
print(df[cols].head(5))
