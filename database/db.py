from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
import os
import config

DB_DIR = "data_store"
os.makedirs(DB_DIR, exist_ok=True)
engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    import database.models_db
    from sqlalchemy import text, inspect
    Base.metadata.create_all(bind=engine)
    
    # Migrações seguras de colunas caso a tabela já exista
    try:
        inspector = inspect(engine)
        if 'predictions' in inspector.get_table_names():
            columns = [c['name'] for c in inspector.get_columns('predictions')]
            with engine.connect() as conn:
                if 'ai_verdict' not in columns:
                    conn.execute(text("ALTER TABLE predictions ADD COLUMN ai_verdict VARCHAR(20) DEFAULT 'APROVADO'"))
                if 'ai_confidence' not in columns:
                    conn.execute(text("ALTER TABLE predictions ADD COLUMN ai_confidence INTEGER"))
                if 'ai_critical_factor' not in columns:
                    conn.execute(text("ALTER TABLE predictions ADD COLUMN ai_critical_factor VARCHAR(255)"))
                if 'ai_analysis' not in columns:
                    conn.execute(text("ALTER TABLE predictions ADD COLUMN ai_analysis TEXT"))
                conn.commit()
    except Exception as e:
        print(f"[DB Migration Note] {e}")

