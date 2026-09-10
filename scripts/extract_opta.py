import re
import json

with open('/tmp/index.js', 'r') as f:
    js_content = f.read()

# Instead of parsing 12MB of potentially malformed embedded JSON,
# we just regex the team blocks directly from the file!
pattern = r'"globalRank":(\d+).*?"contestantName":"([^"]+)".*?"currentRating":([\d.]+)'
matches = re.findall(pattern, js_content)

print(f"Extracted {len(matches)} teams via regex!")
# Since the regex could match in different orders if the json schema is slightly off, 
# let's be more robust:
# find each contestant block first, then extract from it
blocks = re.findall(r'\{"rank":\d+,"contestantId":.*?\}', js_content)
print(f"Found {len(blocks)} blocks!")

teams = []
for block in blocks:
    rank_m = re.search(r'"globalRank":([\d.]+)', block)
    name_m = re.search(r'"contestantName":"([^"]+)"', block)
    rating_m = re.search(r'"currentRating":([\d.]+)', block)
    
    if name_m and rating_m:
        teams.append({
            "name": name_m.group(1),
            "rating": float(rating_m.group(1)),
            "rank": int(float(rank_m.group(1))) if rank_m else None
        })

print(f"Successfully extracted {len(teams)} teams!")
for t in teams[:3]:
    print(t)
    
print("---")
for t in teams:
    if "Palmeiras" in t["name"] or "Cruzeiro" in t["name"] or "Atlético Mineiro" in t["name"] or "Botafogo" in t["name"]:
        print(t)
