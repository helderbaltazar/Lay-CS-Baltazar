import pytest
from database.db import init_db, engine, SessionLocal
from database.models_db import Match, Prediction
from sqlalchemy import inspect

def test_init_db_creates_tables():
    # 1. Garante que init_db roda sem erros
    init_db()
    
    # 2. Inspeciona o banco para garantir que as tabelas existem
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    assert 'matches' in tables, "Tabela 'matches' nao foi criada"
    assert 'predictions' in tables, "Tabela 'predictions' nao foi criada"
    
    # 3. Garante que conseguimos fazer queries sem OperationalError (que causava o 500)
    db = SessionLocal()
    try:
        # A simple query should not raise an exception
        matches_count = db.query(Match).count()
        assert matches_count >= 0
    finally:
        db.close()
