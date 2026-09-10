with open("web/templates/base.html", "r") as f:
    content = f.read()

content = content.replace('<a href="/methodologies">Metodologias</a>', '<a href="/methodologies">Metodologias</a>\n                <a href="/backtest">Backtest Lab</a>')

with open("web/templates/base.html", "w") as f:
    f.write(content)
