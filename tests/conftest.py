import os
import pytest

# Ensure SQLite is used during testing before importing config/db
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import database.db
import database.models_db
from database.db import Base

@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    test_engine = create_engine('sqlite:///:memory:')
    test_session = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    monkeypatch.setattr(database.db, 'engine', test_engine)
    monkeypatch.setattr(database.db, 'SessionLocal', test_session)
    
    Base.metadata.create_all(bind=test_engine)
    
    yield
    
    Base.metadata.drop_all(bind=test_engine)
