import pandas as pd

file_path = "data_store/datasets/base_telegram.xlsx"
df = pd.read_excel(file_path, sheet_name="Historico_Base", nrows=5)
print("Colunas:", df.columns.tolist())
print(df.head())
