import config
from sqlalchemy import create_engine, text

engine = create_engine(config.DATABASE_URL)
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE predictions ADD COLUMN power_score FLOAT"))
        conn.commit()
        print("Coluna adicionada ao Supabase com sucesso!")
    except Exception as e:
        print(f"Aviso (já deve existir no Supabase): {e}")

