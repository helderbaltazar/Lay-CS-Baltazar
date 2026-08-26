with open('data/api_football.py', 'r') as f:
    content = f.read()

old_url = 'url = f"{config.BASE_URL}/fixtures?date={date_str}"'
new_url = 'url = f"{config.BASE_URL}/fixtures?date={date_str}&timezone={config.SCHEDULER_TIMEZONE}"'

if old_url in content:
    content = content.replace(old_url, new_url)
    with open('data/api_football.py', 'w') as f:
        f.write(content)
    print("API URL patched with timezone.")
else:
    print("Could not find the URL string to patch.")
