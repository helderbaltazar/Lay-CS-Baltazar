import re

# Fix base.html
with open('web/templates/base.html', 'r') as f:
    base = f.read()
if '<a href="/analytics">Analytics</a>' not in base:
    base = base.replace(
        '<a href="/history">Dashboard Histórico</a>',
        '<a href="/history">Dashboard Histórico</a>\n                <a href="/analytics">Analytics</a>'
    )
    with open('web/templates/base.html', 'w') as f:
        f.write(base)

# Fix history.html
with open('web/templates/history.html', 'r') as f:
    hist = f.read()
if 'href="/export"' not in hist:
    hist = hist.replace(
        '<h3>Histórico de Jogos Finalizados</h3>',
        '<div style="display: flex; justify-content: space-between; align-items: center;">\n        <h3>Histórico de Jogos Finalizados</h3>\n        <a href="/export" class="badge" style="background:#27ae60; color:#fff; text-decoration:none; padding:8px 15px; font-size:14px;">📥 Exportar CSV</a>\n    </div>'
    )
    with open('web/templates/history.html', 'w') as f:
        f.write(hist)
