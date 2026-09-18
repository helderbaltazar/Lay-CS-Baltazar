import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("No DATABASE_URL found.")
else:
    try:
        engine = create_engine(db_url)
        df = pd.read_sql("SELECT * FROM datafootball_historical LIMIT 5", engine)
        print("Columns:", df.columns.tolist())
    except Exception as e:
        print("Error connecting:", e)
