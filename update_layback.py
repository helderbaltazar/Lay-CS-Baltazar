import os

with open('integration/layback.py', 'r') as f:
    content = f.read()

content = content.replace(
    'page.goto("https://bot-betfair.layback.trade/dashboard")',
    'page.goto("https://bot-betfair.layback.trade/dashboard", timeout=60000, wait_until="domcontentloaded")'
)

content = content.replace(
    'page.goto("https://bot-betfair.layback.trade/login")',
    'page.goto("https://bot-betfair.layback.trade/login", timeout=60000, wait_until="domcontentloaded")'
)

content = content.replace(
    'page.goto(f"https://bot-betfair.layback.trade/bots/{bot_id}/edit", wait_until="networkidle")',
    'page.goto(f"https://bot-betfair.layback.trade/bots/{bot_id}/edit", wait_until="domcontentloaded", timeout=60000)'
)

with open('integration/layback.py', 'w') as f:
    f.write(content)
