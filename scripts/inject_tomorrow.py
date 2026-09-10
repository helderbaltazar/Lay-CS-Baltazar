import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import init_db
init_db()

from run_real_injection import ensure_data_in_db, inject_from_db
print("-> Baixando e calculando jogos de hoje/amanhã...")
ensure_data_in_db()
print("-> Injetando jogos aprovados no LayBack...")
inject_from_db()
