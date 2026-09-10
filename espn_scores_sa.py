import requests
import json

targets = [
    "racing", "tucuman", "corinthians", "chapecoense", "river plate", "independ"
]

results = {}
for date in ["20260905", "20260906", "20260907", "20260908"]:
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard?dates={date}"
    res = requests.get(url)
    data = res.json()
    
    if 'events' in data:
        for event in data['events']:
            name = event.get('name', '')
            name_lower = name.lower()
            
            # Check if any target team is in the name
            if any(t in name_lower for t in targets):
                competitions = event.get('competitions', [])
                if competitions:
                    competitors = competitions[0].get('competitors', [])
                    score = {}
                    for c in competitors:
                        if c.get('homeAway') == 'home':
                            score['home'] = c.get('score')
                        else:
                            score['away'] = c.get('score')
                    results[f"[{date}] {name}"] = f"{score.get('home', '?')}-{score.get('away', '?')}"

print(json.dumps(results, indent=2))
