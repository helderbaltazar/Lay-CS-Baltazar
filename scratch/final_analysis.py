import pandas as pd
import glob
files = glob.glob('/Users/macgeint/Downloads/datafootball-base-2026-09-16 *.csv')
df = pd.concat([pd.read_csv(f, low_memory=False, on_bad_lines='skip') for f in files], ignore_index=True)
df = df[df['Status'].str.lower() == 'complete']

for col in ['Gols HT Casa', 'Gols HT Fora', 'goals_2hg_team_a', 'goals_2hg_team_b']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

df = df.dropna(subset=['Gols HT Casa', 'Gols HT Fora', 'goals_2hg_team_a', 'goals_2hg_team_b'])
df['FT_Home'] = df['Gols HT Casa'] + df['goals_2hg_team_a']
df['FT_Away'] = df['Gols HT Fora'] + df['goals_2hg_team_b']

print(f"Total Completed Matches: {len(df)}")
print("\nDistribution of Match Scores (FT_Home - FT_Away):")
df['Score'] = df['FT_Home'].astype(int).astype(str) + "-" + df['FT_Away'].astype(int).astype(str)
print(df['Score'].value_counts())

print("\nMaximum Total Goals in dataset:", (df['FT_Home'] + df['FT_Away']).max())
