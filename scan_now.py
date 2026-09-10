import sys
from datetime import datetime, timedelta
from database.db import SessionLocal
from scheduler import run_daily_scan
from web.app import app

with app.app_context():
    run_daily_scan()
