import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from run_real_injection import inject_from_db
inject_from_db()
