from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
import os

DB_DIR = "data_store"
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = f"sqlite:///{DB_DIR}/database.sqlite3"

engine = create_engine(DB_PATH)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
