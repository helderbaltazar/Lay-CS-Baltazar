import sys
from data.data_manager import DataManager
from analysis.scanner import scan_all
from models.poisson import PoissonDixonColes

date_str = "2026-08-29"
print(f"Buscando fixtures para {date_str}...")
fixtures, source = DataManager.get_fixtures(date_str)
if fixtures:
    print(f"Encontrados {len(fixtures)} jogos no {source}.")
    model = PoissonDixonColes()
    # Pega só os 5 primeiros pra não demorar muito se FBRef estiver lento
    results = scan_all(fixtures[:5], model, source)
    print(results)
else:
    print("Nenhum jogo encontrado.")
