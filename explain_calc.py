import datetime
import config
from data.api_football import get_fixtures, get_team_stats
from data.league_config import get_league_avg
from models.poisson import PoissonDixonColes
import json

# Target teams
home_team_name = "FC Iberia 1999"
away_team_name = "Jagiellonia Bialystock"

# Let's find the fixture
fixtures = get_fixtures("2026-08-28") + get_fixtures("2026-08-27")
target_fixture = None
for f in fixtures:
    # the names in API-Football might be slightly different like "Jagiellonia"
    if "Iberia" in f['teams']['home']['name'] and "Jagiellonia" in f['teams']['away']['name']:
        target_fixture = f
        break

if not target_fixture:
    print("Fixture not found!")
    import sys
    sys.exit(1)

league_info = target_fixture['league']
home_team = target_fixture['teams']['home']
away_team = target_fixture['teams']['away']

print(f"Match: {home_team['name']} vs {away_team['name']}")
print(f"League: {league_info['name']} (ID: {league_info['id']})")

home_stats = get_team_stats(home_team['id'], league_info['id'])
away_stats = get_team_stats(away_team['id'], league_info['id'])

league_avg = get_league_avg(league_info['id'])

print("=== RAW DATA ===")
print("League Avg (Home Goals, Away Goals):", league_avg)

h_scored = float(home_stats['goals']['for']['total']['home'] or 0)
h_conceded = float(home_stats['goals']['against']['total']['home'] or 0)
h_games = float(home_stats['fixtures']['played']['home'] or 0)

a_scored = float(away_stats['goals']['for']['total']['away'] or 0)
a_conceded = float(away_stats['goals']['against']['total']['away'] or 0)
a_games = float(away_stats['fixtures']['played']['away'] or 0)

print(f"Home ({home_team['name']}) -> Games: {h_games}, Scored (Home): {h_scored}, Conceded (Home): {h_conceded}")
print(f"Away ({away_team['name']}) -> Games: {a_games}, Scored (Away): {a_scored}, Conceded (Away): {a_conceded}")

# calculate_lambdas logic
avg_home, avg_away = league_avg

# +0.1 smoothing applied in scanner.py
h_scored_s = h_scored + 0.1
h_conceded_s = h_conceded + 0.1
h_games_s = h_games + 0.1

a_scored_s = a_scored + 0.1
a_conceded_s = a_conceded + 0.1
a_games_s = a_games + 0.1

h_attack = (h_scored_s / h_games_s) / avg_home
h_defense = (h_conceded_s / h_games_s) / avg_away

a_attack = (a_scored_s / a_games_s) / avg_away
a_defense = (a_conceded_s / a_games_s) / avg_home

lam_home = h_attack * a_defense * avg_home
lam_away = a_attack * h_defense * avg_away

print("\n=== STRENGTH RATIOS ===")
print(f"Home Attack Strength: {h_attack:.4f}")
print(f"Home Defense Strength: {h_defense:.4f}")
print(f"Away Attack Strength: {a_attack:.4f}")
print(f"Away Defense Strength: {a_defense:.4f}")

lam_home_c = max(0.2, min(lam_home, 5.0))
lam_away_c = max(0.2, min(lam_away, 5.0))

print(f"Expected Goals (Lambda) -> Home: {lam_home:.4f} (clamped to {lam_home_c:.4f}), Away: {lam_away:.4f} (clamped to {lam_away_c:.4f})")

model = PoissonDixonColes()
probs = model.get_probabilities(lam_home_c, lam_away_c, ["0-2", "0-3"])

print("\n=== FINAL PROBABILITIES ===")
print("0-2:", probs["0-2"])
print("0-3:", probs["0-3"])

