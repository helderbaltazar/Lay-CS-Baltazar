import pandas as pd
import sqlite3

def import_to_db():
    print("Carregando CSV gigante do repositório...")
    df = pd.read_csv('/tmp/Club-Football-Match-Data/data/Matches.csv', low_memory=False)
    
    # Filtrar colunas mais importantes para o Lay CS
    df = df[['Division', 'MatchDate', 'HomeTeam', 'AwayTeam', 
             'FTHome', 'FTAway', 'HTHome', 'HTAway', 'OddHome', 'OddDraw', 'OddAway', 
             'Over25', 'Under25', 'HomeShots', 'AwayShots', 
             'HomeTarget', 'AwayTarget']]
             
    # Filtro só de 2020 para frente pra não ficar tão pesado
    df['MatchDate'] = pd.to_datetime(df['MatchDate'])
    df = df[df['MatchDate'] >= '2020-01-01']
    
    conn = sqlite3.connect('data_store/database.sqlite3')
    
    print(f"Inserindo {len(df)} jogos históricos no nosso banco...")
    df.to_sql('historical_dataset', conn, if_exists='replace', index=False)
    conn.close()
    print("Importação concluída com sucesso na tabela `historical_dataset`!")

if __name__ == "__main__":
    import_to_db()
