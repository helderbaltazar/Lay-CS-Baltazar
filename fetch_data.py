import pandas as pd
import sqlalchemy

engine = sqlalchemy.create_engine('postgresql://postgres:B%40nde74812005@db.dewniwkvwicalcvmoccc.supabase.co:5432/postgres')

query = '''
SELECT 
    "ID", "Data", "Liga", "Casa", "Fora", "Gols Casa", "Gols Fora",
    "Odd 1", "Odd X", "Odd 2", "Over 2.5", "Under 2.5",
    "team_a_xg_prematch", "team_b_xg_prematch",
    "PPG Casa Pré-Jogo", "PPG Fora Pré-Jogo", "Potencial BTTS",
    "home_odds", "draw_odds", "away_odds"
FROM datafootball_historical
WHERE "Status" = 'complete' AND "Gols Casa" IS NOT NULL AND "Gols Fora" IS NOT NULL
'''

df = pd.read_sql(query, engine)
print("Total rows:", len(df))
print("Missing team_a_xg_prematch:", df["team_a_xg_prematch"].isna().sum())
print("Missing Odd 1:", df["Odd 1"].isna().sum())
print("Missing Over 2.5:", df["Over 2.5"].isna().sum())

df.to_pickle('data_cache.pkl')
