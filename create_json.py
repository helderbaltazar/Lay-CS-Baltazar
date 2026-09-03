import json

data = {
  "version": "1.0",
  "betOnNewTeam": True,
  "teams": [
    {"id": "2118656", "name": "07 Vestur", "side": "A", "checked": True},
    {"id": "1915199", "name": "Cruzeiro MG", "side": "A", "checked": True},
    {"id": "1277122", "name": "Atletico MG", "side": "A", "checked": True},
    {"id": "1992499", "name": "Bodo Glimt", "side": "A", "checked": True}
  ]
}
with open('data/layback_teams_template.json', 'w') as f:
    json.dump(data, f, indent=4)
