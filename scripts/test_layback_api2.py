import sys, os, json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import init_db
init_db()
from integration.layback import get_layback_session, BASE_URL
session, _ = get_layback_session()
r = session.get(f"{BASE_URL}/api/bots/34219")
print(json.dumps(r.json(), indent=2))
