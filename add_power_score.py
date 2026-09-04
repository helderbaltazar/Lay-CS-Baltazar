from database.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE predictions ADD COLUMN power_score FLOAT"))
        conn.commit()
        print("Coluna adicionada ao banco local com sucesso!")
    except Exception as e:
        print(f"Aviso (já deve existir): {e}")

