import pandas as pd
import numpy as np
import glob
import os
import sys

# Load poisson model
sys.path.append(os.path.abspath('.'))
from models.poisson import PoissonDixonColes

def load_data():
    files = glob.glob('/Users/macgeint/Downloads/datafootball-base-2026-09-16 *.csv')
    df_list = []
    for f in files:
        df = pd.read_csv(f, low_memory=False, on_bad_lines='skip')
        df_list.append(df)
    return pd.concat(df_list, ignore_index=True)

df = load_data()
print(f"Total rows loaded: {len(df)}")
df = df[df['Status'].str.lower() == 'complete']
print(f"Total completed matches: {len(df)}")

df['Odd 1'] = pd.to_numeric(df['Odd 1'], errors='coerce')
df['Odd 2'] = pd.to_numeric(df['Odd 2'], errors='coerce')
df['Under 2.5'] = pd.to_numeric(df['Under 2.5'], errors='coerce')
df['Gols Casa'] = pd.to_numeric(df['Gols Casa'], errors='coerce')
df['Gols Fora'] = pd.to_numeric(df['Gols Fora'], errors='coerce')
df['PPG Casa Pré-Jogo'] = pd.to_numeric(df['PPG Casa Pré-Jogo'], errors='coerce')
df['PPG Fora Pré-Jogo'] = pd.to_numeric(df['PPG Fora Pré-Jogo'], errors='coerce')

df = df.dropna(subset=['Odd 1', 'Odd 2', 'Gols Casa', 'Gols Fora'])
print(f"Rows with valid odds and goals: {len(df)}")
