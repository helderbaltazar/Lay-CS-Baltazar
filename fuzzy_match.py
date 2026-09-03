import json
import difflib

with open("logs/teams_api.json", "r") as f:
    layback_teams = json.load(f)["data"]["teams"]

def get_betfair_id(team_name):
    names = [t["name"] for t in layback_teams]
    # Exact match first
    if team_name in names:
        team = next((t for t in layback_teams if t["name"] == team_name), None)
        return {"name": team["name"], "id": int(team["id"])}
        
    # Fuzzy match
    matches = difflib.get_close_matches(team_name, names, n=1, cutoff=0.6)
    if matches:
        match_name = matches[0]
        team = next((t for t in layback_teams if t["name"] == match_name), None)
        return {"name": team["name"], "id": int(team["id"])}
        
    return None

if __name__ == "__main__":
    print(get_betfair_id("Cruzeiro"))
    print(get_betfair_id("Atletico Mineiro"))
