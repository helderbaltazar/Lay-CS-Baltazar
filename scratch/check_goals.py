import pandas as pd
import glob
def load_data():
    files = glob.glob('/Users/macgeint/Downloads/datafootball-base-2026-09-16 *.csv')
    df_list = []
    for f in files:
        df = pd.read_csv(f, low_memory=False, on_bad_lines='skip')
        df_list.append(df)
    return pd.concat(df_list, ignore_index=True)
df = load_data()
df = df[df['Status'].str.lower() == 'complete']
df['Gols Casa'] = pd.to_numeric(df['Gols Casa'], errors='coerce')
df['Gols Fora'] = pd.to_numeric(df['Gols Fora'], errors='coerce')

print("Gols Casa value counts:")
print(df['Gols Casa'].value_counts().head(10))
print("Gols Fora value counts:")
print(df['Gols Fora'].value_counts().head(10))
