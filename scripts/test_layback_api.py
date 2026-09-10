import sys, os, requests
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import init_db
init_db()
from integration.layback import get_layback_session, BASE_URL
session, _ = get_layback_session()
r = session.get(f"{BASE_URL}/api/bots/34219")
bot_data = r.json().get('data', {}).get('bot', {})
print("Current teams in bot:", bot_data.get('teams'))

payload = {
    "ids": [34219],
    "teams": [{"id": "1280005", "name": "Bromley", "checked": True, "side": "A"}]
}
r2 = session.post(f"{BASE_URL}/api/bots/bulk/teams", json=payload)
print("POST response:", r2.status_code, r2.text)

r3 = session.get(f"{BASE_URL}/api/bots/34219")
print("New teams in bot:", r3.json().get('data', {}).get('bot', {}).get('teams'))
