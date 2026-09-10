import requests
import json
from config import BASE_URL, API_KEY

headers = {
    'x-apisports-key': API_KEY,
    'x-rapidapi-host': "v3.football.api-sports.io"
}
res = requests.get(f"{BASE_URL}/fixtures?date=2026-09-06", headers=headers)
data = res.json()
scores = {}
for f in data.get('response', []):
    h = f['teams']['home']['name']
    a = f['teams']['away']['name']
    g = f['goals']
    if g['home'] is not None:
        scores[f"{h} vs {a}"] = f"{g['home']}-{g['away']}"

print(json.dumps(scores, indent=2))
