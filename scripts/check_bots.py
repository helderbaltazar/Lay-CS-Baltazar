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

for bot_id in [34219, 34220, 34225]:
    r = session.get(f"{BASE_URL}/api/bots/{bot_id}", timeout=15)
    if r.status_code == 200:
        bot = r.json().get('data', {}).get('bot', {})
        print(f"Bot {bot_id} ({bot.get('name')}): {len(bot.get('teams', []))} teams injected")
        for t in bot.get('teams', []):
            print(f" - {t.get('name')}")
    else:
        print(f"Failed to fetch bot {bot_id}")
