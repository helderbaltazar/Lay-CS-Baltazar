with open("tests/web/test_ui.py", "r") as f:
    content = f.read()

content = content.replace('date=datetime.utcnow(),', 'date=datetime.now(pytz.timezone("America/Sao_Paulo")),')
content = content.replace('from datetime import datetime', 'from datetime import datetime\n    import pytz')

with open("tests/web/test_ui.py", "w") as f:
    f.write(content)
