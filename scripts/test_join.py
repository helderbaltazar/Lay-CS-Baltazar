import sqlite3
import pandas as pd

conn = sqlite3.connect('data_store/database.sqlite3')
query = """
    SELECT COUNT(*) as JoinedMatches
    FROM historical_dataset h
    INNER JOIN telegram_dataset t 
    ON h.HomeTeam = t.home_name 
       AND h.AwayTeam = t.away_name
       -- E formatar a data: t.Data_Hora_Jogo é 'dd/mm/yyyy' e h.MatchDate é 'yyyy-mm-dd hh:mm:ss'
       AND strftime('%Y-%m-%d', h.MatchDate) = substr(t.Data_Hora_Jogo, 7, 4) || '-' || substr(t.Data_Hora_Jogo, 4, 2) || '-' || substr(t.Data_Hora_Jogo, 1, 2)
"""
df = pd.read_sql_query(query, conn)
print(df)
conn.close()
