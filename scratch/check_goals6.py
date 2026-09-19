import pandas as pd
df = pd.read_csv('/Users/macgeint/Downloads/datafootball-base-2026-09-16 A.csv', low_memory=False, on_bad_lines='skip')
cols = [c for c in df.columns if 'gol' in c.lower() or 'goal' in c.lower()]
print(cols)
