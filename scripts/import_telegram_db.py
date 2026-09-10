import pandas as pd
import sqlite3
import time

def import_to_db():
    print("Iniciando carregamento da nova base de dados do Telegram...")
    file_path = "data_store/datasets/base_telegram.xlsx"
    
    start_time = time.time()
    # Ler a aba Historico_Base
    df = pd.read_excel(file_path, sheet_name="Historico_Base")
    
    # Remover colunas totalmente vazias para evitar lixo
    df = df.dropna(axis=1, how='all')
    
    print(f"Planilha carregada com sucesso em {time.time() - start_time:.2f} segundos!")
    print(f"Total de jogos (linhas): {len(df)}")
    print(f"Total de métricas (colunas): {len(df.columns)}")
    
    # Padronizar os nomes das colunas substituindo espaços por underlines
    df.columns = df.columns.str.replace(' ', '_').str.replace('-', '_').str.replace('.', '')
    
    # Conectar ao banco local
    conn = sqlite3.connect('data_store/database.sqlite3')
    
    print("Injetando dados na nova tabela `telegram_dataset` no SQLite...")
    df.to_sql('telegram_dataset', conn, if_exists='replace', index=False)
    
    conn.close()
    print("✅ Injeção concluída com sucesso! A base está pronta para cruzamento de dados e backtests.")

if __name__ == "__main__":
    import_to_db()
