import requests

url = "https://theanalyst.com/sports/football/opta-power-rankings"
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}
response = requests.get(url, headers=headers)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    content = response.text
    if "opta" in content.lower():
        print("Encontrou opta na pagina.")
    if "Palmeiras" in content or "Manchester City" in content:
        print("Encontrou times na pagina.")
    else:
        print("Não encontrou os times no HTML direto (pode ser renderizado via JS/API)")
