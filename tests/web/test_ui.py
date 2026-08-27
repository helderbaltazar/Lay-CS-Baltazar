import pytest
from web.app import app

import base64
import config

def get_auth_headers():
    username = config.DASHBOARD_USERNAME
    password = config.DASHBOARD_PASSWORD
    token = base64.b64encode(f"{username}:{password}".encode('utf-8')).decode('utf-8')
    return {'Authorization': f'Basic {token}'}


@pytest.fixture(autouse=True)
def setup_db():
    from sqlalchemy import create_engine
    import database.db
    from database.db import Base
    test_engine = create_engine("sqlite:///:memory:")
    database.db.engine = test_engine
    database.db.SessionLocal.configure(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_base_html_has_analytics_link(client):
    response = client.get('/', headers=get_auth_headers())
    html = response.data.decode('utf-8')
    assert 'href="/analytics"' in html, "Falta o link para Analytics no menu principal (base.html)"

def test_history_html_has_export_link(client):
    response = client.get('/history', headers=get_auth_headers())
    html = response.data.decode('utf-8')
    assert 'href="/export"' in html, "Falta o link para Exportar CSV na tela de historico (history.html)"


def test_analytics_route_returns_200(client):
    response = client.get('/analytics', headers=get_auth_headers())
    assert response.status_code == 200, "A rota /analytics retornou erro."
    html = response.data.decode('utf-8')
    assert "Analytics de Desempenho por Liga" in html, "A pagina /analytics nao renderizou corretamente."

def test_export_route_returns_csv(client):
    response = client.get('/export', headers=get_auth_headers())
    assert response.status_code == 200, "A rota /export retornou erro."
    assert response.headers['Content-Type'] == 'text/csv; charset=utf-8' or response.headers['Content-Type'] == 'text/csv', "O Content-Type do export nao e text/csv."
    data = response.data.decode('utf-8')
    assert "Placar Real" in data, "O cabecalho do CSV de exportacao esta ausente."
