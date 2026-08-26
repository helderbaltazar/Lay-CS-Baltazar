import re

# 1. Update web/app.py to fix func.case -> case
with open('web/app.py', 'r') as f:
    app_content = f.read()

bad_imports = "from sqlalchemy import func"
good_imports = "from sqlalchemy import func, case"
app_content = app_content.replace(bad_imports, good_imports)
app_content = app_content.replace("func.case", "case")

with open('web/app.py', 'w') as f:
    f.write(app_content)

# 2. Update tests/web/test_ui.py to include functional tests for /analytics and /export
with open('tests/web/test_ui.py', 'a') as f:
    f.write("""

def test_analytics_route_returns_200(client):
    response = client.get('/analytics')
    assert response.status_code == 200, "A rota /analytics retornou erro."
    html = response.data.decode('utf-8')
    assert "Analytics de Desempenho por Liga" in html, "A pagina /analytics nao renderizou corretamente."

def test_export_route_returns_csv(client):
    response = client.get('/export')
    assert response.status_code == 200, "A rota /export retornou erro."
    assert response.headers['Content-Type'] == 'text/csv; charset=utf-8' or response.headers['Content-Type'] == 'text/csv', "O Content-Type do export nao e text/csv."
    data = response.data.decode('utf-8')
    assert "Placar Real" in data, "O cabecalho do CSV de exportacao esta ausente."
""")
