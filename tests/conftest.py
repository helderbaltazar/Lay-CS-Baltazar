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
def setup_test_environment():
    Base.metadata.create_all(bind=database.db.engine)
    
    yield
    
    Base.metadata.drop_all(bind=database.db.engine)
