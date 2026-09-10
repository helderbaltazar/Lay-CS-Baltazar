import pandas as pd
import sys

file_path = "data_store/datasets/base_telegram.xlsx"
xls = pd.ExcelFile(file_path)
print("Planilhas disponíveis:", xls.sheet_names)

for sheet in xls.sheet_names:
    if "dic" in sheet.lower() or "dicion" in sheet.lower():
        print(f"\n--- Dicionário ({sheet}) ---")
        df_dic = pd.read_excel(xls, sheet_name=sheet)
        print(df_dic.head(30).to_string())
