import urllib.request
import re

url = "https://html.duckduckgo.com/html/?q=site:theanalyst.com+opta+power+rankings"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
try:
    with urllib.request.urlopen(req) as response:
        html = response.read().decode('utf-8')
        links = re.findall(r'href="(.*?)"', html)
        for link in links:
            if 'theanalyst.com' in link:
                print(link)
except Exception as e:
    print(e)
