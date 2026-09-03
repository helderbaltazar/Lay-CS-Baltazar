with open("analysis/scanner.py", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "get_match_winner_odds" in line or "get_over25_odds" in line:
        continue
    new_lines.append(line)

with open("analysis/scanner.py", "w") as f:
    f.writelines(new_lines)
