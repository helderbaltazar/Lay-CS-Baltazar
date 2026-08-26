import pytest
from web.app import app

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
    response = client.get('/')
    html = response.data.decode('utf-8')
    assert 'href="/analytics"' in html, "Falta o link para Analytics no menu principal (base.html)"

def test_history_html_has_export_link(client):
    response = client.get('/history')
    html = response.data.decode('utf-8')
    assert 'href="/export"' in html, "Falta o link para Exportar CSV na tela de historico (history.html)"
