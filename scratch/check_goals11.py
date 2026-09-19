import pandas as pd
import glob
files = glob.glob('/Users/macgeint/Downloads/datafootball-base-2026-09-16 *.csv')
df = pd.read_csv(files[0], low_memory=False, on_bad_lines='skip')
print(df['Gols Totais'].value_counts())
