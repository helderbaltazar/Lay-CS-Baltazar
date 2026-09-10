import requests
import json

url = "https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard?dates=20260905"
res = requests.get(url)
data = res.json()

results = {}
if 'events' in data:
    for event in data['events']:
        name = event.get('name')
        competitions = event.get('competitions', [])
        if competitions:
            competitors = competitions[0].get('competitors', [])
            score = {}
            for c in competitors:
                if c.get('homeAway') == 'home':
                    score['home'] = c.get('score')
                else:
                    score['away'] = c.get('score')
            results[name] = f"{score.get('home', '?')}-{score.get('away', '?')}"

print(json.dumps(results, indent=2))
