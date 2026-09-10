import re
lines = open('result_august.txt').readlines()
invested = 0
returned = 0
for line in lines:
    if "Odd: None" in line: continue
    invested += 100
    if "GREEN" in line:
        odd = float(re.search(r'Odd: ([\d\.]+)', line).group(1))
        returned += 100 * odd
print(f"Invested: {invested}, Returned: {returned}, Profit: {returned-invested}, ROI: {((returned-invested)/invested)*100:.2f}%")
