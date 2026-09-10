import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import init_db
init_db()

from integration.layback import get_layback_session, BASE_URL
session, cookies = get_layback_session()
if not session:
    print("Failed to get session.")
    sys.exit(1)

r = session.get(f"{BASE_URL}/api/bots", timeout=15)
if r.status_code == 200:
    bots = r.json().get('data', {}).get('bots', [])
    print("Found Bots:")
    for b in bots:
        print(f"ID: {b['id']} | Name: {b['name']}")
else:
    print(f"Failed: {r.status_code} - {r.text}")
